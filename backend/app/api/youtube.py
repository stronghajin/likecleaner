"""Read-only YouTube data for the signed-in active user (P2-4). Each load uses quota (SPEC.md 4-2)."""

from fastapi import APIRouter

from app.api.deps import ActiveUser, Db, Http
from app.schemas.playlist import PlaylistItemResponse, PlaylistResponse
from app.schemas.video import LikedVideosResponse, LikesLoadStatus
from app.services import likes_service, playlist_service

router = APIRouter(tags=["youtube"])


@router.post("/api/likes/load")
async def load_likes(user: ActiveUser, http: Http, refresh: bool = False) -> LikesLoadStatus:
    """Starts loading every liked video in the background (DECISIONS.md 59). `refresh=true` = Resync."""
    return likes_service.start_load(http, user.id, refresh=refresh)


@router.get("/api/likes/status")
async def likes_status(user: ActiveUser) -> LikesLoadStatus:
    """How far the load is: idle / loading (with count) / ready / error."""
    return likes_service.load_status(user.id)


@router.get("/api/likes")
async def likes(user: ActiveUser) -> LikedVideosResponse:
    """The loaded list. 409 likesNotReady while loading or before the first load."""
    return likes_service.get_liked_videos(user.id)


@router.get("/api/playlists")
async def playlists(user: ActiveUser, db: Db, http: Http) -> list[PlaylistResponse]:
    return await playlist_service.list_playlists(db, http, user.id)


@router.get("/api/playlists/{playlist_id}/items")
async def playlist_items(
    playlist_id: str, user: ActiveUser, db: Db, http: Http, refresh: bool = False
) -> list[PlaylistItemResponse]:
    """Every item of one playlist. `refresh=true` (Resync) reloads from YouTube."""
    return await playlist_service.get_playlist_items(db, http, user.id, playlist_id, refresh=refresh)
