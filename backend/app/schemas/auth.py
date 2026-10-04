"""Google OAuth data, as returned by `clients/google_oauth_client.py`."""

from pydantic import SecretStr

from app.schemas.common import ApiModel


class TokenSet(ApiModel):
    """Result of a code exchange or a refresh. Google only sends a refresh token on offline consent."""

    access_token: SecretStr
    expires_in: int
    scopes: list[str]
    refresh_token: SecretStr | None = None


class GoogleProfile(ApiModel):
    """The signed-in Google account (openid userinfo)."""

    google_sub: str
    email: str
    name: str
    picture_url: str | None = None
