"""Daily cleanup: jobs and quota usage older than 30 days are deleted (SPEC.md 9)."""

import asyncio
import logging

from app.core.db import SessionFactory
from app.services import job_service

logger = logging.getLogger(__name__)

DAY_SECONDS = 24 * 60 * 60


async def run_daily() -> None:
    """Runs once at start-up, then every 24 hours until the server stops."""
    while True:
        try:
            async with SessionFactory() as db:
                await job_service.delete_old_data(db)
        except Exception:
            logger.exception("Daily cleanup failed")
        await asyncio.sleep(DAY_SECONDS)
