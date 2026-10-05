"""Jobs (SPEC.md 6-5 to 6-7, 7-2, 8; DECISIONS.md 10, 28, 30, 55, 63) against a fake YouTube that keeps state."""

import json
from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select

from app.clients.youtube_client import API_URL
from app.core.config import get_settings
from app.core.db import SessionFactory
from app.core.time import now_utc, pacific_day
from app.models.job import Job
from app.models.quota_usage import QuotaUsage
from app.repositories import job_repository
from app.schemas.job import JobCreate, JobItemCreate
from app.services import job_processor, job_service
from app.workers import job_worker
from tests.fake_google import sign_in_active

LL_PAGE_SIZE = 50


def _error(status: int, reason: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": status, "message": f"{reason} message", "errors": [{"reason": reason}]}})


class FakeYouTube:
    """Likes v1..v5, playlist PL1 (has v1) and an auto-sorted PL2 (empty)."""

    def __init__(self) -> None:
        self.liked = ["v1", "v2", "v3", "v4", "v5"]
        self.playlists: dict[str, list[tuple[str, str]]] = {"PL1": [("e-v1", "v1")], "PL2": []}
        self.auto_sorted = {"PL2"}
        self.calls: list[str] = []
        # method -> errors to answer with, one per call, before behaving normally
        self.errors: dict[str, list[tuple[int, str]]] = {}
        self._seq = 0

    def _scripted(self, method: str) -> httpx.Response | None:
        queue = self.errors.get(method)
        if queue:
            return _error(*queue.pop(0))
        return None

    def _video(self, video_id: str) -> dict:
        return {
            "id": video_id,
            "snippet": {"title": f"Title {video_id}", "channelTitle": "Chan", "categoryId": "10",
                        "publishedAt": "2020-01-01T00:00:00Z", "thumbnails": {"default": {"url": "https://t"}}},
            "contentDetails": {"duration": "PT1M"},
            "status": {"privacyStatus": "public"},
        }

    def _item(self, entry_id: str, video_id: str, position: int) -> dict:
        return {
            "id": entry_id,
            "snippet": {"title": f"Title {video_id}", "position": position, "resourceId": {"videoId": video_id},
                        "videoOwnerChannelTitle": "Chan", "thumbnails": {"default": {"url": "https://t"}}},
            "contentDetails": {"videoId": video_id},
            "status": {"privacyStatus": "public"},
        }

    def videos(self, request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if params.get("myRating") == "like":
            return httpx.Response(200, json={"items": [], "pageInfo": {"totalResults": len(self.liked)}})
        self.calls.append("videos.list")
        return httpx.Response(200, json={"items": [self._video(i) for i in params["id"].split(",")]})

    def categories(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [{"id": "10", "snippet": {"title": "Music"}}]})

    def playlists_list(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [
            {"id": pid, "snippet": {"title": f"Title {pid}"}, "contentDetails": {"itemCount": len(items)}}
            for pid, items in self.playlists.items()
        ]})

    def playlist_items(self, request: httpx.Request) -> httpx.Response:
        playlist_id = request.url.params["playlistId"]
        self.calls.append(f"playlistItems.list({playlist_id})")
        if error := self._scripted("playlistItems.list"):
            return error
        if playlist_id == "LL":
            entries = [(f"l-{v}", v) for v in self.liked]
        else:
            entries = self.playlists[playlist_id]
        return httpx.Response(200, json={"items": [self._item(e, v, n) for n, (e, v) in enumerate(entries)]})

    def insert(self, request: httpx.Request) -> httpx.Response:
        snippet = json.loads(request.content)["snippet"]
        playlist_id, video_id = snippet["playlistId"], snippet["resourceId"]["videoId"]
        at_top = "position" in snippet
        self.calls.append(f"insert({video_id},{'top' if at_top else 'end'})")
        if error := self._scripted("playlistItems.insert"):
            return error
        if at_top and playlist_id in self.auto_sorted:
            return _error(400, "manualSortRequired")
        self._seq += 1
        entry = (f"new-{self._seq}", video_id)
        items = self.playlists[playlist_id]
        items.insert(0, entry) if at_top else items.append(entry)
        return httpx.Response(200, json=self._item(entry[0], video_id, items.index(entry)))

    def delete(self, request: httpx.Request) -> httpx.Response:
        entry_id = request.url.params["id"]
        self.calls.append(f"delete({entry_id})")
        if error := self._scripted("playlistItems.delete"):
            return error
        for items in self.playlists.values():
            for entry in items:
                if entry[0] == entry_id:
                    items.remove(entry)
                    return httpx.Response(204)
        return _error(404, "playlistItemNotFound")

    def rate(self, request: httpx.Request) -> httpx.Response:
        video_id = request.url.params["id"]
        self.calls.append(f"rate({video_id})")
        if error := self._scripted("videos.rate"):
            return error
        if video_id in self.liked:
            self.liked.remove(video_id)
        return httpx.Response(204)


@pytest.fixture
def youtube(google, monkeypatch):
    fake = FakeYouTube()
    google.respx.get(f"{API_URL}/videos").mock(side_effect=fake.videos)
    google.respx.get(f"{API_URL}/videoCategories").mock(side_effect=fake.categories)
    google.respx.get(f"{API_URL}/playlists").mock(side_effect=fake.playlists_list)
    google.respx.get(f"{API_URL}/playlistItems").mock(side_effect=fake.playlist_items)
    google.respx.post(f"{API_URL}/playlistItems").mock(side_effect=fake.insert)
    google.respx.delete(f"{API_URL}/playlistItems").mock(side_effect=fake.delete)
    google.respx.post(f"{API_URL}/videos/rate").mock(side_effect=fake.rate)
    monkeypatch.setattr(job_processor, "RATE_LIMIT_WAITS_S", (0, 0, 0))
    job_processor._auto_sorted.clear()
    return fake


_users = iter(range(1000))


async def _signed_in(client: httpx.AsyncClient, google) -> None:
    """A fresh user each time (the DB is shared by the whole test run), with likes and PL1 loaded."""
    n = next(_users)
    await sign_in_active(client, google, f"jobs{n}@example.com", f"sub-jobs-{n}")
    status = (await client.post("/api/likes/load")).json()
    while status["state"] == "loading":
        status = (await client.get("/api/likes/status")).json()
    assert status["state"] == "ready"
    assert (await client.get("/api/playlists")).status_code == 200
    assert (await client.get("/api/playlists/PL1/items")).status_code == 200


async def _run(client: httpx.AsyncClient, body: dict) -> dict:
    response = await client.post("/api/jobs", json=body)
    assert response.status_code == 200, response.json()
    assert response.json()["status"] == "running"
    await job_worker.wait_all()
    return (await client.get("/api/jobs/latest")).json()


def _statuses(job: dict) -> list[str]:
    return [i["status"] for i in job["items"]]


async def _liked_ids(client: httpx.AsyncClient) -> list[str]:
    return [v["id"] for v in (await client.get("/api/likes")).json()["videos"]]


async def _entries(client: httpx.AsyncClient, playlist_id: str) -> list[str]:
    return [i["videoId"] for i in (await client.get(f"/api/playlists/{playlist_id}/items")).json()]


async def test_remove_like_updates_youtube_and_server_memory(client, google, youtube):
    await _signed_in(client, google)
    job = await _run(client, {"type": "remove_like", "videoIds": ["v2", "v3"]})

    assert job["status"] == "completed"
    assert job["finishedAt"]
    assert [(i["videoId"], i["videoTitle"], i["status"]) for i in job["items"]] == [
        ("v2", "Title v2", "success"),
        ("v3", "Title v3", "success"),
    ]
    assert "fatalError" not in job and "rateLimit" not in job
    assert youtube.liked == ["v1", "v4", "v5"]
    # DECISIONS.md 55: the list in memory follows the result right away, without asking YouTube.
    calls = len(youtube.calls)
    assert await _liked_ids(client) == ["v1", "v4", "v5"]
    assert (await client.get("/api/likes")).json()["totalLiked"] == 3
    assert len(youtube.calls) == calls


async def test_move_adds_at_the_top_and_skips_what_is_there(client, google, youtube):
    await _signed_in(client, google)
    job = await _run(client, {"type": "move", "videoIds": ["v1", "v2"], "targetPlaylistId": "PL1"})

    assert job["targetPlaylistTitle"] == "Title PL1"
    assert _statuses(job) == ["skipped", "success"]
    assert youtube.calls[-2:] == ["videos.list", "insert(v2,top)"]  # fresh duplicate check, then add
    assert [v for _, v in youtube.playlists["PL1"]] == ["v2", "v1"]
    assert await _liked_ids(client) == ["v1", "v2", "v3", "v4", "v5"]  # Move Only keeps likes
    calls = len(youtube.calls)
    assert await _entries(client, "PL1") == ["v2", "v1"]  # from memory, already updated
    assert len(youtube.calls) == calls
    playlists = {p["id"]: p["itemCount"] for p in (await client.get("/api/playlists")).json()}
    assert playlists["PL1"] == 2


async def test_auto_sorted_playlist_gets_the_video_without_a_position(client, google, youtube):
    await _signed_in(client, google)
    job = await _run(client, {"type": "move", "videoIds": ["v2", "v3"], "targetPlaylistId": "PL2"})

    assert _statuses(job) == ["success", "success"]
    # Refused once at the top, then never tried at the top again (DECISIONS.md 30).
    assert [c for c in youtube.calls if c.startswith("insert")] == ["insert(v2,top)", "insert(v2,end)", "insert(v3,end)"]
    assert [v for _, v in youtube.playlists["PL2"]] == ["v2", "v3"]


async def test_move_and_unlike_only_unlikes_videos_already_there(client, google, youtube):
    await _signed_in(client, google)
    job = await _run(client, {"type": "move_and_unlike", "videoIds": ["v1", "v2"], "targetPlaylistId": "PL1"})

    assert _statuses(job) == ["success", "success"]
    assert [c for c in youtube.calls if c.startswith(("insert", "rate"))] == ["rate(v1)", "insert(v2,top)", "rate(v2)"]
    assert youtube.liked == ["v3", "v4", "v5"]
    assert [v for _, v in youtube.playlists["PL1"]] == ["v2", "v1"]


async def test_failed_unlike_is_rolled_back(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(500, "backendError")]
    job = await _run(client, {"type": "move_and_unlike", "videoIds": ["v2", "v3"], "targetPlaylistId": "PL1"})

    first, second = job["items"]
    assert first["status"] == "failed"
    assert first["error"] == {"status": 500, "reason": "backendError", "message": "backendError message"}
    assert second["status"] == "success"
    # v2 was added, its like could not be removed, so it was taken out again (SPEC.md 6-7).
    assert "delete(new-1)" in youtube.calls
    assert [v for _, v in youtube.playlists["PL1"]] == ["v3", "v1"]
    assert "v2" in youtube.liked
    assert await _entries(client, "PL1") == ["v3", "v1"]


async def test_rollback_that_fails_is_marked_for_the_user(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(500, "backendError")]
    youtube.errors["playlistItems.delete"] = [(500, "backendError")]
    job = await _run(client, {"type": "move_and_unlike", "videoIds": ["v2", "v3"], "targetPlaylistId": "PL1"})

    assert _statuses(job) == ["rollback_failed", "success"]
    assert job["status"] == "completed"
    # Retry Failed leaves rollback_failed out (DECISIONS.md 10).
    retry = await client.post(f"/api/jobs/{job['id']}/retry")
    assert retry.json()["reason"] == "nothingToRetry"


async def test_rate_limit_retries_the_same_call(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["playlistItems.insert"] = [(429, "rateLimitExceeded"), (429, "rateLimitExceeded")]
    job = await _run(client, {"type": "move", "videoIds": ["v2"], "targetPlaylistId": "PL1"})

    assert _statuses(job) == ["success"]
    assert "rateLimit" not in job
    assert [c for c in youtube.calls if c.startswith("insert")] == ["insert(v2,top)"] * 3
    assert [v for _, v in youtube.playlists["PL1"]] == ["v2", "v1"]  # added once


async def test_rate_limit_that_does_not_stop_ends_the_job(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(429, "rateLimitExceeded")] * 4
    job = await _run(client, {"type": "remove_like", "videoIds": ["v2", "v3"]})

    assert job["status"] == "stopped"
    assert job["fatalError"]["reason"] == "rateLimitExceeded"
    assert _statuses(job) == ["not_processed", "not_processed"]
    assert youtube.calls.count("rate(v2)") == 4  # first try + 3 retries
    assert "rate(v3)" not in youtube.calls

    # Retry Failed picks up both (DECISIONS.md 28).
    response = await client.post(f"/api/jobs/{job['id']}/retry")
    assert [i["videoId"] for i in response.json()["items"]] == ["v2", "v3"]
    await job_worker.wait_all()
    assert _statuses((await client.get("/api/jobs/latest")).json()) == ["success", "success"]


async def test_quota_exceeded_stops_and_leaves_the_rest(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(500, "backendError"), (403, "quotaExceeded")]
    job = await _run(client, {"type": "remove_like", "videoIds": ["v2", "v3", "v4"]})

    assert job["status"] == "stopped"
    assert job["fatalError"]["reason"] == "quotaExceeded"
    assert _statuses(job) == ["failed", "not_processed", "not_processed"]
    assert "rate(v4)" not in youtube.calls


async def test_quota_exceeded_on_the_unlike_rolls_back_before_stopping(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(403, "quotaExceeded")]
    job = await _run(client, {"type": "move_and_unlike", "videoIds": ["v2", "v3"], "targetPlaylistId": "PL1"})

    assert job["status"] == "stopped"
    assert _statuses(job) == ["failed", "not_processed"]
    assert [v for _, v in youtube.playlists["PL1"]] == ["v1"]  # nothing left half done


async def test_playlist_remove(client, google, youtube):
    await _signed_in(client, google)
    youtube.playlists["PL1"] += [("e-v2", "v2"), ("e-v3", "v3")]
    await client.get("/api/playlists/PL1/items", params={"refresh": "true"})
    youtube.errors["playlistItems.delete"] = [(404, "playlistItemNotFound")]
    job = await _run(client, {"type": "playlist_remove", "playlistId": "PL1", "playlistItemIds": ["e-v2", "e-v3"]})

    assert [(i["playlistItemId"], i["status"]) for i in job["items"]] == [("e-v2", "failed"), ("e-v3", "success")]
    assert await _entries(client, "PL1") == ["v1", "v2"]

    response = await client.post(f"/api/jobs/{job['id']}/retry")
    assert [i["playlistItemId"] for i in response.json()["items"]] == ["e-v2"]
    await job_worker.wait_all()
    assert await _entries(client, "PL1") == ["v1"]


async def test_one_job_at_a_time_and_request_checks(client, google, youtube):
    await _signed_in(client, google)
    youtube.errors["videos.rate"] = [(429, "rateLimitExceeded")]
    first = await client.post("/api/jobs", json={"type": "remove_like", "videoIds": ["v2"]})
    second = await client.post("/api/jobs", json={"type": "remove_like", "videoIds": ["v3"]})
    assert first.status_code == 200
    assert second.status_code == 409 and second.json()["reason"] == "jobAlreadyRunning"
    await job_worker.wait_all()

    assert (await client.post("/api/jobs", json={"type": "remove_like", "videoIds": []})).json()["reason"] == "noItems"
    too_many = [f"x{n}" for n in range(101)]
    assert (await client.post("/api/jobs", json={"type": "remove_like", "videoIds": too_many})).json()["reason"] == "tooManyItems"
    missing = await client.post("/api/jobs", json={"type": "move", "videoIds": ["v2"], "targetPlaylistId": "nope"})
    assert missing.json()["reason"] == "playlistNotFound"


async def test_server_checks_the_quota_too(client, google, youtube, monkeypatch):
    await _signed_in(client, google)
    used = (await client.get("/api/quota")).json()["used"]
    monkeypatch.setattr(get_settings(), "daily_quota", used + 120)  # room for 2 unlikes, not 3
    response = await client.post("/api/jobs", json={"type": "remove_like", "videoIds": ["v2", "v3", "v4"]})
    assert response.status_code == 403
    assert response.json() == {
        "status": 403,
        "reason": "notEnoughQuota",
        "message": "Not enough quota. You can process up to 2 items today.",
    }


async def test_jobs_cut_off_by_a_restart_are_stopped(client, google, youtube):
    await _signed_in(client, google)
    me = (await client.get("/api/me")).json()
    async with SessionFactory() as db:
        job = await job_repository.create(
            db,
            JobCreate(
                id="restart-test",
                user_id=int(me["id"]),
                type="remove_like",
                items=[JobItemCreate(video_id="v2", video_title="Title v2")],
            ),
        )
        await job_service.stop_interrupted_jobs(db)  # what start-up does

    latest = (await client.get("/api/jobs/latest")).json()
    assert latest["id"] == job.id
    assert latest["status"] == "stopped"
    assert latest["fatalError"]["reason"] == "serverRestarted"
    assert _statuses(latest) == ["not_processed"]
    assert "rate(v2)" not in youtube.calls  # not resumed (DECISIONS.md 63)

    # Retry Failed picks the cut-off items up again (DECISIONS.md 10, 63).
    retry = await client.post(f"/api/jobs/{job.id}/retry")
    assert retry.status_code == 200
    assert [i["videoId"] for i in retry.json()["items"]] == ["v2"]
    await job_worker.wait_all()
    assert _statuses((await client.get("/api/jobs/latest")).json()) == ["success"]
    assert "v2" not in youtube.liked


async def test_old_jobs_and_usage_are_deleted_after_30_days(client, google, youtube):
    await _signed_in(client, google)
    me = (await client.get("/api/me")).json()
    old = now_utc() - timedelta(days=31)
    async with SessionFactory() as db:
        db.add(Job(id="old-job", user_id=int(me["id"]), type="remove_like", status="completed", created_at=old))
        db.add(QuotaUsage(date_pt=pacific_day() - timedelta(days=31), method="videos.rate", units=50, success=True))
        await db.commit()
        await job_service.delete_old_data(db)
        assert await db.get(Job, "old-job") is None
        old_usage = await db.scalar(
            select(QuotaUsage.id).where(QuotaUsage.date_pt < pacific_day() - timedelta(days=30))
        )
        assert old_usage is None


async def test_latest_job_is_null_before_any_job(client, google, youtube):
    n = next(_users)
    await sign_in_active(client, google, f"nojob{n}@example.com", f"sub-nojob-{n}")
    response = await client.get("/api/jobs/latest")
    assert response.status_code == 200
    assert response.json() is None
