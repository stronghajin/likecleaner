"""Test setup: a throwaway SQLite file per test run, never the real backend/data DB."""

import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

_TMP_DIR = Path(tempfile.mkdtemp(prefix="likecleaner-test-"))
# Must be set before `app` is imported: the engine is created from settings at import time.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DIR / 'test.db'}"

from cryptography.fernet import Fernet  # noqa: E402

# Tests never use the real secrets in backend/.env.
os.environ["TOKEN_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["SMTP_APP_PASSWORD"] = "test-app-password"

import httpx  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
async def started_app() -> AsyncIterator[None]:
    """Runs the real startup (database migrations) once for the whole test run."""
    async with app.router.lifespan_context(app):
        yield


@pytest.fixture
async def client(started_app: None) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
