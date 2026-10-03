"""DB reachability check. No business decisions here."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ping(session: AsyncSession) -> None:
    """Raises if the database cannot be queried."""
    await session.execute(text("SELECT 1"))
