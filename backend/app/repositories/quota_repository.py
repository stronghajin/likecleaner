"""`quota_usage` table access."""

from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota_usage import QuotaUsage
from app.schemas.quota import QuotaUsageCreate


async def record(session: AsyncSession, usage: QuotaUsageCreate) -> None:
    session.add(QuotaUsage(**usage.model_dump(by_alias=False)))
    await session.commit()


async def units_used_on(session: AsyncSession, day: date) -> int:
    total = await session.scalar(select(func.sum(QuotaUsage.units)).where(QuotaUsage.date_pt == day))
    return int(total or 0)


async def delete_before(session: AsyncSession, day: date) -> None:
    """Usage rows older than `day` (SPEC.md 9: kept 30 days)."""
    await session.execute(delete(QuotaUsage).where(QuotaUsage.date_pt < day))
    await session.commit()
