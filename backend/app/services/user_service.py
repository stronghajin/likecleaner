"""Allowlist management (DECISIONS.md 56). Used by the admin command `scripts/users.py`."""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.repositories import token_repository, user_repository
from app.schemas.user import StoredUserStatus, UserRecord, UserSummary

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    """Emails are compared lowercase, so `Someone@Gmail.com` and `someone@gmail.com` are one user."""
    return email.strip().lower()


async def add_user(session: AsyncSession, email: str) -> UserRecord:
    email = normalize_email(email)
    if not _EMAIL.match(email):
        raise AppError(400, "invalidEmail", f"'{email}' is not an email address.")
    if await user_repository.get_by_email(session, email):
        raise AppError(409, "userExists", f"{email} is already registered.")
    return await user_repository.create(session, email, "active")


async def set_status(session: AsyncSession, email: str, status: StoredUserStatus) -> UserRecord:
    email = normalize_email(email)
    user = await user_repository.get_by_email(session, email)
    if user is None:
        raise AppError(404, "userNotFound", f"{email} is not registered.")
    return await user_repository.set_status(session, user.id, status)


async def list_users(session: AsyncSession) -> list[UserSummary]:
    summaries = []
    for user in await user_repository.list_all(session):
        token = await token_repository.get(session, user.id)
        summaries.append(
            UserSummary(
                email=user.email,
                status=user.status,
                signed_in_before=user.google_sub is not None,
                youtube_connected=token is not None,
                created_at=user.created_at,
            )
        )
    return summaries
