from app.schemas.common import ApiModel


class MailMessage(ApiModel):
    to: str
    subject: str
    body: str
