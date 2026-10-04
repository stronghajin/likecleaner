"""Read APIs (likes, playlists, items, quota) against a fake YouTube (respx). Nothing reaches the internet."""

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
        if params.get("myRating") == "like":
            self.calls.append("videos.list(like)")
            if params.get("pageToken") == "p2":
                # v1 again: a like added mid-load shifted it onto the next page
                return httpx.Response(200, json={"items": [_video("v3", "20"), _video("v1")]})
            return httpx.Response(200, json={"items": [_video("v1"), _video("v2")], "nextPageToken": "p2"})
        self.calls.append(f"videos.list(id={params['id']})")
        return httpx.Response(200, json={"items": [_video(i) for i in params["id"].split(",") if i != "gone"]})

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


async def _usage_rows() -> list[QuotaUsage]:
    async with SessionFactory() as db:
        rows = await db.scalars(select(QuotaUsage).order_by(QuotaUsage.id))
        return list(rows)


async def test_liked_list_merges_pages_and_fills_categories(client, google, youtube):
    await sign_in_active(client, google, "likes@example.com", "sub-likes")
    quota_before = (await client.get("/api/quota")).json()["used"]

    response = await client.get("/api/likes")
    assert response.status_code == 200
    videos = response.json()
    assert [v["id"] for v in videos] == ["v1", "v2", "v3"]
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
    # 2 pages of videos.list + the category lists (names are remembered across users and tests)
    used = (await client.get("/api/quota")).json()["used"] - quota_before
    assert used == 2 + sum(c.startswith("videoCategories.list") for c in youtube.calls)


async def test_second_load_comes_from_memory_and_resync_reloads(client, google, youtube):
    await sign_in_active(client, google, "memory@example.com", "sub-memory")
    await client.get("/api/likes")
    calls = len(youtube.calls)

    assert len((await client.get("/api/likes")).json()) == 3
    assert len(youtube.calls) == calls  # no YouTube call, 0 units

    await client.get("/api/likes", params={"refresh": "true"})
    assert youtube.calls[calls:] == ["videos.list(like)", "videos.list(like)"]  # categories already known


async def test_sign_out_drops_the_lists_in_memory(client, google, youtube):
    await sign_in_active(client, google, "out@example.com", "sub-out")
    await client.get("/api/likes")
    await client.post("/api/auth/logout")

    # Sign in again (YouTube step is skipped now) and the list is loaded from YouTube again.
    await callback(client, code="c1", state=await start(client))
    calls = len(youtube.calls)
    await client.get("/api/likes")
    assert youtube.calls[calls:].count("videos.list(like)") == 2


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

    response = await client.get("/api/likes", params={"refresh": "true"})
    assert response.status_code == 403
    assert response.json() == {"status": 403, "reason": "quotaExceeded", "message": "quotaExceeded"}

    assert (await client.get("/api/quota")).json()["used"] == before + 1
    last = (await _usage_rows())[-1]
    assert (last.method, last.units, last.success) == ("videos.list", 1, False)


async def test_quota_status(client, google, youtube):
    await sign_in_active(client, google, "quota@example.com", "sub-quota")
    quota = (await client.get("/api/quota")).json()
    assert quota["limit"] == 10_000
    assert quota["remaining"] == quota["limit"] - quota["used"]
    assert 0 < quota["resetsInSeconds"] <= 25 * 60 * 60  # 25 h on the day clocks fall back
    assert quota["resetsAt"].endswith(("Z", "+00:00"))


async def test_read_apis_need_an_active_user(client, google, youtube):
    for path in ("/api/likes", "/api/playlists", "/api/playlists/PL1/items", "/api/quota"):
        assert (await client.get(path)).status_code == 401

    await sign_in_active(client, google, "blocked@example.com", "sub-blocked")
    await set_status("blocked@example.com", "disable")
    for path in ("/api/likes", "/api/playlists", "/api/playlists/PL1/items", "/api/quota"):
        response = await client.get(path)
        assert (response.status_code, response.json()["reason"]) == (403, "accessDenied")


@pytest.mark.parametrize(
    ("iso", "seconds"),
    [("PT4M13S", 253), ("PT1H", 3600), ("PT45S", 45), ("P1DT2H3M4S", 93784), ("P0D", 0), ("", None), (None, None)],
)
def test_duration_seconds(iso, seconds):
    assert duration_seconds(iso) == seconds
