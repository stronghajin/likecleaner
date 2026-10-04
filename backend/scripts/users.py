"""Admin command for the allowlist (DECISIONS.md 56). Run from backend/:

    uv run python -m scripts.users add someone@gmail.com
    uv run python -m scripts.users disable someone@gmail.com
    uv run python -m scripts.users enable someone@gmail.com
    uv run python -m scripts.users list
"""

import argparse
import asyncio
import sys

from app.core.config import get_settings
from app.core.db import SessionFactory, engine
from app.core.errors import AppError
from app.core.migrations import upgrade_to_latest
from app.core.time import format_kst
from app.services import user_service


async def run(command: str, email: str | None) -> int:
    # Works even before the server has ever started: bring the tables up to date first.
    await upgrade_to_latest(get_settings().database_url)
    try:
        async with SessionFactory() as db:
            if command == "add":
                user = await user_service.add_user(db, email or "")
                print(f"Added {user.email} (active). They can sign in now.")
            elif command == "disable":
                user = await user_service.set_status(db, email or "", "disabled")
                print(f"{user.email} is now disabled. They will see Access Denied.")
            elif command == "enable":
                user = await user_service.set_status(db, email or "", "active")
                print(f"{user.email} is now active.")
            else:
                users = await user_service.list_users(db)
                if not users:
                    print("No users yet. Add one with: uv run python -m scripts.users add someone@gmail.com")
                for u in users:
                    signed_in = "signed in before" if u.signed_in_before else "never signed in"
                    youtube = "YouTube connected" if u.youtube_connected else "YouTube not connected"
                    print(f"{u.email:<40} {u.status:<9} {signed_in:<17} {youtube:<22} added {format_kst(u.created_at)}")
        return 0
    except AppError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.users", description="Manage who can use LikeCleaner.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("add", "register an email (active)"),
        ("disable", "block a registered email"),
        ("enable", "unblock a registered email"),
    ]:
        sub.add_parser(name, help=help_text).add_argument("email")
    sub.add_parser("list", help="show every registered email")
    args = parser.parse_args(argv)
    return asyncio.run(run(args.command, getattr(args, "email", None)))


if __name__ == "__main__":
    sys.exit(main())
