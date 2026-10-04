from datetime import date, datetime

from app.schemas.common import ApiModel


class QuotaResponse(ApiModel):
    """Frontend `Quota`: the whole project's YouTube units for today (US Pacific day)."""

    limit: int
    used: int
    remaining: int
    resets_at: datetime
    resets_in_seconds: int


class QuotaUsageCreate(ApiModel):
    """One YouTube API call to record, failed calls included (SPEC.md 4-1)."""

    date_pt: date
    method: str
    units: int
    user_id: int | None
    success: bool
