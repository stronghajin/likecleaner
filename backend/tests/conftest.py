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
os.environ["SESSION_SECRET"] = "test-session-secret"
os.environ["APP_BASE_URL"] = "http://localhost:5173"

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


@pytest.fixture
def google():
    """Fake Google sign-in (tests/fake_google.py). YouTube calls are not faked here."""
    import respx

    from app.clients.google_oauth_client import TOKEN_URL, USERINFO_URL
    from tests.fake_google import FakeGoogle

    with respx.mock(assert_all_called=False) as mock:
        fake = FakeGoogle("me@example.com", "sub-me")
        mock.post(TOKEN_URL).mock(side_effect=fake.token)
        mock.get(USERINFO_URL).mock(side_effect=fake.userinfo)
        fake.respx = mock
        yield fake
