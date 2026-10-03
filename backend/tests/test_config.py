"""Settings come from one place (app/core/config.py); blank values fall back to defaults."""

from pathlib import Path

from app.core.config import BACKEND_DIR, Settings


def test_example_file_with_blank_values_uses_defaults(tmp_path: Path, monkeypatch):
    # Only the file should matter here, not the test process environment.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text((BACKEND_DIR / ".env.example").read_text())

    settings = Settings(_env_file=env_file)

    assert settings.daily_quota == 10_000
    assert settings.admin_email == "hajin300@gmail.com"
    assert settings.google_client_id == ""
    assert settings.database_url.endswith("data/likecleaner.db")


def test_filled_values_are_used(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("DAILY_QUOTA=500\nADMIN_EMAIL=admin@example.com\nGOOGLE_CLIENT_ID=abc.apps.googleusercontent.com\n")

    settings = Settings(_env_file=env_file)

    assert settings.daily_quota == 500
    assert settings.admin_email == "admin@example.com"
    assert settings.google_client_id == "abc.apps.googleusercontent.com"


def test_example_file_lists_every_setting_with_an_explanation():
    lines = (BACKEND_DIR / ".env.example").read_text().splitlines()
    keys = [line.split("=")[0] for line in lines if line and not line.startswith("#")]
    assert set(keys) == {name.upper() for name in Settings.model_fields}
    for i, line in enumerate(lines):
        if line and not line.startswith("#"):
            assert line.endswith("="), f"{line} should be blank in the example"
            assert lines[i - 1].startswith("#"), f"{line} needs a comment right above it"
