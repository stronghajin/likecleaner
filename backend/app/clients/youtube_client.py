"""YouTube Data API v3 over httpx. Talks to YouTube only; no business decisions here.

Every method costs quota (UNITS, SPEC.md 4-2). Failed calls cost the same, so
callers record usage whether the call succeeds or not.
"""

from typing import Any, Literal

import httpx

from app.clients.errors import ExternalApiError
from app.schemas.common import ErrorResponse
from app.schemas.youtube import (
    YouTubeCategory,
    YouTubePlaylist,
    YouTubePlaylistItem,
    YouTubePlaylistItemPage,
    YouTubePlaylistPage,
    YouTubeVideo,
    YouTubeVideoPage,
)

API_URL = "https://www.googleapis.com/youtube/v3"
PAGE_SIZE = 50

UNITS = {
    "videos.list": 1,
    "videos.rate": 50,
    "videoCategories.list": 1,
    "playlists.list": 1,
    "playlistItems.list": 1,
    "playlistItems.insert": 50,
    "playlistItems.delete": 50,
}


class YouTubeClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def list_liked_videos(self, access_token: str, page_token: str | None = None) -> YouTubeVideoPage:
        data = await self._get(
            access_token,
            "videos",
            {"part": "snippet,contentDetails", "myRating": "like", "maxResults": PAGE_SIZE, "pageToken": page_token},
        )
        return YouTubeVideoPage(
            items=[_video(item) for item in data.get("items", [])],
            next_page_token=data.get("nextPageToken"),
            total_results=data.get("pageInfo", {}).get("totalResults"),
        )

    async def get_videos(self, access_token: str, video_ids: list[str]) -> list[YouTubeVideo]:
        """Up to 50 IDs. Videos YouTube no longer serves are simply missing from the result."""
        data = await self._get(
            access_token,
            "videos",
            {"part": "snippet,contentDetails,status", "id": ",".join(video_ids), "maxResults": PAGE_SIZE},
        )
        return [_video(item) for item in data.get("items", [])]

    async def list_video_categories(
        self, access_token: str, category_ids: list[str] | None = None
    ) -> list[YouTubeCategory]:
        """English names (DECISIONS.md 46). Without ids: every US category. YouTube refuses `id` with `regionCode`."""
        params = {"part": "snippet", "hl": "en"}
        params |= {"id": ",".join(category_ids)} if category_ids else {"regionCode": "US"}
        data = await self._get(access_token, "videoCategories", params)
        return [YouTubeCategory(id=item["id"], title=item["snippet"]["title"]) for item in data.get("items", [])]

    async def list_playlists(self, access_token: str, page_token: str | None = None) -> YouTubePlaylistPage:
        data = await self._get(
            access_token,
            "playlists",
            {"part": "snippet,contentDetails", "mine": "true", "maxResults": PAGE_SIZE, "pageToken": page_token},
        )
        return YouTubePlaylistPage(
            items=[
                YouTubePlaylist(
                    id=item["id"],
                    title=item["snippet"]["title"],
                    item_count=item["contentDetails"]["itemCount"],
                )
                for item in data.get("items", [])
            ],
            next_page_token=data.get("nextPageToken"),
            total_results=data.get("pageInfo", {}).get("totalResults"),
        )

    async def list_playlist_items(
        self, access_token: str, playlist_id: str, page_token: str | None = None
    ) -> YouTubePlaylistItemPage:
        data = await self._get(
            access_token,
            "playlistItems",
            {
                "part": "snippet,contentDetails,status",
                "playlistId": playlist_id,
                "maxResults": PAGE_SIZE,
                "pageToken": page_token,
            },
        )
        return YouTubePlaylistItemPage(
            items=[_playlist_item(item) for item in data.get("items", [])],
            next_page_token=data.get("nextPageToken"),
            total_results=data.get("pageInfo", {}).get("totalResults"),
        )

    async def insert_playlist_item(
        self, access_token: str, playlist_id: str, video_id: str, position: int | None = None
    ) -> YouTubePlaylistItem:
        """`position=None` lets YouTube decide (the end, or the playlist's own sort order)."""
        snippet: dict[str, Any] = {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}
        if position is not None:
            snippet["position"] = position
        response = await self._http.post(
            f"{API_URL}/playlistItems",
            params={"part": "snippet,contentDetails,status"},
            json={"snippet": snippet},
            headers=_auth(access_token),
        )
        return _playlist_item(_json_or_raise(response))

    async def delete_playlist_item(self, access_token: str, playlist_item_id: str) -> None:
        response = await self._http.delete(
            f"{API_URL}/playlistItems", params={"id": playlist_item_id}, headers=_auth(access_token)
        )
        if response.is_error:
            raise ExternalApiError(_parse_error(response))

    async def rate_video(self, access_token: str, video_id: str, rating: Literal["like", "none"]) -> None:
        response = await self._http.post(
            f"{API_URL}/videos/rate", params={"id": video_id, "rating": rating}, headers=_auth(access_token)
        )
        if response.is_error:
            raise ExternalApiError(_parse_error(response))

    async def _get(self, access_token: str, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {key: value for key, value in params.items() if value is not None}
        response = await self._http.get(f"{API_URL}/{resource}", params=params, headers=_auth(access_token))
        return _json_or_raise(response)


def _auth(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _json_or_raise(response: httpx.Response) -> dict[str, Any]:
    if response.is_error:
        raise ExternalApiError(_parse_error(response))
    return response.json()


def _parse_error(response: httpx.Response) -> ErrorResponse:
    """YouTube errors look like {"error": {"code": 403, "message": "...", "errors": [{"reason": "quotaExceeded"}]}}."""
    try:
        error = response.json().get("error", {})
    except ValueError:
        error = {}
    if not isinstance(error, dict):
        error = {}
    details = error.get("errors") or [{}]
    reason = details[0].get("reason") or "youtubeError"
    message = error.get("message") or response.reason_phrase or "YouTube request failed."
    return ErrorResponse(status=response.status_code, reason=reason, message=message)


def _thumbnail(snippet: dict[str, Any]) -> str | None:
    # 120x90 is enough for the list (DECISIONS.md 33).
    return snippet.get("thumbnails", {}).get("default", {}).get("url")


def _video(item: dict[str, Any]) -> YouTubeVideo:
    snippet = item.get("snippet", {})
    return YouTubeVideo(
        id=item["id"],
        title=snippet.get("title", ""),
        channel_id=snippet.get("channelId"),
        channel_title=snippet.get("channelTitle"),
        category_id=snippet.get("categoryId"),
        duration=item.get("contentDetails", {}).get("duration"),
        published_at=snippet.get("publishedAt"),
        thumbnail_url=_thumbnail(snippet),
        privacy_status=item.get("status", {}).get("privacyStatus"),
    )


def _playlist_item(item: dict[str, Any]) -> YouTubePlaylistItem:
    snippet = item.get("snippet", {})
    return YouTubePlaylistItem(
        playlist_item_id=item["id"],
        position=snippet.get("position", 0),
        video_id=snippet.get("resourceId", {}).get("videoId") or item.get("contentDetails", {}).get("videoId", ""),
        title=snippet.get("title", ""),
        video_owner_channel_title=snippet.get("videoOwnerChannelTitle"),
        video_published_at=item.get("contentDetails", {}).get("videoPublishedAt"),
        thumbnail_url=_thumbnail(snippet),
        privacy_status=item.get("status", {}).get("privacyStatus"),
    )
