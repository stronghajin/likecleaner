from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.health import HealthResponse
from app.services import health_service

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(session: Annotated[AsyncSession, Depends(get_db)]) -> HealthResponse:
    """Is the server up and the database reachable?"""
    return await health_service.check(session)
