"""`quota_usage` table (SPEC.md section 9): one row per YouTube API call, failed calls included."""

from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import now_utc
from app.models.base import Base, UTCDateTime


class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    __table_args__ = (Index("ix_quota_usage_date_pt", "date_pt"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date_pt: Mapped[date] = mapped_column(Date)  # US Pacific day the call counted against
    method: Mapped[str] = mapped_column(String(64))  # e.g. videos.rate
    units: Mapped[int]
    # The quota is shared by the whole project, so usage stays counted even if the user is deleted.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    success: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now_utc)
