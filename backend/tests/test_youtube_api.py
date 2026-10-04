"""Read APIs (likes, playlists, items, quota) against a fake YouTube (respx). Nothing reaches the internet."""

import asyncio

import httpx
import pytest
from sqlalchemy import select

from app.clients.youtube_client import API_URL
from app.core.db import SessionFactory
from app.models.quota_usage import QuotaUsage
from app.services.video_details import duration_seconds
from tests.fake_google import callback, set_status, sign_in_active, start


def _video(video_id: str, category: str = "10", **snippet) -> dict:
    return {
        "id": video_id,
        "snippet": {
            "title": f"Title {video_id}",
            "channelId": "c1",
            "channelTitle": "Chan",
            "categoryId": category,
            "publishedAt": "2020-01-01T00:00:00Z",
            "thumbnails": {"default": {"url": f"https://i/{video_id}.jpg"}},
            **snippet,
        },
        "contentDetails": {"duration": "PT1M5S"},
        "status": {"privacyStatus": "public"},
    }


def _item(item_id: str, video_id: str, position: int, *, owner: str | None, privacy: str, title: str) -> dict:
    snippet = {
        "title": title,
        "position": position,
        "resourceId": {"videoId": video_id},
        **({"videoOwnerChannelTitle": owner, "thumbnails": {"default": {"url": "https://t"}}} if owner else {}),
    }
    details = {"videoId": video_id, **({"videoPublishedAt": "2021-02-03T00:00:00Z"} if owner else {})}
    return {"id": item_id, "snippet": snippet, "contentDetails": details, "status": {"privacyStatus": privacy}}


class FakeYouTube:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_with: tuple[int, str] | None = None

    def videos(self, request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if self.fail_with:
            status, reason = self.fail_with
            self.calls.append("videos.list")
            return httpx.Response(status, json={"error": {"code": status, "message": reason, "errors": [{"reason": reason}]}})
        self.calls.append(f"videos.list(id={params['id']})")
        category = {"v3": "20"}
        ids = params["id"].split(",")
        return httpx.Response(200, json={"items": [_video(i, category.get(i, "10")) for i in ids if i != "gone"]})

    def categories(self, request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if "id" in params and "regionCode" in params:
            return httpx.Response(400, json={"error": {"code": 400, "message": "x", "errors": [{"reason": "incompatibleParameters"}]}})
        # The US list has Music only; Gaming must be asked by id.
        names = {"10": "Music"} if "regionCode" in params else {"20": "Gaming"}
        self.calls.append(f"videoCategories.list({params.get('id', 'US')})")
        ids = params["id"].split(",") if "id" in params else list(names)
        return httpx.Response(200, json={"items": [{"id": i, "snippet": {"title": names[i]}} for i in ids if i in names]})

    def playlists(self, request: httpx.Request) -> httpx.Response:
        self.calls.append("playlists.list")
        return httpx.Response(
            200,
            json={
                "items": [
                    {"id": "PL1", "snippet": {"title": "Road trip"}, "contentDetails": {"itemCount": 5}},
                    {"id": "PL2", "snippet": {"title": "Later"}, "contentDetails": {"itemCount": 0}},
                ]
            },
        )

    def playlist_items(self, request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if self.fail_with:
            status, reason = self.fail_with
            self.calls.append("playlistItems.list")
            return httpx.Response(status, json={"error": {"code": status, "message": reason, "errors": [{"reason": reason}]}})
        if params["playlistId"] == "LL":
            # The "Liked videos" playlist (DECISIONS.md 59), newest first.
            self.calls.append(f"playlistItems.list(LL,{params.get('pageToken', 'p1')})")
            if params.get("pageToken") == "p2":
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            _item("l3", "v3", 3, owner="Chan", privacy="public", title="Title v3"),
                            # v1 again: a like added mid-load shifted it onto the next page
                            _item("l4", "v1", 4, owner="Chan", privacy="public", title="Title v1"),
                            _item("l5", "gone", 5, owner="Chan", privacy="public", title="Region blocked"),
                        ]
                    },
                )
            return httpx.Response(
                200,
                json={
                    "items": [
                        _item("l0", "v1", 0, owner="Chan", privacy="public", title="Title v1"),
                        _item("l1", "vd", 1, owner=None, privacy="privacyStatusUnspecified", title="Deleted video"),
                        _item("l2", "v2", 2, owner="Chan", privacy="public", title="Title v2"),
                    ],
                    "nextPageToken": "p2",
                },
            )
        self.calls.append("playlistItems.list")
        return httpx.Response(
            200,
            json={
                "items": [
                    _item("i0", "v1", 0, owner="Chan", privacy="public", title="Title v1"),
                    _item("i1", "vd", 1, owner=None, privacy="privacyStatusUnspecified", title="Deleted video"),
                    _item("i2", "vp", 2, owner=None, privacy="private", title="Private video"),
                    # The user's own private upload: still watchable by them (DECISIONS.md 53).
                    _item("i3", "mine", 3, owner="Me", privacy="private", title="My private clip"),
                    _item("i4", "gone", 4, owner="Chan", privacy="public", title="Region blocked"),
                ]
            },
        )


@pytest.fixture
def youtube(google):
    fake = FakeYouTube()
    google.respx.get(f"{API_URL}/videos").mock(side_effect=fake.videos)
    google.respx.get(f"{API_URL}/videoCategories").mock(side_effect=fake.categories)
    google.respx.get(f"{API_URL}/playlists").mock(side_effect=fake.playlists)
    google.respx.get(f"{API_URL}/playlistItems").mock(side_effect=fake.playlist_items)
    return fake


async def _load_likes(client: httpx.AsyncClient, *, refresh: bool = False) -> dict:
    """Starts the background load and waits for it like the browser does. Returns the final status."""
    status = (await client.post("/api/likes/load", params={"refresh": "true"} if refresh else None)).json()
    for _ in range(200):
        if status["state"] != "loading":
            return status
        await asyncio.sleep(0.01)
        status = (await client.get("/api/likes/status")).json()
    raise AssertionError("load did not finish")


async def _usage_rows() -> list[QuotaUsage]:
    async with SessionFactory() as db:
        rows = await db.scalars(select(QuotaUsage).order_by(QuotaUsage.id))
        return list(rows)


async def test_whole_liked_list_from_the_liked_playlist(client, google, youtube):
    await sign_in_active(client, google, "likes@example.com", "sub-likes")
    quota_before = (await client.get("/api/quota")).json()["used"]
    assert (await client.get("/api/likes")).json()["reason"] == "likesNotReady"  # nothing loaded yet

    status = await _load_likes(client)
    # 5 different liked entries; the deleted one and the one videos.list does not know are hidden.
    assert status == {"state": "ready", "loaded": 5, "hiddenUnavailable": 2, "error": None}

    body = (await client.get("/api/likes")).json()
    assert body["hiddenUnavailable"] == 2
    videos = body["videos"]
    assert [v["id"] for v in videos] == ["v1", "v2", "v3"]  # liked order, each once
    assert videos[0] == {
        "id": "v1",
        "title": "Title v1",
        "channelId": "c1",
        "channelTitle": "Chan",
        "categoryName": "Music",
        "durationSeconds": 65,
        "publishedAt": "2020-01-01T00:00:00Z",
        "thumbnailUrl": "https://i/v1.jpg",
    }
    assert videos[2]["categoryName"] == "Gaming"
    # Details are asked only for watchable videos, one videos.list per LL page.
    assert "videos.list(id=v1,v2)" in youtube.calls
    assert "videos.list(id=v3,gone)" in youtube.calls
    # 2 LL pages + 2 videos.list + the category lists (remembered across users and tests)
    used = (await client.get("/api/quota")).json()["used"] - quota_before
    assert used == 4 + sum(c.startswith("videoCategories.list") for c in youtube.calls)


async def test_second_load_comes_from_memory_and_resync_reloads(client, google, youtube):
    await sign_in_active(client, google, "memory@example.com", "sub-memory")
    await _load_likes(client)
    calls = len(youtube.calls)

    assert (await _load_likes(client))["state"] == "ready"
    assert len((await client.get("/api/likes")).json()["videos"]) == 3
    assert len(youtube.calls) == calls  # no YouTube call, 0 units

    await _load_likes(client, refresh=True)
    assert youtube.calls[calls:] == [
        "playlistItems.list(LL,p1)",
        "videos.list(id=v1,v2)",
        "playlistItems.list(LL,p2)",
        "videos.list(id=v3,gone)",
    ]  # categories already known


async def test_other_requests_answer_while_likes_load(client, google, youtube):
    await sign_in_active(client, google, "busy@example.com", "sub-busy")
    started = (await client.post("/api/likes/load")).json()
    assert started["state"] in ("loading", "ready")
    assert (await client.get("/api/quota")).status_code == 200
    assert (await client.get("/api/playlists")).status_code == 200
    assert (await _load_likes(client))["state"] == "ready"


async def test_sign_out_drops_the_lists_in_memory(client, google, youtube):
    await sign_in_active(client, google, "out@example.com", "sub-out")
    await _load_likes(client)
    await client.post("/api/auth/logout")

    # Sign in again (YouTube step is skipped now) and the list is loaded from YouTube again.
    await callback(client, code="c1", state=await start(client))
    assert (await client.get("/api/likes/status")).json()["state"] == "idle"
    calls = len(youtube.calls)
    await _load_likes(client)
    assert "playlistItems.list(LL,p1)" in youtube.calls[calls:]


async def test_playlists(client, google, youtube):
    await sign_in_active(client, google, "pl@example.com", "sub-pl")
    response = await client.get("/api/playlists")
    assert response.json() == [
        {"id": "PL1", "title": "Road trip", "itemCount": 5},
        {"id": "PL2", "title": "Later", "itemCount": 0},
    ]


async def test_playlist_items_mark_deleted_and_private_but_keep_own_private_uploads(client, google, youtube):
    await sign_in_active(client, google, "items@example.com", "sub-items")
    items = (await client.get("/api/playlists/PL1/items")).json()
    by_id = {i["playlistItemId"]: i for i in items}

    assert [i["availability"] for i in items] == ["available", "deleted", "private", "available", "available"]
    assert by_id["i1"] == {
        "playlistItemId": "i1",
        "position": 1,
        "videoId": "vd",
        "title": "Deleted video",
        "availability": "deleted",
        "channelTitle": None,
        "categoryName": None,
        "durationSeconds": None,
        "publishedAt": None,
        "thumbnailUrl": None,
    }
    assert by_id["i0"]["categoryName"] == "Music"
    assert by_id["i0"]["durationSeconds"] == 65
    assert by_id["i0"]["publishedAt"] == "2021-02-03T00:00:00Z"
    assert by_id["i3"]["channelTitle"] == "Me"
    # Watchable but missing from videos.list: no category or duration, still listed.
    assert (by_id["i4"]["categoryName"], by_id["i4"]["durationSeconds"]) == (None, None)
    # videos.list is asked only for watchable videos.
    assert "videos.list(id=v1,mine,gone)" in youtube.calls

    calls = len(youtube.calls)
    await client.get("/api/playlists/PL1/items")
    assert len(youtube.calls) == calls
    await client.get("/api/playlists/PL1/items", params={"refresh": "true"})
    assert "playlistItems.list" in youtube.calls[calls:]


async def test_failed_calls_are_recorded_and_the_error_is_passed_on(client, google, youtube):
    await sign_in_active(client, google, "fail@example.com", "sub-fail")
    before = (await client.get("/api/quota")).json()["used"]
    youtube.fail_with = (403, "quotaExceeded")

    status = await _load_likes(client, refresh=True)
    assert status["state"] == "error"
    assert status["error"] == {"status": 403, "reason": "quotaExceeded", "message": "quotaExceeded"}
    assert (await client.get("/api/likes")).status_code == 409

    assert (await client.get("/api/quota")).json()["used"] == before + 1
    last = (await _usage_rows())[-1]
    assert (last.method, last.units, last.success) == ("playlistItems.list", 1, False)


async def test_quota_status(client, google, youtube):
    await sign_in_active(client, google, "quota@example.com", "sub-quota")
    quota = (await client.get("/api/quota")).json()
    assert quota["limit"] == 10_000
    assert quota["remaining"] == quota["limit"] - quota["used"]
    assert 0 < quota["resetsInSeconds"] <= 25 * 60 * 60  # 25 h on the day clocks fall back
    assert quota["resetsAt"].endswith(("Z", "+00:00"))


async def test_read_apis_need_an_active_user(client, google, youtube):
    for path in ("/api/likes", "/api/likes/status", "/api/playlists", "/api/playlists/PL1/items", "/api/quota"):
        assert (await client.get(path)).status_code == 401
    assert (await client.post("/api/likes/load")).status_code == 401

    await sign_in_active(client, google, "blocked@example.com", "sub-blocked")
    await set_status("blocked@example.com", "disable")
    for path in ("/api/likes", "/api/likes/status", "/api/playlists", "/api/playlists/PL1/items", "/api/quota"):
        response = await client.get(path)
        assert (response.status_code, response.json()["reason"]) == (403, "accessDenied")
    assert (await client.post("/api/likes/load")).status_code == 403


@pytest.mark.parametrize(
    ("iso", "seconds"),
    [("PT4M13S", 253), ("PT1H", 3600), ("PT45S", 45), ("P1DT2H3M4S", 93784), ("P0D", 0), ("", None), (None, None)],
)
def test_duration_seconds(iso, seconds):
    assert duration_seconds(iso) == seconds
