"""Daily copy of the SQLite database (DECISIONS 65). Run inside the server container:

    docker exec likecleaner-api python -m scripts.backup

Writes backups/likecleaner-YYYY-MM-DD.db with SQLite's own backup (a plain file copy can be
broken while WAL mode is on) and deletes copies older than KEEP_DAYS. Copies hold the same data
as the database, so they follow the Privacy Policy's 30-day promise: keep them shorter than that.
"""

import os
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import BACKEND_DIR, get_settings

KEEP_DAYS = 14
PREFIX = "likecleaner-"


def main() -> int:
    db_path = make_url(get_settings().database_url).database
    if not db_path or db_path == ":memory:" or not Path(db_path).exists():
        print(f"No database file at {db_path!r}.", file=sys.stderr)
        return 1
    backup_dir = Path(os.environ.get("BACKUP_DIR", BACKEND_DIR / "backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    target = backup_dir / f"{PREFIX}{today.isoformat()}.db"
    partial = target.with_suffix(".db.partial")
    source = sqlite3.connect(db_path)
    copy = sqlite3.connect(partial)
    try:
        source.backup(copy)
    finally:
        copy.close()
        source.close()
    partial.replace(target)
    print(f"Saved {target.name} ({target.stat().st_size:,} bytes).")

    oldest_kept = today - timedelta(days=KEEP_DAYS - 1)
    for old in sorted(backup_dir.glob(f"{PREFIX}*.db")):
        try:
            day = date.fromisoformat(old.stem.removeprefix(PREFIX))
        except ValueError:
            continue
        if day < oldest_kept:
            old.unlink()
            print(f"Deleted {old.name} (older than {KEEP_DAYS} days).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
