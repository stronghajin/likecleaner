"""Gmail SMTP with an app password (DECISIONS.md 40)."""

from email.message import EmailMessage

import aiosmtplib

from app.core.config import get_settings
from app.schemas.mail import MailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


class MailClient:
    async def send(self, mail: MailMessage) -> None:
        settings = get_settings()
        message = EmailMessage()
        message["From"] = settings.smtp_user
        message["To"] = mail.to
        message["Subject"] = mail.subject
        message.set_content(mail.body)
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=settings.smtp_user,
            password=settings.smtp_app_password.get_secret_value(),
        )
