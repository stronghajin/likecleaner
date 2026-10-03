"""`users` table (SPEC.md section 9)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import now_utc
from app.models.base import Base, UTCDateTime


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(320))
    name: Mapped[str] = mapped_column(String(255))
    picture_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now_utc)
    # Set once the admin notification mail was sent (sent only once, SPEC.md 3-3).
    notified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
