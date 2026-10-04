"""Users (allowlist, DECISIONS.md 56)."""

from datetime import datetime
from typing import Literal

from app.schemas.common import ApiModel

# Stored in the `users` table.
StoredUserStatus = Literal["active", "disabled"]
# What the frontend sees (`UserStatus` in types.ts): an unregistered email is not a DB row.
UserStatus = Literal["active", "disabled", "not_registered"]


class UserRecord(ApiModel):
    """One `users` row. Google details are empty until the first sign-in."""

    id: int
    email: str
    google_sub: str | None
    name: str | None
    picture_url: str | None
    status: StoredUserStatus
    created_at: datetime


class UserResponse(ApiModel):
    """Frontend `User`. `id` is empty for an email the admin has not registered."""

    id: str
    email: str
    name: str
    picture_url: str
    status: UserStatus


class UserSummary(ApiModel):
    """One line of `scripts.users list`."""

    email: str
    status: StoredUserStatus
    signed_in_before: bool
    youtube_connected: bool
    created_at: datetime
