"""Two-step Google sign-in for allowlisted users (SPEC.md 3-2, DECISIONS.md 56, 57).

Step 1 asks only for `openid email profile`. Only an `active` user without a saved
YouTube permission goes on to step 2 (`youtube`, offline access). The api layer
keeps the returned SessionState in the signed session cookie.
"""

import logging
import secrets

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import ExternalApiError
from app.clients.google_oauth_client import BASIC_SCOPES, YOUTUBE_SCOPE, GoogleOAuthClient
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decrypt_secret, encrypt_secret
from app.repositories import token_repository, user_repository
from app.schemas.auth import CallbackResult, OAuthPending, SessionState, SignInProfile, StoredToken, TokenSet
from app.schemas.user import UserRecord, UserResponse
from app.services.user_service import normalize_email

logger = logging.getLogger(__name__)

HOME = "/"
# The landing page shows "LikeCleaner needs access to your YouTube account…" for this (DECISIONS.md 57).
YOUTUBE_PERMISSION_DENIED = "/?signin_error=youtube_permission"

_SIGNED_OUT = SessionState()


def start_login(http: httpx.AsyncClient) -> CallbackResult:
    """Step 1. Starts a fresh session; Google always shows its account chooser."""
    state = secrets.token_urlsafe(24)
    url = GoogleOAuthClient(http).authorization_url(
        scopes=BASIC_SCOPES,
        redirect_uri=get_settings().google_redirect_uri,
        state=state,
        choose_account=True,
    )
    return CallbackResult(redirect_to=url, session=SessionState(oauth=OAuthPending(state=state, step=1)))


async def handle_callback(
    db: AsyncSession,
    http: httpx.AsyncClient,
    current: SessionState,
    *,
    code: str | None,
    state: str | None,
    error: str | None,
) -> CallbackResult:
    pending = current.oauth
    if pending is None or state is None or not secrets.compare_digest(state, pending.state):
        # Not a sign-in this browser started (old tab, forged link): sign in from scratch.
        return CallbackResult(redirect_to=HOME, session=_SIGNED_OUT)
    try:
        if pending.step == 1:
            return await _finish_step_one(db, http, code, error)
        return await _finish_step_two(db, http, pending, code, error)
    except ExternalApiError as e:
        logger.warning("Google sign-in failed at step %s: %s %s", pending.step, e.error.status, e.error.reason)
        return CallbackResult(redirect_to=HOME, session=_SIGNED_OUT)


async def _finish_step_one(
    db: AsyncSession, http: httpx.AsyncClient, code: str | None, error: str | None
) -> CallbackResult:
    if error or not code:
        return CallbackResult(redirect_to=HOME, session=_SIGNED_OUT)  # cancelled on Google's page
    oauth = GoogleOAuthClient(http)
    tokens = await oauth.exchange_code(code, get_settings().google_redirect_uri)
    profile = await oauth.get_profile(tokens.access_token.get_secret_value())
    email = normalize_email(profile.email)

    user = await user_repository.get_by_email(db, email)
    if user is None or user.status != "active":
        denied = SignInProfile(email=email, name=profile.name, picture_url=profile.picture_url)
        return CallbackResult(redirect_to=HOME, session=SessionState(denied=denied))

    if (user.google_sub, user.name, user.picture_url) != (profile.google_sub, profile.name, profile.picture_url):
        user = await user_repository.update_profile(
            db, user.id, google_sub=profile.google_sub, name=profile.name, picture_url=profile.picture_url
        )

    saved = await token_repository.get(db, user.id)
    if saved is not None and YOUTUBE_SCOPE in saved.scopes:
        # YouTube permission is asked only once (DECISIONS.md 57).
        return CallbackResult(redirect_to=HOME, session=SessionState(user_id=user.id))

    state = secrets.token_urlsafe(24)
    url = oauth.authorization_url(
        scopes=[YOUTUBE_SCOPE],
        redirect_uri=get_settings().google_redirect_uri,
        state=state,
        offline=True,
        login_hint=email,
    )
    pending = OAuthPending(state=state, step=2, user_id=user.id, google_sub=profile.google_sub)
    return CallbackResult(redirect_to=url, session=SessionState(oauth=pending))


async def _finish_step_two(
    db: AsyncSession, http: httpx.AsyncClient, pending: OAuthPending, code: str | None, error: str | None
) -> CallbackResult:
    denied = CallbackResult(redirect_to=YOUTUBE_PERMISSION_DENIED, session=_SIGNED_OUT)
    if error or not code:
        return denied
    oauth = GoogleOAuthClient(http)
    tokens = await oauth.exchange_code(code, get_settings().google_redirect_uri)
    # The user can untick the YouTube box on Google's consent screen.
    if YOUTUBE_SCOPE not in tokens.scopes or tokens.refresh_token is None:
        return denied

    profile = await oauth.get_profile(tokens.access_token.get_secret_value())
    if profile.google_sub != pending.google_sub or pending.user_id is None:
        # A different Google account was picked at step 2.
        return CallbackResult(redirect_to=HOME, session=_SIGNED_OUT)
    user = await user_repository.get_by_id(db, pending.user_id)
    if user is None or user.status != "active":
        return CallbackResult(redirect_to=HOME, session=_SIGNED_OUT)

    await token_repository.save(
        db,
        StoredToken(
            user_id=user.id,
            refresh_token=encrypt_secret(tokens.refresh_token.get_secret_value()),
            scopes=tokens.scopes,
        ),
    )
    return CallbackResult(redirect_to=HOME, session=SessionState(user_id=user.id))


async def get_me(db: AsyncSession, current: SessionState) -> UserResponse | None:
    """The signed-in user, with today's status from the DB. None = treat as signed out."""
    if current.user_id is not None:
        user = await user_repository.get_by_id(db, current.user_id)
        return _response(user) if user else None
    if current.denied is not None:
        user = await user_repository.get_by_email(db, current.denied.email)
        if user is not None and user.status == "active":
            return None  # registered since: sign in again to continue
        return UserResponse(
            id="",
            email=current.denied.email,
            name=current.denied.name,
            picture_url=current.denied.picture_url or "",
            status="disabled" if user else "not_registered",
        )
    return None


async def require_active(db: AsyncSession, current: SessionState) -> UserRecord:
    """Gate for every YouTube-related API (DECISIONS.md 56). Reads the DB on each request."""
    user = await user_repository.get_by_id(db, current.user_id) if current.user_id is not None else None
    if user is None:
        raise AppError(401, "notSignedIn", "Please sign in to continue.")
    if user.status != "active":
        raise AppError(403, "accessDenied", "This Google account doesn't have access to LikeCleaner.")
    return user


async def get_access_token(db: AsyncSession, http: httpx.AsyncClient, user_id: int) -> TokenSet:
    """A fresh access token from the saved refresh token (used from P2-4)."""
    saved = await token_repository.get(db, user_id)
    if saved is None:
        raise _reauth_required()
    try:
        return await GoogleOAuthClient(http).refresh(decrypt_secret(saved.refresh_token))
    except ExternalApiError as e:
        if e.error.reason == "invalid_grant":
            # Access was removed in Google account settings: ask for step 2 again (DECISIONS.md 45).
            await token_repository.delete(db, user_id)
            raise _reauth_required() from e
        raise AppError(502, "googleAuthError", e.error.message) from e


def _reauth_required() -> AppError:
    return AppError(403, "youtubeReauthRequired", "Please sign in again to reconnect your YouTube account.")


def _response(user: UserRecord) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name or user.email,
        picture_url=user.picture_url or "",
        status=user.status,
    )
