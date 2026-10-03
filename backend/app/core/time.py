"""Time helpers. Quota days follow US Pacific midnight (SPEC.md 4-1); admin mail uses KST (3-3)."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
KST = ZoneInfo("Asia/Seoul")


def now_utc() -> datetime:
    return datetime.now(UTC)


def pacific_day(at: datetime | None = None) -> date:
    """The quota day `at` belongs to."""
    return (at or now_utc()).astimezone(PACIFIC).date()


def next_quota_reset(at: datetime | None = None) -> datetime:
    """Next US Pacific midnight, in UTC. Handles daylight saving changes."""
    local = (at or now_utc()).astimezone(PACIFIC)
    next_midnight = datetime.combine(local.date() + timedelta(days=1), datetime.min.time(), tzinfo=PACIFIC)
    return next_midnight.astimezone(UTC)


def format_kst(at: datetime) -> str:
    """e.g. 2026-10-03 14:05 KST"""
    return at.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
