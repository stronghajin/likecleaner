"""Worst-case units for a job (SPEC.md 4-3). Same formula as `estimateUnits` in frontend/src/services/quotaEstimate.ts."""

import math

from app.clients.youtube_client import PAGE_SIZE, UNITS
from app.schemas.job import JobType


def _pages(count: int) -> int:
    return max(1, math.ceil(count / PAGE_SIZE))


def estimate_units(job_type: JobType, count: int, target_item_count: int = 0) -> int:
    """`target_item_count` = size of the destination playlist (move jobs).

    Moves read the destination first (playlistItems.list pages + videos.list pages for its details,
    DECISIONS.md 63) and keep 50 for one refused "add at the top" (DECISIONS.md 30).
    """
    details = _pages(target_item_count) if target_item_count > 0 else 0
    move_setup = (_pages(target_item_count) + details) * UNITS["playlistItems.list"] + UNITS["playlistItems.insert"]
    match job_type:
        case "remove_like":
            return count * UNITS["videos.rate"]
        case "move":
            return move_setup + count * UNITS["playlistItems.insert"]
        case "move_and_unlike":
            return move_setup + count * (UNITS["playlistItems.insert"] + UNITS["videos.rate"])
        case "playlist_remove":
            return count * UNITS["playlistItems.delete"]


def max_affordable_items(job_type: JobType, units_left: int, target_item_count: int = 0) -> int:
    fixed = estimate_units(job_type, 0, target_item_count)
    per_item = estimate_units(job_type, 1, target_item_count) - fixed
    return max(0, min(100, (units_left - fixed) // per_item))
