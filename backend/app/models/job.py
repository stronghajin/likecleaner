"""`jobs` and `job_items` tables (SPEC.md section 9 + DECISIONS.md 42)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import now_utc
from app.models.base import Base, UTCDateTime

JOB_TYPES = ("remove_like", "move", "move_and_unlike", "playlist_remove")
JOB_STATUSES = ("running", "completed", "stopped")
ITEM_STATUSES = ("pending", "success", "failed", "skipped", "rollback_failed", "not_processed")


def _one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(_one_of("type", JOB_TYPES), name="type"),
        CheckConstraint(_one_of("status", JOB_STATUSES), name="status"),
        Index("ix_jobs_user_id_status", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32))
    target_playlist_id: Mapped[str | None] = mapped_column(String(64))
    target_playlist_title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="running")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # The error that stopped the job (popup, SPEC.md 8-3)
    fatal_error_status: Mapped[int | None]
    fatal_error_reason: Mapped[str | None] = mapped_column(String(64))
    fatal_error_message: Mapped[str | None] = mapped_column(Text)

    # Waiting to retry after a 429 (DECISIONS.md 28)
    rate_limit_attempt: Mapped[int | None]
    rate_limit_retry_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    items: Mapped[list["JobItem"]] = relationship(
        back_populates="job", order_by="JobItem.position", cascade="all, delete-orphan"
    )


class JobItem(Base):
    __tablename__ = "job_items"
    __table_args__ = (
        CheckConstraint(_one_of("status", ITEM_STATUSES), name="status"),
        Index("ix_job_items_job_id_position", "job_id", "position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    position: Mapped[int]  # processing order = the order the user selected
    video_id: Mapped[str] = mapped_column(String(64))
    video_title: Mapped[str] = mapped_column(Text)
    playlist_item_id: Mapped[str | None] = mapped_column(String(128))  # playlist_remove jobs only
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error_code: Mapped[int | None]  # HTTP status
    error_reason: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)

    job: Mapped[Job] = relationship(back_populates="items")
