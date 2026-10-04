"""Google OAuth 2.0 (SPEC.md 3-2). Talks to Google only; no decisions about users here."""

from urllib.parse import urlencode

import httpx

from app.clients.errors import ExternalApiError
from app.core.config import get_settings
from app.schemas.auth import GoogleProfile, TokenSet
from app.schemas.common import ErrorResponse

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

BASIC_SCOPES = ["openid", "email", "profile"]
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"


class GoogleOAuthClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http
        settings = get_settings()
        self._client_id = settings.google_client_id
        self._client_secret = settings.google_client_secret

    def authorization_url(
        self,
        *,
        scopes: list[str],
        redirect_uri: str,
        state: str,
        offline: bool = False,
        login_hint: str | None = None,
    ) -> str:
        """Where to send the browser. `offline=True` asks for a refresh token (step 2 of SPEC.md 3-2)."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            # Keep scopes granted earlier (incremental authorization).
            "include_granted_scopes": "true",
        }
        if offline:
            params["access_type"] = "offline"
            # Google only returns a refresh token when the consent screen is shown.
            params["prompt"] = "consent"
        if login_hint:
            params["login_hint"] = login_hint
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> TokenSet:
        return await self._token_request(
            {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        )

    async def refresh(self, refresh_token: str) -> TokenSet:
        """Raises ExternalApiError with reason `invalid_grant` when the user removed access (DECISIONS.md 45)."""
        return await self._token_request({"grant_type": "refresh_token", "refresh_token": refresh_token})

    async def get_profile(self, access_token: str) -> GoogleProfile:
        response = await self._http.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if response.is_error:
            raise ExternalApiError(_parse_error(response))
        data = response.json()
        return GoogleProfile(
            google_sub=data["sub"],
            email=data["email"],
            name=data.get("name") or data["email"],
            picture_url=data.get("picture"),
        )

    async def _token_request(self, form: dict[str, str]) -> TokenSet:
        form |= {"client_id": self._client_id, "client_secret": self._client_secret.get_secret_value()}
        response = await self._http.post(TOKEN_URL, data=form)
        if response.is_error:
            raise ExternalApiError(_parse_error(response))
        data = response.json()
        return TokenSet(
            access_token=data["access_token"],
            expires_in=data["expires_in"],
            scopes=data.get("scope", "").split(),
            refresh_token=data.get("refresh_token"),
        )


def _parse_error(response: httpx.Response) -> ErrorResponse:
    """Google OAuth errors look like {"error": "invalid_grant", "error_description": "..."}."""
    try:
        data = response.json()
    except ValueError:
        data = {}
    reason = data.get("error") if isinstance(data.get("error"), str) else "googleOAuthError"
    message = data.get("error_description") or response.reason_phrase or "Google sign-in failed."
    return ErrorResponse(status=response.status_code, reason=reason, message=message)
