from app.schemas.common import ApiModel


class AppInfoResponse(ApiModel):
    """Frontend `AppInfo`: public settings shown on screens, e.g. the Privacy Policy (DECISIONS.md 64)."""

    admin_email: str
