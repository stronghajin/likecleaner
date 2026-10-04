"""LikeCleaner backend entry point.

Run (from backend/):  uv run uvicorn app.main:app --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth, health, quota, youtube
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import register_error_handlers
from app.core.migrations import upgrade_to_latest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


SESSION_DAYS = 7  # DECISIONS.md 44


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Create or update the database tables before taking requests.
    await upgrade_to_latest(get_settings().database_url)
    # One HTTP client for every Google / YouTube call.
    app.state.http = httpx.AsyncClient(timeout=30)
    # P2-5: start the job worker and the daily cleanup here.
    yield
    await app.state.http.aclose()
    await engine.dispose()


def _session_secret() -> str:
    secret = get_settings().session_secret.get_secret_value()
    if not secret:
        raise RuntimeError("SESSION_SECRET is not set in backend/.env.")
    return secret


app = FastAPI(title="LikeCleaner API", lifespan=lifespan)
register_error_handlers(app)
# Signed cookie: the browser can read it but not change it. Holds who is signed in, never tokens (DECISIONS.md 57).
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret(),
    session_cookie="lc_session",
    max_age=SESSION_DAYS * 24 * 60 * 60,
    same_site="lax",
    https_only=get_settings().app_base_url.startswith("https://"),
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(youtube.router)
app.include_router(quota.router)
