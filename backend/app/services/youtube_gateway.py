"""The only way services call YouTube. Every call is recorded in `quota_usage`.

Successful, failed and retried calls each add one row with the method's units
(SPEC.md 4-1: failed calls cost quota too). YouTube errors come out as AppError
with the same {status, reason, message}.
"""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import ExternalApiError
from app.clients.youtube_client import UNITS, YouTubeClient
from app.core.errors import AppError
from app.core.time import pacific_day
from app.repositories import quota_repository
from app.schemas.quota import QuotaUsageCreate
from app.services import auth_service

logger = logging.getLogger(__name__)

T = TypeVar("T")

# user_id -> (access token, monotonic time it stops being used). Memory only, never stored.
_access_tokens: dict[int, tuple[str, float]] = {}
_EARLY_SECONDS = 60


async def _access_token(db: AsyncSession, http: httpx.AsyncClient, user_id: int) -> str:
    cached = _access_tokens.get(user_id)
    if cached and cached[1] > time.monotonic():
        return cached[0]
    tokens = await auth_service.get_access_token(db, http, user_id)
    token = tokens.access_token.get_secret_value()
    _access_tokens[user_id] = (token, time.monotonic() + max(0, tokens.expires_in - _EARLY_SECONDS))
    return token


def forget_user(user_id: int) -> None:
    _access_tokens.pop(user_id, None)


async def call(
    db: AsyncSession,
    http: httpx.AsyncClient,
    user_id: int,
    method: str,
    request: Callable[[YouTubeClient, str], Awaitable[T]],
) -> T:
    """Runs one YouTube API call, e.g. call(db, http, uid, "videos.list", lambda yt, t: yt.get_videos(t, ids))."""
    units = UNITS[method]  # KeyError here = a method without a known cost; never call unrecorded
    token = await _access_token(db, http, user_id)
    try:
        result = await request(YouTubeClient(http), token)
    except ExternalApiError as e:
        await _record(db, user_id, method, units, success=False)
        if e.error.status == 401:
            forget_user(user_id)  # token expired early; the next call refreshes it
        raise AppError(e.error.status, e.error.reason, e.error.message) from e
    except httpx.HTTPError as e:
        # The request may or may not have reached YouTube; count it to stay on the safe side.
        await _record(db, user_id, method, units, success=False)
        logger.warning("YouTube %s did not answer: %s", method, type(e).__name__)
        raise AppError(502, "youtubeUnavailable", "YouTube did not respond. Please try again.") from e
    await _record(db, user_id, method, units, success=True)
    return result


async def _record(db: AsyncSession, user_id: int, method: str, units: int, *, success: bool) -> None:
    await quota_repository.record(
        db,
        QuotaUsageCreate(date_pt=pacific_day(), method=method, units=units, user_id=user_id, success=success),
    )
