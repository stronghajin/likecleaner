"""YouTube Data API data, as returned by `clients/youtube_client.py`.

These mirror what YouTube sends, with only the fields we use. Deciding what they
mean (e.g. whether a playlist item is deleted or private) is the services' job.
"""

from app.schemas.common import ApiModel


class YouTubeVideo(ApiModel):
    id: str
    title: str
    channel_id: str | None = None
    channel_title: str | None = None
    category_id: str | None = None
    duration: str | None = None  # ISO 8601, e.g. "PT4M13S"
    published_at: str | None = None
    thumbnail_url: str | None = None
    privacy_status: str | None = None


class YouTubeVideoPage(ApiModel):
    items: list[YouTubeVideo]
    next_page_token: str | None = None
    total_results: int | None = None


class YouTubePlaylist(ApiModel):
    id: str
    title: str
    item_count: int


class YouTubePlaylistPage(ApiModel):
    items: list[YouTubePlaylist]
    next_page_token: str | None = None
    total_results: int | None = None


class YouTubePlaylistItem(ApiModel):
    playlist_item_id: str
    position: int
    video_id: str
    title: str
    # Missing for deleted/private videos (SPEC.md 14, item 3).
    video_owner_channel_title: str | None = None
    video_published_at: str | None = None
    thumbnail_url: str | None = None
    privacy_status: str | None = None


class YouTubePlaylistItemPage(ApiModel):
    items: list[YouTubePlaylistItem]
    next_page_token: str | None = None
    total_results: int | None = None


class YouTubeCategory(ApiModel):
    id: str
    title: str
