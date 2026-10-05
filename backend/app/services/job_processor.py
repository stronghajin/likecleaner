"""Runs one job, one item at a time (SPEC.md 6-5 to 6-7, 7-2, 8; DECISIONS.md 28, 30, 63).

Every YouTube call goes through `youtube_gateway` (quota recorded, retries included).
A 429 retries the same call after 2, 4 and 8 s, never the whole item, so a video that
was already added is never added twice.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import TypeVar

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.time import now_utc
from app.repositories import job_repository
from app.schemas.common import ErrorResponse
from app.schemas.job import JobItemResponse, JobItemResult, JobItemStatus, JobResponse, RateLimitInfo
from app.schemas.playlist import PlaylistItemResponse
from app.schemas.youtube import YouTubePlaylistItem
from app.services import memory_store, playlist_service, youtube_gateway

logger = logging.getLogger(__name__)

T = TypeVar("T")

RATE_LIMIT_WAITS_S: tuple[float, ...] = (2, 4, 8)  # DECISIONS.md 28; tests set these to 0
RATE_LIMIT_REASONS = {"rateLimitExceeded", "userRateLimitExceeded"}
# Errors that every following item would hit as well: stop the job (SPEC.md 8-3).
STOPPING_REASONS = {"quotaExceeded", "youtubeReauthRequired", "accessDenied", "notSignedIn"}

# Playlists that refused `position=0` once; later adds go straight to "no position" (DECISIONS.md 30).
_auto_sorted: set[str] = set()


class _Stop(Exception):
    """Stops the job; `error` is shown as the popup."""

    def __init__(self, error: ErrorResponse) -> None:
        super().__init__(error.message)
        self.error = error


def _error(e: AppError) -> ErrorResponse:
    return ErrorResponse(status=e.status, reason=e.reason, message=e.message)


class JobRunner:
    def __init__(self, db: AsyncSession, http: httpx.AsyncClient, user_id: int, job: JobResponse) -> None:
        self.db = db
        self.http = http
        self.user_id = user_id
        self.job = job
        self.in_playlist: set[str] = set()  # video ids already in the destination

    async def run(self) -> None:
        try:
            if self.job.type in ("move", "move_and_unlike"):
                await self._read_destination()
            for position, item in enumerate(self.job.items):
                if item.status != "pending":
                    continue
                await self._process(position, item)
        except _Stop as stop:
            await job_repository.finish(self.db, self.job.id, "stopped", stop.error)
            return
        await job_repository.finish(self.db, self.job.id, "completed", None)

    # ---------- calls ----------

    async def _call(self, method: str, request: Callable[..., Awaitable[T]]) -> T:
        return await self._with_retry(lambda: youtube_gateway.call(self.db, self.http, self.user_id, method, request))

    async def _with_retry(self, attempt: Callable[[], Awaitable[T]]) -> T:
        """429: wait 2, 4, 8 s and try the same call again. Raises _Stop for errors that end the job."""
        for retry in range(len(RATE_LIMIT_WAITS_S) + 1):
            try:
                result = await attempt()
            except AppError as e:
                if (e.status == 429 or e.reason in RATE_LIMIT_REASONS) and retry < len(RATE_LIMIT_WAITS_S):
                    wait = RATE_LIMIT_WAITS_S[retry]
                    retry_at = now_utc() + timedelta(seconds=wait)
                    await job_repository.set_rate_limit(self.db, self.job.id, RateLimitInfo(attempt=retry + 1, retry_at=retry_at))
                    await asyncio.sleep(wait)
                    continue
                if retry:
                    await job_repository.set_rate_limit(self.db, self.job.id, None)
                if e.status == 429 or e.reason in RATE_LIMIT_REASONS or e.reason in STOPPING_REASONS:
                    raise _Stop(_error(e)) from e
                raise
            if retry:
                await job_repository.set_rate_limit(self.db, self.job.id, None)
            return result
        raise AssertionError("unreachable")

    # ---------- items ----------

    async def _save(self, position: int, status: JobItemStatus, error: ErrorResponse | None = None) -> None:
        await job_repository.set_item_result(self.db, self.job.id, JobItemResult(position=position, status=status, error=error))

    async def _process(self, position: int, item: JobItemResponse) -> None:
        try:
            match self.job.type:
                case "remove_like":
                    await self._unlike(item.video_id)
                case "playlist_remove":
                    await self._remove_from_playlist(item)
                case "move" | "move_and_unlike":
                    if await self._move(position, item):
                        return  # result already saved
        except AppError as e:
            await self._save(position, "failed", _error(e))
            return
        await self._save(position, "success")

    async def _unlike(self, video_id: str) -> None:
        await self._call("videos.rate", lambda yt, token: yt.rate_video(token, video_id, "none"))
        memory_store.remove_like(self.user_id, video_id)

    async def _remove_from_playlist(self, item: JobItemResponse) -> None:
        playlist_id = self.job.target_playlist_id or ""
        entry_id = item.playlist_item_id or ""
        await self._call("playlistItems.delete", lambda yt, token: yt.delete_playlist_item(token, entry_id))
        memory_store.remove_playlist_item(self.user_id, playlist_id, entry_id)

    async def _read_destination(self) -> None:
        """Duplicate check before the first item (SPEC.md 6-6), fresh from YouTube. Also refreshes server memory."""
        playlist_id = self.job.target_playlist_id or ""
        try:
            items = await self._with_retry(
                lambda: playlist_service.get_playlist_items(self.db, self.http, self.user_id, playlist_id, refresh=True)
            )
        except AppError as e:
            raise _Stop(_error(e)) from e  # without the check, adding could make duplicates
        self.in_playlist = {i.video_id for i in items}

    async def _move(self, position: int, item: JobItemResponse) -> bool:
        """Returns True when it saved the item's result itself."""
        if item.video_id in self.in_playlist:
            if self.job.type == "move":
                await self._save(position, "skipped")
                return True
            await self._unlike(item.video_id)  # already there: only remove the like
            return False

        added = await self._add(item.video_id)
        self.in_playlist.add(item.video_id)
        if self.job.type == "move":
            return False

        try:
            await self._unlike(item.video_id)
        except (AppError, _Stop) as unlike_failed:
            await self._roll_back(position, added, unlike_failed)
            return True
        return False

    async def _add(self, video_id: str) -> YouTubePlaylistItem:
        """At the top; an auto-sorted playlist refuses a position, so add again without one (SPEC.md 6-6)."""
        playlist_id = self.job.target_playlist_id or ""
        at_top = playlist_id not in _auto_sorted
        if at_top:
            try:
                added = await self._call(
                    "playlistItems.insert", lambda yt, token: yt.insert_playlist_item(token, playlist_id, video_id, 0)
                )
            except AppError as e:
                if e.reason != "manualSortRequired":
                    raise
                _auto_sorted.add(playlist_id)
                at_top = False
        if not at_top:
            added = await self._call(
                "playlistItems.insert", lambda yt, token: yt.insert_playlist_item(token, playlist_id, video_id)
            )
        memory_store.add_playlist_item(self.user_id, playlist_id, self._memory_item(added), at_top=at_top)
        return added

    async def _roll_back(self, position: int, added: YouTubePlaylistItem, cause: AppError | _Stop) -> None:
        """SPEC.md 6-7: the like could not be removed, so take the video back out of the playlist."""
        playlist_id = self.job.target_playlist_id or ""
        unlike_error = cause.error if isinstance(cause, _Stop) else _error(cause)
        try:
            await self._call(
                "playlistItems.delete", lambda yt, token: yt.delete_playlist_item(token, added.playlist_item_id)
            )
        except (AppError, _Stop) as e:
            # The only state the user has to check by hand.
            await self._save(position, "rollback_failed", e.error if isinstance(e, _Stop) else _error(e))
        else:
            memory_store.remove_playlist_item(self.user_id, playlist_id, added.playlist_item_id)
            await self._save(position, "failed", unlike_error)
        if isinstance(cause, _Stop):
            raise cause  # the job still stops; this item already has its result

    def _memory_item(self, added: YouTubePlaylistItem) -> PlaylistItemResponse:
        video = memory_store.find_liked_video(self.user_id, added.video_id)
        return PlaylistItemResponse(
            playlist_item_id=added.playlist_item_id,
            position=added.position,
            video_id=added.video_id,
            title=video.title if video else added.title,
            availability="available",
            channel_title=video.channel_title if video else added.video_owner_channel_title,
            category_name=video.category_name if video else None,
            duration_seconds=video.duration_seconds if video else None,
            published_at=video.published_at if video else added.video_published_at,
            thumbnail_url=video.thumbnail_url if video else added.thumbnail_url,
        )
