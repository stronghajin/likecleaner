from fastapi import APIRouter

from app.schemas.app_info import AppInfoResponse
from app.services import app_info_service

router = APIRouter(tags=["app-info"])


@router.get("/api/app-info")
async def app_info() -> AppInfoResponse:
    """No sign-in needed: the Privacy Policy is public. ADMIN_EMAIL from backend/.env (SPEC.md 10)."""
    return await app_info_service.get()
