"""Jobs (SPEC.md 8): what the browser sends, what it gets back, and what the layers pass around.

`JobResponse` / `JobItemResponse` match the frontend `Job` / `JobItem` in `services/types.ts`.
"""

from datetime import datetime
from typing import Literal

from app.schemas.common import ApiModel, ErrorResponse

JobType = Literal["remove_like", "move", "move_and_unlike", "playlist_remove"]
JobStatus = Literal["running", "completed", "stopped"]
JobItemStatus = Literal["pending", "success", "failed", "skipped", "rollback_failed", "not_processed"]


class CreateJobRequest(ApiModel):
    """Frontend `CreateJobInput`: videoIds (+ targetPlaylistId for moves), or playlistId + playlistItemIds."""

    type: JobType
    video_ids: list[str] | None = None
    target_playlist_id: str | None = None
    playlist_id: str | None = None
    playlist_item_ids: list[str] | None = None


class RateLimitInfo(ApiModel):
    """Waiting to retry after a 429 (DECISIONS.md 28)."""

    attempt: int
    retry_at: datetime


class JobItemResponse(ApiModel):
    video_id: str
    video_title: str
    playlist_item_id: str | None = None
    status: JobItemStatus
    error: ErrorResponse | None = None


class JobResponse(ApiModel):
    id: str
    type: JobType
    target_playlist_id: str | None = None
    target_playlist_title: str | None = None
    status: JobStatus
    created_at: datetime
    finished_at: datetime | None = None
    items: list[JobItemResponse]
    fatal_error: ErrorResponse | None = None
    rate_limit: RateLimitInfo | None = None


class JobItemCreate(ApiModel):
    video_id: str
    video_title: str
    playlist_item_id: str | None = None


class JobCreate(ApiModel):
    """A checked job, ready to store (services → repositories)."""

    id: str
    user_id: int
    type: JobType
    target_playlist_id: str | None = None
    target_playlist_title: str | None = None
    items: list[JobItemCreate]


class JobItemResult(ApiModel):
    """The outcome of one item (worker → repositories). `position` = its place in the job."""

    position: int
    status: JobItemStatus
    error: ErrorResponse | None = None
