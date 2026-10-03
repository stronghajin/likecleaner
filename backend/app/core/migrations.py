"""Bring the database up to the latest alembic revision when the server starts."""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import BACKEND_DIR


def _alembic_config(database_url: str) -> Config:
    config = Config(str(Path(BACKEND_DIR) / "alembic.ini"))
    config.set_main_option("script_location", str(Path(BACKEND_DIR) / "alembic"))
    config.attributes["database_url"] = database_url
    config.attributes["configure_logger"] = False
    return config


async def upgrade_to_latest(database_url: str) -> None:
    # alembic's env.py runs its own event loop, so run it in a worker thread.
    await asyncio.to_thread(command.upgrade, _alembic_config(database_url), "head")
