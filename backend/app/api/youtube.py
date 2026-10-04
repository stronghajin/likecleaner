"""Read-only YouTube data for the signed-in active user (P2-4). Each load uses quota (SPEC.md 4-2)."""

from fastapi import APIRouter

from app.api.deps import ActiveUser, Db, Http
from app.schemas.playlist import PlaylistItemResponse, PlaylistResponse
from app.schemas.video import VideoResponse
from app.services import likes_service, playlist_service

router = APIRouter(tags=["youtube"])


@router.get("/api/likes")
async def likes(user: ActiveUser, db: Db, http: Http, refresh: bool = False) -> list[VideoResponse]:
    """The latest ~1,000 liked videos (DECISIONS.md 52). `refresh=true` (Resync) reloads from YouTube."""
    return await likes_service.get_liked_videos(db, http, user.id, refresh=refresh)


@router.get("/api/playlists")
async def playlists(user: ActiveUser, db: Db, http: Http) -> list[PlaylistResponse]:
    return await playlist_service.list_playlists(db, http, user.id)


@router.get("/api/playlists/{playlist_id}/items")
async def playlist_items(
    playlist_id: str, user: ActiveUser, db: Db, http: Http, refresh: bool = False
) -> list[PlaylistItemResponse]:
    """Every item of one playlist. `refresh=true` (Resync) reloads from YouTube."""
    return await playlist_service.get_playlist_items(db, http, user.id, playlist_id, refresh=refresh)
