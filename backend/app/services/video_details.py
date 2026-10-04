"""Helpers shared by the liked list and playlist items: durations and category names."""

import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import memory_store, youtube_gateway

_DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


def duration_seconds(iso: str | None) -> int | None:
    """YouTube durations look like PT1H2M3S (live streams can be P0D). None if missing or odd."""
    match = _DURATION.match(iso or "")
    if not match:
        return None
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


async def category_names(
    db: AsyncSession, http: httpx.AsyncClient, user_id: int, category_ids: set[str]
) -> dict[str, str]:
    """English names for these category ids. Remembered in memory, so usually 1 unit per server run.

    First the whole US list (DECISIONS.md 46); ids outside it are asked by id.
    """
    known = memory_store.category_names()
    if category_ids - known.keys() and not known:
        found = await youtube_gateway.call(
            db, http, user_id, "videoCategories.list", lambda yt, token: yt.list_video_categories(token)
        )
        known.update({category.id: category.title for category in found})
    missing = sorted(category_ids - known.keys())
    if missing:
        found = await youtube_gateway.call(
            db, http, user_id, "videoCategories.list", lambda yt, token: yt.list_video_categories(token, missing)
        )
        known.update({category.id: category.title for category in found})
        # Ids YouTube does not know get no name; do not ask again for them.
        known.update({category_id: "" for category_id in missing if category_id not in known})
    return {category_id: known[category_id] for category_id in category_ids if category_id in known}
