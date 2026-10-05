"""Lists kept in server memory only, never in the DB (SPEC.md 6-1, DECISIONS.md 58).

Per user: the liked list and each opened playlist's items. Dropped on sign-out
and after the 7-day session length. Empty after a restart; the services then
load from YouTube again.
"""

import time
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.schemas.playlist import PlaylistItemResponse, PlaylistResponse
from app.schemas.video import LikedVideosResponse, VideoResponse

T = TypeVar("T")

MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # DECISIONS.md 44


@dataclass
class _Entry(Generic[T]):
    value: T
    stored_at: float


_likes: dict[int, _Entry[LikedVideosResponse]] = {}
_playlist_items: dict[tuple[int, str], _Entry[list[PlaylistItemResponse]]] = {}
# The last playlists.list answer, for job titles and sizes only. GET /api/playlists still asks YouTube.
_playlists: dict[int, _Entry[list[PlaylistResponse]]] = {}
# YouTube category id -> English name. Not personal data, shared by everyone.
_category_names: dict[str, str] = {}


def _fresh(entry: _Entry[T] | None) -> T | None:
    if entry is None or time.monotonic() - entry.stored_at > MAX_AGE_SECONDS:
        return None
    return entry.value


def get_likes(user_id: int) -> LikedVideosResponse | None:
    return _fresh(_likes.get(user_id))


def set_likes(user_id: int, likes: LikedVideosResponse) -> None:
    _likes[user_id] = _Entry(likes, time.monotonic())


def get_playlist_items(user_id: int, playlist_id: str) -> list[PlaylistItemResponse] | None:
    return _fresh(_playlist_items.get((user_id, playlist_id)))


def set_playlist_items(user_id: int, playlist_id: str, items: list[PlaylistItemResponse]) -> None:
    _playlist_items[(user_id, playlist_id)] = _Entry(items, time.monotonic())


def get_playlists(user_id: int) -> list[PlaylistResponse] | None:
    return _fresh(_playlists.get(user_id))


def set_playlists(user_id: int, playlists: list[PlaylistResponse]) -> None:
    _playlists[user_id] = _Entry(playlists, time.monotonic())


# ---- Job results, applied as each item succeeds (DECISIONS.md 55): no reload from YouTube needed. ----


def find_liked_video(user_id: int, video_id: str) -> VideoResponse | None:
    likes = get_likes(user_id)
    return next((v for v in likes.videos if v.id == video_id), None) if likes else None


def remove_like(user_id: int, video_id: str) -> None:
    entry = _likes.get(user_id)
    if entry is None or not any(v.id == video_id for v in entry.value.videos):
        return
    likes = entry.value
    entry.value = likes.model_copy(
        update={
            "videos": [v for v in likes.videos if v.id != video_id],
            "total_liked": likes.total_liked - 1 if likes.total_liked else likes.total_liked,
        }
    )


def add_playlist_item(user_id: int, playlist_id: str, item: PlaylistItemResponse, *, at_top: bool) -> None:
    entry = _playlist_items.get((user_id, playlist_id))
    if entry is not None:
        items = [item, *entry.value] if at_top else [*entry.value, item]
        entry.value = _renumbered(items)
    _change_count(user_id, playlist_id, +1)


def remove_playlist_item(user_id: int, playlist_id: str, playlist_item_id: str) -> None:
    entry = _playlist_items.get((user_id, playlist_id))
    if entry is not None:
        entry.value = _renumbered([i for i in entry.value if i.playlist_item_id != playlist_item_id])
    _change_count(user_id, playlist_id, -1)


def _renumbered(items: list[PlaylistItemResponse]) -> list[PlaylistItemResponse]:
    return [i if i.position == n else i.model_copy(update={"position": n}) for n, i in enumerate(items)]


def _change_count(user_id: int, playlist_id: str, delta: int) -> None:
    entry = _playlists.get(user_id)
    if entry is not None:
        entry.value = [
            p.model_copy(update={"item_count": max(0, p.item_count + delta)}) if p.id == playlist_id else p
            for p in entry.value
        ]


def category_names() -> dict[str, str]:
    return _category_names


def forget_user(user_id: int) -> None:
    _likes.pop(user_id, None)
    _playlists.pop(user_id, None)
    for key in [key for key in _playlist_items if key[0] == user_id]:
        del _playlist_items[key]
