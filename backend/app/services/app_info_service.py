"""Public settings the screens show. Only what anyone may see: no secrets."""

from app.core.config import get_settings
from app.schemas.app_info import AppInfoResponse


async def get() -> AppInfoResponse:
    return AppInfoResponse(admin_email=get_settings().admin_email)
