"""Today's shared YouTube quota (SPEC.md 4-1): the day ends at US Pacific midnight."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.time import next_quota_reset, now_utc, pacific_day
from app.repositories import quota_repository
from app.schemas.quota import QuotaResponse


async def status(db: AsyncSession) -> QuotaResponse:
    now = now_utc()
    limit = get_settings().daily_quota
    used = await quota_repository.units_used_on(db, pacific_day(now))
    resets_at = next_quota_reset(now)
    return QuotaResponse(
        limit=limit,
        used=used,
        remaining=max(0, limit - used),
        resets_at=resets_at,
        resets_in_seconds=max(0, int((resets_at - now).total_seconds())),
    )
