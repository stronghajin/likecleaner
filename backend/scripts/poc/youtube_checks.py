"""PoC 1, 3, 4 (SPEC.md 14) with the account saved by `scripts.poc.login`.

Run from backend/:  uv run python -m scripts.poc.youtube_checks

- 1: page through all liked videos (read only)
- 3: how deleted / private videos look in playlistItems.list (read only)
- 4: position=0 insert into `LC Test 1` (manual order) and `LC Test 2` (automatic order),
     a middle insert into `LC Test 2`, and a duplicate entry in `LC Test 1`.
     Every item added here is removed again before the script ends.

Only counts and response shapes are saved; no titles of the user's own videos.
"""

import asyncio
from collections import Counter
from typing import Any

import httpx

from app.clients.errors import ExternalApiError
from app.clients.google_oauth_client import GoogleOAuthClient
from app.clients.youtube_client import YouTubeClient
from app.schemas.youtube import YouTubePlaylist, YouTubePlaylistItem
from scripts.poc.common import UnitCounter, load_refresh_token, save_results

MANUAL_TEST_PLAYLIST = "LC Test 1"
AUTO_TEST_PLAYLIST = "LC Test 2"
UNAVAILABLE_TITLES = {"Deleted video", "Private video"}
# Writes show up in playlistItems.list only after a few seconds (seen in the PoC).
SETTLE_SECONDS = 8


async def check_likes(yt: YouTubeClient, token: str, units: UnitCounter) -> dict[str, Any]:
    fetched, pages, totals, page_sizes = [], 0, set(), []
    page_token = None
    while True:
        units.add("videos.list")
        page = await yt.list_liked_videos(token, page_token)
        pages += 1
        fetched.extend(video.id for video in page.items)
        page_sizes.append(len(page.items))
        if page.total_results is not None:
            totals.add(page.total_results)
        page_token = page.next_page_token
        if not page_token:
            break
    return {
        "fetched": len(fetched),
        "unique": len(set(fetched)),
        "pages": pages,
        "pageSizes": page_sizes,
        "totalResultsReported": sorted(totals),
    }


async def all_playlist_items(
    yt: YouTubeClient, token: str, playlist_id: str, units: UnitCounter
) -> list[YouTubePlaylistItem]:
    items, page_token = [], None
    while True:
        units.add("playlistItems.list")
        page = await yt.list_playlist_items(token, playlist_id, page_token)
        items.extend(page.items)
        page_token = page.next_page_token
        if not page_token:
            return items


def _shape(item: YouTubePlaylistItem) -> dict[str, Any]:
    """What an item looks like, without its title (unless it is YouTube's placeholder title)."""
    return {
        "title": item.title if item.title in UNAVAILABLE_TITLES else "(normal title)",
        "privacyStatus": item.privacy_status,
        "hasVideoOwnerChannelTitle": item.video_owner_channel_title is not None,
        "hasVideoPublishedAt": item.video_published_at is not None,
        "hasThumbnail": item.thumbnail_url is not None,
    }


async def check_unavailable(
    yt: YouTubeClient, token: str, playlists: list[YouTubePlaylist], units: UnitCounter
) -> dict[str, Any]:
    total_items = 0
    unavailable: list[YouTubePlaylistItem] = []
    normal_shapes: Counter[str] = Counter()
    odd_shapes: list[dict[str, Any]] = []  # normal title but no channel, or the other way round
    duplicates: dict[str, int] = {}

    for playlist in playlists:
        items = await all_playlist_items(yt, token, playlist.id, units)
        total_items += len(items)
        counts = Counter(item.video_id for item in items)
        extra = sum(count - 1 for count in counts.values() if count > 1)
        if extra:
            # Only the test playlists are named; the user's own playlist titles are not saved.
            key = playlist.title if playlist.title.startswith("LC Test") else "(other playlists)"
            duplicates[key] = duplicates.get(key, 0) + extra
        for item in items:
            by_title = item.title in UNAVAILABLE_TITLES
            no_owner = item.video_owner_channel_title is None
            if by_title:
                unavailable.append(item)
            elif no_owner:
                odd_shapes.append(_shape(item))
            else:
                normal_shapes[str(sorted(_shape(item).items()))] += 1

    shapes = Counter(str(sorted(_shape(item).items())) for item in unavailable)

    # Does videos.list still return these videos?
    lookup: dict[str, Any] = {}
    ids = sorted({item.video_id for item in unavailable})[:50]
    if ids:
        units.add("videos.list")
        found = await yt.get_videos(token, ids)
        lookup = {
            "asked": len(ids),
            "returned": len(found),
            "returnedPrivacyStatuses": dict(Counter(video.privacy_status for video in found)),
        }

    return {
        "playlistsScanned": len(playlists),
        "itemsScanned": total_items,
        "unavailableByTitle": dict(Counter(item.title for item in unavailable)),
        "unavailableShapes": {shape: count for shape, count in shapes.items()},
        "normalShapes": dict(normal_shapes),
        "normalTitleButNoOwner": odd_shapes[:20],
        "videosListLookupOfUnavailable": lookup,
        "duplicateEntries": duplicates,
    }


async def try_front_insert(
    yt: YouTubeClient, token: str, playlist: YouTubePlaylist, video_id: str, units: UnitCounter
) -> dict[str, Any]:
    """Adds `video_id` at position 0, falls back to no position (SPEC.md 6), then removes what was added."""
    added: list[str] = []
    result: dict[str, Any] = {"playlistSizeBefore": playlist.item_count}
    try:
        try:
            units.add("playlistItems.insert")
            item = await yt.insert_playlist_item(token, playlist.id, video_id, position=0)
            added.append(item.playlist_item_id)
            result["positionZero"] = {"ok": True, "returnedPosition": item.position}
        except ExternalApiError as e:
            result["positionZero"] = {"ok": False, "error": e.error.model_dump()}
            units.add("playlistItems.insert")
            item = await yt.insert_playlist_item(token, playlist.id, video_id)
            added.append(item.playlist_item_id)
            result["noPosition"] = {"ok": True, "returnedPosition": item.position}

        # Where did it really land?
        await asyncio.sleep(SETTLE_SECONDS)
        items = await all_playlist_items(yt, token, playlist.id, units)
        positions = [i.position for i in items if i.playlist_item_id in added]
        result["positionAfterReload"] = positions[0] if positions else None
        result["playlistSizeAfterInsert"] = len(items)
    finally:
        for playlist_item_id in added:
            units.add("playlistItems.delete")
            await yt.delete_playlist_item(token, playlist_item_id)
        result["cleanedUp"] = len(added)
    return result


async def check_front_insert(
    yt: YouTubeClient, token: str, playlists: list[YouTubePlaylist], liked_ids: list[str], units: UnitCounter
) -> dict[str, Any]:
    by_title = {p.title: p for p in playlists}
    missing = [t for t in (MANUAL_TEST_PLAYLIST, AUTO_TEST_PLAYLIST) if t not in by_title]
    if missing:
        return {"skipped": f"Playlist not found: {', '.join(missing)}"}

    # A liked video that is in neither test playlist, so the insert is a clean "new" add.
    in_tests: set[str] = set()
    for title in (MANUAL_TEST_PLAYLIST, AUTO_TEST_PLAYLIST):
        in_tests |= {i.video_id for i in await all_playlist_items(yt, token, by_title[title].id, units)}
    video_id = next((v for v in liked_ids if v not in in_tests), None)
    if video_id is None:
        return {"skipped": "No liked video outside the test playlists."}

    return {
        "manualOrder": await try_front_insert(yt, token, by_title[MANUAL_TEST_PLAYLIST], video_id, units),
        "automaticOrder": await try_front_insert(yt, token, by_title[AUTO_TEST_PLAYLIST], video_id, units),
        "automaticOrderMiddle": await try_middle_insert(yt, token, by_title[AUTO_TEST_PLAYLIST], video_id, units),
        "duplicate": await try_duplicate(yt, token, by_title[MANUAL_TEST_PLAYLIST], units),
    }


async def try_middle_insert(
    yt: YouTubeClient, token: str, playlist: YouTubePlaylist, video_id: str, units: UnitCounter
) -> dict[str, Any]:
    """position=1 shows whether YouTube enforces the playlist's automatic order on API inserts."""
    added: list[str] = []
    try:
        units.add("playlistItems.insert")
        try:
            item = await yt.insert_playlist_item(token, playlist.id, video_id, position=1)
        except ExternalApiError as e:
            return {"ok": False, "error": e.error.model_dump()}
        added.append(item.playlist_item_id)
        await asyncio.sleep(SETTLE_SECONDS)
        items = await all_playlist_items(yt, token, playlist.id, units)
        positions = [i.position for i in items if i.playlist_item_id == item.playlist_item_id]
        return {"ok": True, "returnedPosition": item.position, "positionAfterReload": positions[0] if positions else None}
    finally:
        for playlist_item_id in added:
            units.add("playlistItems.delete")
            await yt.delete_playlist_item(token, playlist_item_id)


async def try_duplicate(yt: YouTubeClient, token: str, playlist: YouTubePlaylist, units: UnitCounter) -> dict[str, Any]:
    """The YouTube website will not add a video twice; the API is used to make a duplicate entry."""
    existing = (await all_playlist_items(yt, token, playlist.id, units))[0]
    added: list[str] = []
    try:
        units.add("playlistItems.insert")
        item = await yt.insert_playlist_item(token, playlist.id, existing.video_id)
        added.append(item.playlist_item_id)
        await asyncio.sleep(SETTLE_SECONDS)
        same = [i for i in await all_playlist_items(yt, token, playlist.id, units) if i.video_id == existing.video_id]
        return {
            "entriesForSameVideo": len(same),
            "distinctPlaylistItemIds": len({i.playlist_item_id for i in same}),
            "positions": [i.position for i in same],
        }
    finally:
        for playlist_item_id in added:
            units.add("playlistItems.delete")
            await yt.delete_playlist_item(token, playlist_item_id)


async def main() -> None:
    units = UnitCounter()
    results: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=30) as http:
        tokens = await GoogleOAuthClient(http).refresh(load_refresh_token())
        token = tokens.access_token.get_secret_value()
        yt = YouTubeClient(http)

        print("PoC 1: liked videos ...", flush=True)
        results["likes"] = await check_likes(yt, token, units)
        print(f"  {results['likes']}", flush=True)

        # First liked page again for a test video (1 unit).
        units.add("videos.list")
        liked_ids = [v.id for v in (await yt.list_liked_videos(token)).items]

        playlists, page_token = [], None
        while True:
            units.add("playlists.list")
            page = await yt.list_playlists(token, page_token)
            playlists.extend(page.items)
            page_token = page.next_page_token
            if not page_token:
                break

        print(f"PoC 3: scanning {len(playlists)} playlists (read only) ...", flush=True)
        results["unavailable"] = await check_unavailable(yt, token, playlists, units)
        print(f"  unavailable by title: {results['unavailable']['unavailableByTitle']}", flush=True)

        print("PoC 4: position=0 insert into LC Test playlists (removed again) ...", flush=True)
        try:
            results["frontInsert"] = await check_front_insert(yt, token, playlists, liked_ids, units)
        except ExternalApiError as e:
            results["frontInsert"] = {"failed": e.error.model_dump()}
        print(f"  {results['frontInsert']}", flush=True)

    results["quota"] = units.summary()
    path = save_results("youtube_checks", results)
    print(f"\nQuota used: {units.total} units. Saved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
