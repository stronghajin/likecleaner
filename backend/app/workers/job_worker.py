"""Background jobs: one asyncio task per running job (SPEC.md 8-1, DECISIONS.md 41).

Each user has at most one job, and its items run one at a time; different users'
jobs run side by side. Jobs keep running when the browser tab is closed.
"""

import asyncio
import logging

import httpx

from app.core.db import SessionFactory
from app.repositories import job_repository
from app.schemas.common import ErrorResponse
from app.services.job_processor import JobRunner

logger = logging.getLogger(__name__)

# job id -> its task
_tasks: dict[str, asyncio.Task[None]] = {}


def start(http: httpx.AsyncClient, user_id: int, job_id: str) -> None:
    _tasks[job_id] = asyncio.create_task(_run(http, user_id, job_id), name=f"job-{job_id}")


def is_running(job_id: str) -> bool:
    task = _tasks.get(job_id)
    return task is not None and not task.done()


async def wait_all() -> None:
    """Tests: wait until every started job is done."""
    await asyncio.gather(*_tasks.values(), return_exceptions=True)


def cancel_all() -> None:
    """Server shutdown. Jobs left `running` in the DB are stopped on the next start (DECISIONS.md 63)."""
    for task in _tasks.values():
        task.cancel()
    _tasks.clear()


async def _run(http: httpx.AsyncClient, user_id: int, job_id: str) -> None:
    try:
        async with SessionFactory() as db:
            job = await job_repository.get(db, job_id, user_id)
            if job is None:
                return
            try:
                await JobRunner(db, http, user_id, job).run()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Job %s failed unexpectedly", job_id)
                await job_repository.finish(
                    db,
                    job_id,
                    "stopped",
                    ErrorResponse(status=500, reason="internalError", message="Something went wrong on the server."),
                )
    finally:
        _tasks.pop(job_id, None)
