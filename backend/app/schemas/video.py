from app.schemas.common import ApiModel


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
