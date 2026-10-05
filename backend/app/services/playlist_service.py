"""My playlists and their items (SPEC.md 7)."""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.youtube_client import PAGE_SIZE
from app.schemas.playlist import PlaylistItemResponse, PlaylistResponse, VideoAvailability
from app.schemas.youtube import YouTubePlaylistItem, YouTubeVideo
from app.services import memory_store, youtube_gateway
from app.services.video_details import category_names, duration_seconds

UNAVAILABLE_TITLES: dict[VideoAvailability, str] = {"deleted": "Deleted video", "private": "Private video"}


async def list_playlists(db: AsyncSession, http: httpx.AsyncClient, user_id: int) -> list[PlaylistResponse]:
    playlists: list[PlaylistResponse] = []
    page_token: str | None = None
    while True:
        page = await youtube_gateway.call(
            db, http, user_id, "playlists.list", lambda yt, token: yt.list_playlists(token, page_token)
        )
        playlists.extend(PlaylistResponse(id=p.id, title=p.title, item_count=p.item_count) for p in page.items)
        page_token = page.next_page_token
        if not page_token:
            memory_store.set_playlists(user_id, playlists)  # titles and sizes for jobs
            return playlists


def availability(item: YouTubePlaylistItem) -> VideoAvailability:
    """DECISIONS.md 53: no owner channel = a video nobody can watch; `private` vs everything else = deleted.

    The user's own private uploads still have their channel, so they stay `available`.
    """
    if item.video_owner_channel_title is not None:
        return "available"
    return "private" if item.privacy_status == "private" else "deleted"


async def get_playlist_items(
    db: AsyncSession, http: httpx.AsyncClient, user_id: int, playlist_id: str, *, refresh: bool = False
) -> list[PlaylistItemResponse]:
    """From server memory when there; otherwise (or on Resync) every page from YouTube."""
    if not refresh and (cached := memory_store.get_playlist_items(user_id, playlist_id)) is not None:
        return cached

    items: list[YouTubePlaylistItem] = []
    page_token: str | None = None
    while True:
        page = await youtube_gateway.call(
            db,
            http,
            user_id,
            "playlistItems.list",
            lambda yt, token: yt.list_playlist_items(token, playlist_id, page_token),
        )
        items.extend(page.items)
        page_token = page.next_page_token
        if not page_token:
            break

    # Category and duration come from videos.list, only for videos that can be watched (DECISIONS.md 6).
    watchable = list(dict.fromkeys(i.video_id for i in items if availability(i) == "available"))
    details: dict[str, YouTubeVideo] = {}
    for start in range(0, len(watchable), PAGE_SIZE):
        batch = watchable[start : start + PAGE_SIZE]
        found = await youtube_gateway.call(
            db, http, user_id, "videos.list", lambda yt, token: yt.get_videos(token, batch)
        )
        details.update({video.id: video for video in found})
    names = await category_names(db, http, user_id, {v.category_id for v in details.values() if v.category_id})

    result = [_item(item, details.get(item.video_id), names) for item in items]
    memory_store.set_playlist_items(user_id, playlist_id, result)
    return result


def _item(item: YouTubePlaylistItem, video: YouTubeVideo | None, names: dict[str, str]) -> PlaylistItemResponse:
    state = availability(item)
    if state != "available":
        return PlaylistItemResponse(
            playlist_item_id=item.playlist_item_id,
            position=item.position,
            video_id=item.video_id,
            title=UNAVAILABLE_TITLES[state],
            availability=state,
            channel_title=None,
            category_name=None,
            duration_seconds=None,
            published_at=None,
            thumbnail_url=None,
        )
    # A watchable video missing from videos.list (rare, e.g. blocked in some regions) keeps what the item has.
    return PlaylistItemResponse(
        playlist_item_id=item.playlist_item_id,
        position=item.position,
        video_id=item.video_id,
        title=item.title,
        availability="available",
        channel_title=item.video_owner_channel_title,
        category_name=names.get(video.category_id or "") if video else None,
        duration_seconds=duration_seconds(video.duration) if video else None,
        published_at=item.video_published_at or (video.published_at if video else None),
        thumbnail_url=item.thumbnail_url,
    )
