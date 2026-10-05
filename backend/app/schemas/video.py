from typing import Literal

from app.schemas.common import ApiModel, ErrorResponse


class VideoResponse(ApiModel):
    """Frontend `Video`: one liked video."""

    id: str
    title: str
    channel_id: str
    channel_title: str
    category_name: str
    duration_seconds: int
    published_at: str  # upload date, ISO
    thumbnail_url: str


class LikedVideosResponse(ApiModel):
    """Frontend `LikedVideosResult`: every liked video that can still be watched (DECISIONS.md 59)."""

    videos: list[VideoResponse]
    # Deleted/private videos left out of `videos`.
    hidden_unavailable: int
    # YouTube's count of every like (DECISIONS.md 61). Above videos + hidden = older likes YouTube does not hand out.
    total_liked: int | None = None


class LikesLoadStatus(ApiModel):
    """Progress of loading the liked list in the background (DECISIONS.md 59)."""

    state: Literal["idle", "loading", "ready", "error"]
    # Liked entries read from YouTube so far (shown + hidden).
    loaded: int
    hidden_unavailable: int
    error: ErrorResponse | None = None
