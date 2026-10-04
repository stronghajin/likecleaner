"""Google OAuth data, as returned by `clients/google_oauth_client.py`."""

from typing import Literal

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


class StoredToken(ApiModel):
    """An `oauth_tokens` row. `refresh_token` is still encrypted here."""

    user_id: int
    refresh_token: str
    scopes: list[str]


class SignInProfile(ApiModel):
    """Who signed in at step 1. Kept in the session to show the Access Denied screen."""

    email: str
    name: str
    picture_url: str | None = None


class OAuthPending(ApiModel):
    """An OAuth round trip in progress, kept in the session until Google calls back."""

    state: str
    step: Literal[1, 2]
    # Step 2 only: who passed step 1.
    user_id: int | None = None
    google_sub: str | None = None


class SessionState(ApiModel):
    """Everything the session cookie holds. Never tokens."""

    user_id: int | None = None
    denied: SignInProfile | None = None
    oauth: OAuthPending | None = None


class CallbackResult(ApiModel):
    """What to do after Google calls back: where to send the browser and the new session."""

    redirect_to: str
    session: SessionState
