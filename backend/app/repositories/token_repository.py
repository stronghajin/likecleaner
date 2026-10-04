"""`oauth_tokens` table access. Tokens arrive and leave encrypted; decrypting is the services' job."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_token import OAuthToken
from app.schemas.auth import StoredToken


def _record(row: OAuthToken) -> StoredToken:
    return StoredToken(user_id=row.user_id, refresh_token=row.refresh_token, scopes=row.scopes.split())


async def get(session: AsyncSession, user_id: int) -> StoredToken | None:
    row = await session.get(OAuthToken, user_id)
    return _record(row) if row else None


async def save(session: AsyncSession, token: StoredToken) -> StoredToken:
    row = await session.get(OAuthToken, token.user_id)
    if row is None:
        row = OAuthToken(user_id=token.user_id)
        session.add(row)
    row.refresh_token = token.refresh_token
    row.scopes = " ".join(token.scopes)
    await session.commit()
    return _record(row)


async def delete(session: AsyncSession, user_id: int) -> None:
    row = await session.get(OAuthToken, user_id)
    if row is not None:
        await session.delete(row)
        await session.commit()
