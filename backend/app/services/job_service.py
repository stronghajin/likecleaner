"""Creating jobs and reading their progress (SPEC.md 8, DECISIONS.md 10, 30, 63).

The rules are checked here, not only in the browser: one job per user, 1 to 100 items,
and enough of today's quota for the worst case.
"""

import asyncio
import uuid
from datetime import timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.time import now_utc, pacific_day
from app.repositories import job_repository, quota_repository
from app.schemas.common import ErrorResponse
from app.schemas.job import CreateJobRequest, JobCreate, JobItemCreate, JobResponse, JobType
from app.services import memory_store, playlist_service, quota_service
from app.services.job_estimate import estimate_units, max_affordable_items
from app.workers import job_worker

MAX_ITEMS = 100
KEEP_DAYS = 30
RETRYABLE = ("failed", "not_processed")  # not rollback_failed: the user checks those by hand (DECISIONS.md 10)

SERVER_RESTARTED = ErrorResponse(
    status=503,
    reason="serverRestarted",
    message="The server restarted while this job was running. Use Retry Failed to continue.",
)

# Two clicks at once must not start two jobs for the same user.
_locks: dict[int, asyncio.Lock] = {}


async def create_job(db: AsyncSession, http: httpx.AsyncClient, user_id: int, request: CreateJobRequest) -> JobResponse:
    async with _locks.setdefault(user_id, asyncio.Lock()):
        await _check_no_running_job(db, user_id)
        if request.type == "playlist_remove":
            playlist_id = _required(request.playlist_id, "playlistId")
            items = await _playlist_entries(db, http, user_id, playlist_id, _unique(request.playlist_item_ids))
        else:
            video_ids = _unique(request.video_ids)
            _check_count(len(video_ids))
            items = [_liked_item(user_id, video_id) for video_id in video_ids]
            playlist_id = (
                _required(request.target_playlist_id, "targetPlaylistId") if request.type != "remove_like" else None
            )
        return await _start(db, http, user_id, request.type, playlist_id, items)


async def retry_failed(db: AsyncSession, http: httpx.AsyncClient, user_id: int, job_id: str) -> JobResponse:
    """A new job with the failed and not-processed items of `job_id` (SPEC.md 8-2, DECISIONS.md 10)."""
    async with _locks.setdefault(user_id, asyncio.Lock()):
        old = await job_repository.get(db, job_id, user_id)
        if old is None:
            raise AppError(404, "jobNotFound", "The job could not be found.")
        await _check_no_running_job(db, user_id)
        items = [
            JobItemCreate(video_id=i.video_id, video_title=i.video_title, playlist_item_id=i.playlist_item_id)
            for i in old.items
            if i.status in RETRYABLE
        ]
        if not items:
            raise AppError(400, "nothingToRetry", "There are no failed items to retry.")
        return await _start(db, http, user_id, old.type, old.target_playlist_id, items)


async def latest_job(db: AsyncSession, user_id: int) -> JobResponse | None:
    return await job_repository.latest(db, user_id)


async def stop_interrupted_jobs(db: AsyncSession) -> None:
    """Start-up: jobs cut off by a restart are stopped, not resumed (DECISIONS.md 63)."""
    for job_id in await job_repository.running_ids(db):
        if not job_worker.is_running(job_id):
            await job_repository.finish(db, job_id, "stopped", SERVER_RESTARTED)


async def delete_old_data(db: AsyncSession) -> None:
    """SPEC.md 9: jobs, job items and quota usage are kept 30 days."""
    cutoff = now_utc() - timedelta(days=KEEP_DAYS)
    await job_repository.delete_created_before(db, cutoff)
    await quota_repository.delete_before(db, pacific_day() - timedelta(days=KEEP_DAYS))


# ---------- helpers ----------


async def _start(
    db: AsyncSession,
    http: httpx.AsyncClient,
    user_id: int,
    job_type: JobType,
    playlist_id: str | None,
    items: list[JobItemCreate],
) -> JobResponse:
    _check_count(len(items))
    title, size = await _playlist_title_and_size(db, http, user_id, playlist_id) if playlist_id else (None, 0)
    await _check_quota(db, job_type, len(items), size)
    job = await job_repository.create(
        db,
        JobCreate(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=job_type,
            target_playlist_id=playlist_id,
            target_playlist_title=title,
            items=items,
        ),
    )
    job_worker.start(http, user_id, job.id)
    return job


async def _check_no_running_job(db: AsyncSession, user_id: int) -> None:
    if await job_repository.has_running(db, user_id):
        raise AppError(409, "jobAlreadyRunning", "Another job is already running. Wait for it to finish.")


def _check_count(count: int) -> None:
    if count == 0:
        raise AppError(400, "noItems", "Select at least one video.")
    if count > MAX_ITEMS:
        raise AppError(400, "tooManyItems", f"You can select up to {MAX_ITEMS} videos at a time.")


async def _check_quota(db: AsyncSession, job_type: JobType, count: int, target_size: int) -> None:
    """Checked again here: the quota is shared, and the browser's number may be old (SPEC.md 4-4)."""
    left = (await quota_service.status(db)).remaining
    if estimate_units(job_type, count, target_size) > left:
        most = max_affordable_items(job_type, left, target_size)
        raise AppError(403, "notEnoughQuota", f"Not enough quota. You can process up to {most} items today.")


def _required(value: str | None, name: str) -> str:
    if not value:
        raise AppError(400, "invalidRequest", f"{name} is required.")
    return value


def _unique(ids: list[str] | None) -> list[str]:
    return list(dict.fromkeys(ids or []))


def _liked_item(user_id: int, video_id: str) -> JobItemCreate:
    video = memory_store.find_liked_video(user_id, video_id)
    return JobItemCreate(video_id=video_id, video_title=video.title if video else video_id)


async def _playlist_entries(
    db: AsyncSession, http: httpx.AsyncClient, user_id: int, playlist_id: str, entry_ids: list[str]
) -> list[JobItemCreate]:
    _check_count(len(entry_ids))
    # Usually from server memory (the user just looked at it); 0 units.
    entries = {i.playlist_item_id: i for i in await playlist_service.get_playlist_items(db, http, user_id, playlist_id)}
    items = []
    for entry_id in entry_ids:
        entry = entries.get(entry_id)
        if entry is None:
            raise AppError(
                404, "playlistItemNotFound", "The playlist item identified with the request cannot be found."
            )
        items.append(JobItemCreate(video_id=entry.video_id, video_title=entry.title, playlist_item_id=entry_id))
    return items


async def _playlist_title_and_size(
    db: AsyncSession, http: httpx.AsyncClient, user_id: int, playlist_id: str
) -> tuple[str, int]:
    playlists = memory_store.get_playlists(user_id)
    if playlists is None or not any(p.id == playlist_id for p in playlists):
        playlists = await playlist_service.list_playlists(db, http, user_id)  # 1 unit per 50 playlists
    playlist = next((p for p in playlists if p.id == playlist_id), None)
    if playlist is None:
        raise AppError(404, "playlistNotFound", "The playlist could not be found.")
    items = memory_store.get_playlist_items(user_id, playlist_id)
    return playlist.title, len(items) if items is not None else playlist.item_count
