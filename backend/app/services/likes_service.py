"""The liked list (SPEC.md 6-1). YouTube returns only about the latest 1,000 (DECISIONS.md 52)."""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.video import VideoResponse
from app.schemas.youtube import YouTubeVideo
from app.services import memory_store, youtube_gateway
from app.services.video_details import category_names, duration_seconds


async def get_liked_videos(
    db: AsyncSession, http: httpx.AsyncClient, user_id: int, *, refresh: bool = False
) -> list[VideoResponse]:
    """From server memory when there; otherwise (or on Resync) every page from YouTube."""
    if not refresh and (cached := memory_store.get_likes(user_id)) is not None:
        return cached

    videos: dict[str, YouTubeVideo] = {}
    page_token: str | None = None
    while True:
        page = await youtube_gateway.call(
            db, http, user_id, "videos.list", lambda yt, token: yt.list_liked_videos(token, page_token)
        )
        for video in page.items:
            videos.setdefault(video.id, video)  # a like added mid-load can shift a video onto two pages
        page_token = page.next_page_token
        if not page_token:
            break

    names = await category_names(db, http, user_id, {v.category_id for v in videos.values() if v.category_id})
    result = [
        VideoResponse(
            id=v.id,
            title=v.title,
            channel_id=v.channel_id or "",
            channel_title=v.channel_title or "",
            category_name=names.get(v.category_id or "", ""),
            duration_seconds=duration_seconds(v.duration) or 0,
            published_at=v.published_at or "",
            thumbnail_url=v.thumbnail_url or "",
        )
        for v in videos.values()
    ]
    memory_store.set_likes(user_id, result)
    return result
