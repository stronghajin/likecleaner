"""Settings read from `backend/.env` (SPEC.md section 2)."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # A blank line like `DAILY_QUOTA=` means "use the default below".
        env_ignore_empty=True,
    )

    # Google OAuth (filled in by the user before P2-2)
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")

    # Where data deletion requests go; shown on the Privacy Policy (SPEC.md 10, DECISIONS.md 64)
    admin_email: str = "hajin300@gmail.com"
    # Mail settings: currently unused (DECISIONS.md 56). Kept for clients/mail_client.py.
    smtp_user: str = ""
    smtp_app_password: SecretStr = SecretStr("")

    # Encrypts refresh tokens at rest (Fernet key)
    token_encryption_key: SecretStr = SecretStr("")
    # Signs the session cookie
    session_secret: SecretStr = SecretStr("")

    # Shared daily YouTube quota for the whole GCP project
    daily_quota: int = 10_000

    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'data' / 'likecleaner.db'}"

    # Address people open in the browser. Google's redirect URI is built from it (DECISIONS.md 57).
    app_base_url: str = "http://localhost:5173"

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.app_base_url.rstrip('/')}/api/auth/google/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
