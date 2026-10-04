"""Lists kept in server memory only, never in the DB (SPEC.md 6-1, DECISIONS.md 58).

Per user: the liked list and each opened playlist's items. Dropped on sign-out
and after the 7-day session length. Empty after a restart; the services then
load from YouTube again.
"""

import time
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.schemas.playlist import PlaylistItemResponse
from app.schemas.video import VideoResponse

T = TypeVar("T")

MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # DECISIONS.md 44


@dataclass
class _Entry(Generic[T]):
    value: T
    stored_at: float


_likes: dict[int, _Entry[list[VideoResponse]]] = {}
_playlist_items: dict[tuple[int, str], _Entry[list[PlaylistItemResponse]]] = {}
# YouTube category id -> English name. Not personal data, shared by everyone.
_category_names: dict[str, str] = {}


def _fresh(entry: _Entry[T] | None) -> T | None:
    if entry is None or time.monotonic() - entry.stored_at > MAX_AGE_SECONDS:
        return None
    return entry.value


def get_likes(user_id: int) -> list[VideoResponse] | None:
    return _fresh(_likes.get(user_id))


def set_likes(user_id: int, videos: list[VideoResponse]) -> None:
    _likes[user_id] = _Entry(videos, time.monotonic())


def get_playlist_items(user_id: int, playlist_id: str) -> list[PlaylistItemResponse] | None:
    return _fresh(_playlist_items.get((user_id, playlist_id)))


def set_playlist_items(user_id: int, playlist_id: str, items: list[PlaylistItemResponse]) -> None:
    _playlist_items[(user_id, playlist_id)] = _Entry(items, time.monotonic())


def category_names() -> dict[str, str]:
    return _category_names


def forget_user(user_id: int) -> None:
    _likes.pop(user_id, None)
    for key in [key for key in _playlist_items if key[0] == user_id]:
        del _playlist_items[key]
