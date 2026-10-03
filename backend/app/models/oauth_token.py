"""`oauth_tokens` table (SPEC.md section 9). The refresh token is stored encrypted."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import now_utc
from app.models.base import Base, UTCDateTime


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    # Deleting a user deletes their token (SPEC.md 10: deletion on request).
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    refresh_token: Mapped[str] = mapped_column(Text)  # encrypted with TOKEN_ENCRYPTION_KEY
    scopes: Mapped[str] = mapped_column(String(1024))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now_utc, onupdate=now_utc)
