"""Jobs (SPEC.md 8): start one, retry its failed items, and follow the latest one."""

from fastapi import APIRouter

from app.api.deps import ActiveUser, Db, Http
from app.schemas.job import CreateJobRequest, JobResponse
from app.services import job_service

router = APIRouter(tags=["jobs"])


@router.post("/api/jobs", response_model_exclude_none=True)
async def create_job(body: CreateJobRequest, user: ActiveUser, db: Db, http: Http) -> JobResponse:
    """Saves the job and its items, then a background worker processes them one by one."""
    return await job_service.create_job(db, http, user.id, body)


@router.post("/api/jobs/{job_id}/retry", response_model_exclude_none=True)
async def retry_failed(job_id: str, user: ActiveUser, db: Db, http: Http) -> JobResponse:
    """A new job with the Failed and Not processed items (DECISIONS.md 10)."""
    return await job_service.retry_failed(db, http, user.id, job_id)


@router.get("/api/jobs/latest", response_model_exclude_none=True)
async def latest_job(user: ActiveUser, db: Db) -> JobResponse | None:
    """The most recent job, or null. The browser polls this while a job runs. No YouTube call."""
    return await job_service.latest_job(db, user.id)
