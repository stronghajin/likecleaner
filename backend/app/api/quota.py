from fastapi import APIRouter

from app.api.deps import ActiveUser, Db
from app.schemas.quota import QuotaResponse
from app.services import quota_service

router = APIRouter(tags=["quota"])


@router.get("/api/quota")
async def quota(_: ActiveUser, db: Db) -> QuotaResponse:
    """Today's project-wide units (US Pacific day). No YouTube call."""
    return await quota_service.status(db)
