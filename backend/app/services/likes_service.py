"""The whole liked list, from the "Liked videos" playlist (LL) (DECISIONS.md 59, replaces 52).

`videos.list(myRating=like)` stops near 1,000; LL goes to the end. Each LL page
(1 unit) is followed by one `videos.list(id=…)` (1 unit) for the details of the
videos that can still be watched; deleted/private ones are only counted.

A full load takes a minute or two for thousands of likes, so it runs as a
background task per user. The browser starts it, polls the progress, then
fetches the list. Other requests keep working meanwhile.
"""

import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from app.core.db import SessionFactory
from app.core.errors import AppError
from app.schemas.common import ErrorResponse
from app.schemas.video import LikedVideosResponse, LikesLoadStatus, VideoResponse
from app.schemas.youtube import YouTubeVideo
from app.services import memory_store, youtube_gateway
from app.services.playlist_service import availability
from app.services.video_details import category_names, duration_seconds

logger = logging.getLogger(__name__)

LIKED_PLAYLIST_ID = "LL"


@dataclass
class _Load:
    loaded: int = 0
    hidden: int = 0
    error: ErrorResponse | None = None
    task: asyncio.Task[None] | None = field(default=None, repr=False)


# user_id -> the load running now, or the one that failed last.
_loads: dict[int, _Load] = {}


def start_load(http: httpx.AsyncClient, user_id: int, *, refresh: bool = False) -> LikesLoadStatus:
    """Starts loading unless a load is running, or (without refresh) the list is already in memory."""
    current = _loads.get(user_id)
    if current and current.task and not current.task.done():
        return load_status(user_id)
    if not refresh and memory_store.get_likes(user_id) is not None:
        return load_status(user_id)
    load = _Load()
    _loads[user_id] = load
    load.task = asyncio.create_task(_run(http, user_id, load), name=f"likes-{user_id}")
    return load_status(user_id)


def load_status(user_id: int) -> LikesLoadStatus:
    load = _loads.get(user_id)
    if load and load.task and not load.task.done():
        return LikesLoadStatus(state="loading", loaded=load.loaded, hidden_unavailable=load.hidden)
    if load and load.error:
        return LikesLoadStatus(state="error", loaded=load.loaded, hidden_unavailable=load.hidden, error=load.error)
    likes = memory_store.get_likes(user_id)
    if likes is not None:
        total = len(likes.videos) + likes.hidden_unavailable
        return LikesLoadStatus(state="ready", loaded=total, hidden_unavailable=likes.hidden_unavailable)
    return LikesLoadStatus(state="idle", loaded=0, hidden_unavailable=0)


def get_liked_videos(user_id: int) -> LikedVideosResponse:
    likes = memory_store.get_likes(user_id)
    if likes is None or load_status(user_id).state == "loading":
        raise AppError(409, "likesNotReady", "Your liked videos are still loading.")
    return likes


def cancel_all() -> None:
    """Server shutdown: stop every running load."""
    for user_id in list(_loads):
        cancel(user_id)


def cancel(user_id: int) -> None:
    """Sign-out: stop a running load and forget it."""
    load = _loads.pop(user_id, None)
    if load and load.task and not load.task.done():
        load.task.cancel()


async def _run(http: httpx.AsyncClient, user_id: int, load: _Load) -> None:
    try:
        async with SessionFactory() as db:
            liked: list[YouTubeVideo] = []
            seen: set[str] = set()
            page_token: str | None = None
            while True:
                page = await youtube_gateway.call(
                    db,
                    http,
                    user_id,
                    "playlistItems.list",
                    lambda yt, token: yt.list_playlist_items(token, LIKED_PLAYLIST_ID, page_token),
                )
                # A like added mid-load can push a video onto the next page as well; count it once.
                fresh = list({i.video_id: i for i in page.items if i.video_id not in seen}.values())
                seen.update(i.video_id for i in fresh)
                watchable = [i.video_id for i in fresh if availability(i) == "available"]
                found: dict[str, YouTubeVideo] = {}
                if watchable:
                    videos = await youtube_gateway.call(
                        db, http, user_id, "videos.list", lambda yt, token: yt.get_videos(token, watchable)
                    )
                    found = {video.id: video for video in videos}
                # Keep LL order (most recently liked first). Missing from videos.list = cannot be watched.
                liked.extend(found[video_id] for video_id in watchable if video_id in found)
                load.loaded += len(fresh)
                load.hidden += len(fresh) - sum(1 for video_id in watchable if video_id in found)
                page_token = page.next_page_token
                if not page_token:
                    break

            names = await category_names(db, http, user_id, {v.category_id for v in liked if v.category_id})
        result = LikedVideosResponse(
            videos=[_video(v, names) for v in liked],
            hidden_unavailable=load.hidden,
        )
        memory_store.set_likes(user_id, result)
    except AppError as e:
        load.error = ErrorResponse(status=e.status, reason=e.reason, message=e.message)
    except Exception:
        logger.exception("Loading liked videos failed")
        load.error = ErrorResponse(status=500, reason="internalError", message="Something went wrong on the server.")


def _video(v: YouTubeVideo, names: dict[str, str]) -> VideoResponse:
    return VideoResponse(
        id=v.id,
        title=v.title,
        channel_id=v.channel_id or "",
        channel_title=v.channel_title or "",
        category_name=names.get(v.category_id or "", ""),
        duration_seconds=duration_seconds(v.duration) or 0,
        published_at=v.published_at or "",
        thumbnail_url=v.thumbnail_url or "",
    )
