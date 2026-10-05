"""`jobs` and `job_items` table access. Results go out as `JobResponse`, never as ORM rows."""

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time import now_utc
from app.models.job import Job, JobItem
from app.schemas.common import ErrorResponse
from app.schemas.job import JobCreate, JobItemResponse, JobItemResult, JobResponse, JobStatus, RateLimitInfo


async def create(session: AsyncSession, job: JobCreate) -> JobResponse:
    row = Job(
        id=job.id,
        user_id=job.user_id,
        type=job.type,
        target_playlist_id=job.target_playlist_id,
        target_playlist_title=job.target_playlist_title,
        status="running",
        items=[
            JobItem(
                position=n,
                video_id=item.video_id,
                video_title=item.video_title,
                playlist_item_id=item.playlist_item_id,
                status="pending",
            )
            for n, item in enumerate(job.items)
        ],
    )
    session.add(row)
    await session.commit()
    return await _get(session, job.id)  # type: ignore[return-value]


async def get(session: AsyncSession, job_id: str, user_id: int) -> JobResponse | None:
    job = await _get(session, job_id)
    return job if job and await _owner(session, job_id) == user_id else None


async def latest(session: AsyncSession, user_id: int) -> JobResponse | None:
    job_id = await session.scalar(
        select(Job.id).where(Job.user_id == user_id).order_by(Job.created_at.desc()).limit(1)
    )
    return await _get(session, job_id) if job_id else None


async def has_running(session: AsyncSession, user_id: int) -> bool:
    found = await session.scalar(select(Job.id).where(Job.user_id == user_id, Job.status == "running").limit(1))
    return found is not None


async def running_ids(session: AsyncSession) -> list[str]:
    return list(await session.scalars(select(Job.id).where(Job.status == "running")))


async def set_item_result(session: AsyncSession, job_id: str, result: JobItemResult) -> None:
    error = result.error
    await session.execute(
        update(JobItem)
        .where(JobItem.job_id == job_id, JobItem.position == result.position)
        .values(
            status=result.status,
            error_code=error.status if error else None,
            error_reason=error.reason if error else None,
            error_message=error.message if error else None,
        )
    )
    await session.commit()


async def set_rate_limit(session: AsyncSession, job_id: str, wait: RateLimitInfo | None) -> None:
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            rate_limit_attempt=wait.attempt if wait else None,
            rate_limit_retry_at=wait.retry_at if wait else None,
        )
    )
    await session.commit()


async def finish(session: AsyncSession, job_id: str, status: JobStatus, fatal_error: ErrorResponse | None) -> None:
    """Ends a job. Items still pending become not_processed (SPEC.md 8-3)."""
    await session.execute(
        update(JobItem).where(JobItem.job_id == job_id, JobItem.status == "pending").values(status="not_processed")
    )
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status=status,
            finished_at=now_utc(),
            rate_limit_attempt=None,
            rate_limit_retry_at=None,
            fatal_error_status=fatal_error.status if fatal_error else None,
            fatal_error_reason=fatal_error.reason if fatal_error else None,
            fatal_error_message=fatal_error.message if fatal_error else None,
        )
    )
    await session.commit()


async def delete_created_before(session: AsyncSession, cutoff: datetime) -> None:
    """Finished jobs created before `cutoff`, with their items (SPEC.md 9: kept 30 days)."""
    old_jobs = select(Job.id).where(Job.created_at < cutoff, Job.status != "running")
    await session.execute(delete(JobItem).where(JobItem.job_id.in_(old_jobs)))
    await session.execute(delete(Job).where(Job.created_at < cutoff, Job.status != "running"))
    await session.commit()


async def _owner(session: AsyncSession, job_id: str) -> int | None:
    return await session.scalar(select(Job.user_id).where(Job.id == job_id))


async def _get(session: AsyncSession, job_id: str) -> JobResponse | None:
    session.expire_all()  # the worker writes through its own session; always read what is stored now
    job = await session.scalar(select(Job).where(Job.id == job_id).options(selectinload(Job.items)))
    return _response(job) if job else None


def _response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        type=job.type,  # type: ignore[arg-type]
        target_playlist_id=job.target_playlist_id,
        target_playlist_title=job.target_playlist_title,
        status=job.status,  # type: ignore[arg-type]
        created_at=job.created_at,
        finished_at=job.finished_at,
        items=[
            JobItemResponse(
                video_id=item.video_id,
                video_title=item.video_title,
                playlist_item_id=item.playlist_item_id,
                status=item.status,  # type: ignore[arg-type]
                error=_error(item.error_code, item.error_reason, item.error_message),
            )
            for item in job.items
        ],
        fatal_error=_error(job.fatal_error_status, job.fatal_error_reason, job.fatal_error_message),
        rate_limit=(
            RateLimitInfo(attempt=job.rate_limit_attempt, retry_at=job.rate_limit_retry_at)
            if job.rate_limit_attempt and job.rate_limit_retry_at
            else None
        ),
    )


def _error(status: int | None, reason: str | None, message: str | None) -> ErrorResponse | None:
    if status is None or reason is None:
        return None
    return ErrorResponse(status=status, reason=reason, message=message or "")
