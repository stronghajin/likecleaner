from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.repositories import health_repository
from app.schemas.health import HealthResponse


async def check(session: AsyncSession) -> HealthResponse:
    try:
        await health_repository.ping(session)
    except Exception as exc:  # noqa: BLE001 - any DB failure means "not healthy"
        raise AppError(503, "databaseUnavailable", "The database is not reachable.") from exc
    return HealthResponse(status="ok", database="ok")
