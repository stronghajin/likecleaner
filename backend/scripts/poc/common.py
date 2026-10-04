import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.clients.youtube_client import UNITS
from app.core.config import BACKEND_DIR
from app.core.security import decrypt_secret, encrypt_secret

POC_DIR = BACKEND_DIR / "data" / "poc"
TOKEN_FILE = POC_DIR / "refresh_token.enc"
# Must match the redirect URI registered in Google Cloud (PHASE2_PLAN.md 5-B).
REDIRECT_URI = "http://localhost:5173/api/auth/google/callback"


def save_refresh_token(refresh_token: str) -> None:
    POC_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(encrypt_secret(refresh_token))


def load_refresh_token() -> str:
    if not TOKEN_FILE.exists():
        raise SystemExit("No saved sign-in. Run `uv run python -m scripts.poc.login` first.")
    return decrypt_secret(TOKEN_FILE.read_text())


def save_results(name: str, results: dict[str, Any]) -> Path:
    POC_DIR.mkdir(parents=True, exist_ok=True)
    path = POC_DIR / f"{name}.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    return path


class UnitCounter:
    """Adds up quota units per API method, failed calls included (SPEC.md 4-2)."""

    def __init__(self) -> None:
        self.calls: Counter[str] = Counter()

    def add(self, method: str) -> None:
        self.calls[method] += 1

    @property
    def total(self) -> int:
        return sum(UNITS[method] * count for method, count in self.calls.items())

    def summary(self) -> dict[str, Any]:
        return {"calls": dict(self.calls), "totalUnits": self.total}
