"""PoC 5: send one test mail through Gmail SMTP with the app password (DECISIONS.md 40).

Run from backend/:  uv run python -m scripts.poc.mail_check
"""

import asyncio

import aiosmtplib

from app.clients.mail_client import MailClient
from app.core.config import get_settings
from app.core.time import format_kst, now_utc
from app.schemas.mail import MailMessage
from scripts.poc.common import save_results


async def main() -> None:
    to = get_settings().admin_email
    sent_at = format_kst(now_utc())
    try:
        await MailClient().send(
            MailMessage(
                to=to,
                subject="[LikeCleaner] PoC test mail",
                body=f"This is a test mail from LikeCleaner P2-2.\nSent at: {sent_at}",
            )
        )
        result = {"ok": True, "sentAt": sent_at}
        print(f"Sent a test mail to {to} at {sent_at}.")
    except aiosmtplib.SMTPException as e:
        # The exception names the problem (e.g. bad login) and never contains the password.
        result = {"ok": False, "error": type(e).__name__, "code": getattr(e, "code", None)}
        print(f"Mail failed: {type(e).__name__} {getattr(e, 'code', '')}")
    save_results("mail", result)


if __name__ == "__main__":
    asyncio.run(main())
