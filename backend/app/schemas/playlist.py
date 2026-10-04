from typing import Literal

from app.schemas.common import ApiModel

VideoAvailability = Literal["available", "deleted", "private"]


class PlaylistResponse(ApiModel):
    """Frontend `Playlist`."""

    id: str
    title: str
    item_count: int


class PlaylistItemResponse(ApiModel):
    """Frontend `PlaylistItem`. Deleted/private videos have no channel, category, duration or date."""

    playlist_item_id: str
    position: int
    video_id: str
    title: str
    availability: VideoAvailability
    channel_title: str | None
    category_name: str | None
    duration_seconds: int | None
    published_at: str | None
    thumbnail_url: str | None
