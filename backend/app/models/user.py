"""`users` table (SPEC.md section 9, allowlist per DECISIONS.md 56).

The admin registers an email first (scripts/users.py); Google details are
filled in on that user's first sign-in.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import now_utc
from app.models.base import Base, UTCDateTime


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN ('active', 'disabled')", name="status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)  # always lowercase
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    name: Mapped[str | None] = mapped_column(String(255))
    picture_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now_utc)
