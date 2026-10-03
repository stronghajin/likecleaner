"""LikeCleaner backend entry point.

Run (from backend/):  uv run uvicorn app.main:app --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import register_error_handlers
from app.core.migrations import upgrade_to_latest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Create or update the database tables before taking requests.
    await upgrade_to_latest(get_settings().database_url)
    # P2-5: start the job worker and the daily cleanup here.
    yield
    await engine.dispose()


app = FastAPI(title="LikeCleaner API", lifespan=lifespan)
register_error_handlers(app)
app.include_router(health.router)
