"""`users` table access. No business decisions here; rows leave as UserRecord."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import StoredUserStatus, UserRecord


async def get_by_id(session: AsyncSession, user_id: int) -> UserRecord | None:
    row = await session.get(User, user_id)
    return UserRecord.model_validate(row) if row else None


async def get_by_email(session: AsyncSession, email: str) -> UserRecord | None:
    row = await session.scalar(select(User).where(User.email == email))
    return UserRecord.model_validate(row) if row else None


async def create(session: AsyncSession, email: str, status: StoredUserStatus) -> UserRecord:
    row = User(email=email, status=status)
    session.add(row)
    await session.commit()
    return UserRecord.model_validate(row)


async def set_status(session: AsyncSession, user_id: int, status: StoredUserStatus) -> UserRecord:
    row = await session.get_one(User, user_id)
    row.status = status
    await session.commit()
    return UserRecord.model_validate(row)


async def update_profile(
    session: AsyncSession, user_id: int, *, google_sub: str, name: str, picture_url: str | None
) -> UserRecord:
    row = await session.get_one(User, user_id)
    row.google_sub = google_sub
    row.name = name
    row.picture_url = picture_url
    await session.commit()
    return UserRecord.model_validate(row)


async def list_all(session: AsyncSession) -> list[UserRecord]:
    rows = await session.scalars(select(User).order_by(User.created_at, User.id))
    return [UserRecord.model_validate(row) for row in rows]
