"""Clients against fake Google/YouTube responses (respx). Nothing here reaches the internet."""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from app.clients import mail_client as mail_module
from app.clients.errors import ExternalApiError
from app.clients.google_oauth_client import TOKEN_URL, USERINFO_URL, YOUTUBE_SCOPE, GoogleOAuthClient
from app.clients.mail_client import MailClient
from app.clients.youtube_client import API_URL, YouTubeClient
from app.core.security import decrypt_secret, encrypt_secret
from app.schemas.mail import MailMessage

REDIRECT = "http://localhost:5173/api/auth/google/callback"


@pytest.fixture
async def http():
    async with httpx.AsyncClient() as c:
        yield c


# --- Google OAuth ---------------------------------------------------------


def test_step_two_url_asks_for_offline_access_and_keeps_earlier_scopes(http):
    url = GoogleOAuthClient(http).authorization_url(
        scopes=[YOUTUBE_SCOPE], redirect_uri=REDIRECT, state="s1", offline=True, login_hint="a@b.com"
    )
    query = parse_qs(urlparse(url).query)
    assert query["scope"] == [YOUTUBE_SCOPE]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["include_granted_scopes"] == ["true"]
    assert query["login_hint"] == ["a@b.com"]
    assert query["state"] == ["s1"]


def test_step_one_url_does_not_ask_for_offline_access(http):
    url = GoogleOAuthClient(http).authorization_url(scopes=["openid"], redirect_uri=REDIRECT, state="s")
    query = parse_qs(urlparse(url).query)
    assert "access_type" not in query
    assert "prompt" not in query


@respx.mock
async def test_exchange_code_returns_tokens(http):
    respx.post(TOKEN_URL).respond(
        json={"access_token": "at", "expires_in": 3599, "scope": f"openid {YOUTUBE_SCOPE}", "refresh_token": "rt"}
    )
    tokens = await GoogleOAuthClient(http).exchange_code("code", REDIRECT)
    assert tokens.access_token.get_secret_value() == "at"
    assert tokens.refresh_token.get_secret_value() == "rt"
    assert tokens.scopes == ["openid", YOUTUBE_SCOPE]


@respx.mock
async def test_refresh_after_access_was_removed_raises_invalid_grant(http):
    respx.post(TOKEN_URL).respond(400, json={"error": "invalid_grant", "error_description": "Token has been expired or revoked."})
    with pytest.raises(ExternalApiError) as caught:
        await GoogleOAuthClient(http).refresh("rt")
    assert caught.value.error.status == 400
    assert caught.value.error.reason == "invalid_grant"


@respx.mock
async def test_profile(http):
    respx.get(USERINFO_URL).respond(json={"sub": "123", "email": "a@b.com", "name": "A", "picture": "https://p"})
    profile = await GoogleOAuthClient(http).get_profile("at")
    assert (profile.google_sub, profile.email, profile.name, profile.picture_url) == ("123", "a@b.com", "A", "https://p")


# --- YouTube --------------------------------------------------------------


def _youtube_error(status: int, reason: str) -> dict:
    return {"error": {"code": status, "message": f"{reason} happened", "errors": [{"reason": reason}]}}


@respx.mock
async def test_liked_videos_page(http):
    route = respx.get(f"{API_URL}/videos").respond(
        json={
            "items": [
                {
                    "id": "v1",
                    "snippet": {
                        "title": "Song",
                        "channelId": "c1",
                        "channelTitle": "Chan",
                        "categoryId": "10",
                        "publishedAt": "2020-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "https://i/1.jpg"}},
                    },
                    "contentDetails": {"duration": "PT3M5S"},
                }
            ],
            "nextPageToken": "p2",
            "pageInfo": {"totalResults": 120},
        }
    )
    page = await YouTubeClient(http).list_liked_videos("at", page_token="p1")
    params = route.calls.last.request.url.params
    assert params["myRating"] == "like"
    assert params["pageToken"] == "p1"
    assert route.calls.last.request.headers["Authorization"] == "Bearer at"
    assert page.next_page_token == "p2"
    assert page.total_results == 120
    video = page.items[0]
    assert (video.id, video.category_id, video.duration, video.thumbnail_url) == ("v1", "10", "PT3M5S", "https://i/1.jpg")


@respx.mock
async def test_first_page_sends_no_page_token(http):
    route = respx.get(f"{API_URL}/videos").respond(json={"items": []})
    await YouTubeClient(http).list_liked_videos("at")
    assert "pageToken" not in route.calls.last.request.url.params


@respx.mock
async def test_playlist_item_of_deleted_video_has_no_channel(http):
    respx.get(f"{API_URL}/playlistItems").respond(
        json={
            "items": [
                {
                    "id": "pi1",
                    "snippet": {"title": "Deleted video", "position": 3, "resourceId": {"videoId": "v9"}},
                    "contentDetails": {"videoId": "v9"},
                    "status": {"privacyStatus": "privacyStatusUnspecified"},
                }
            ]
        }
    )
    page = await YouTubeClient(http).list_playlist_items("at", "PL1")
    item = page.items[0]
    assert (item.playlist_item_id, item.position, item.video_id, item.title) == ("pi1", 3, "v9", "Deleted video")
    assert item.video_owner_channel_title is None
    assert item.thumbnail_url is None


@respx.mock
async def test_insert_at_front_sends_position_zero(http):
    route = respx.post(f"{API_URL}/playlistItems").respond(
        json={"id": "pi2", "snippet": {"title": "Song", "position": 0, "resourceId": {"videoId": "v1"}}}
    )
    item = await YouTubeClient(http).insert_playlist_item("at", "PL1", "v1", position=0)
    body = route.calls.last.request.read()
    assert b'"position":0' in body.replace(b" ", b"")
    assert item.position == 0


@respx.mock
async def test_insert_without_position_leaves_it_out(http):
    route = respx.post(f"{API_URL}/playlistItems").respond(
        json={"id": "pi3", "snippet": {"title": "Song", "position": 7, "resourceId": {"videoId": "v1"}}}
    )
    await YouTubeClient(http).insert_playlist_item("at", "PL1", "v1")
    assert b"position" not in route.calls.last.request.read()


@respx.mock
async def test_manual_sort_required_comes_back_as_a_reason(http):
    respx.post(f"{API_URL}/playlistItems").respond(400, json=_youtube_error(400, "manualSortRequired"))
    with pytest.raises(ExternalApiError) as caught:
        await YouTubeClient(http).insert_playlist_item("at", "PL1", "v1", position=0)
    assert caught.value.error.status == 400
    assert caught.value.error.reason == "manualSortRequired"
    assert caught.value.error.message == "manualSortRequired happened"


@respx.mock
async def test_quota_exceeded_on_delete(http):
    respx.delete(f"{API_URL}/playlistItems").respond(403, json=_youtube_error(403, "quotaExceeded"))
    with pytest.raises(ExternalApiError) as caught:
        await YouTubeClient(http).delete_playlist_item("at", "pi1")
    assert caught.value.error.reason == "quotaExceeded"


@respx.mock
async def test_error_without_json_body_still_has_the_common_shape(http):
    respx.post(f"{API_URL}/videos/rate").respond(429, text="Too Many Requests")
    with pytest.raises(ExternalApiError) as caught:
        await YouTubeClient(http).rate_video("at", "v1", "none")
    assert (caught.value.error.status, caught.value.error.reason) == (429, "youtubeError")


@respx.mock
async def test_categories_are_asked_in_english(http):
    route = respx.get(f"{API_URL}/videoCategories").respond(json={"items": [{"id": "10", "snippet": {"title": "Music"}}]})
    categories = await YouTubeClient(http).list_video_categories("at", ["10"])
    params = route.calls.last.request.url.params
    assert (params["hl"], params["regionCode"]) == ("en", "US")
    assert categories[0].title == "Music"


# --- Mail and encryption --------------------------------------------------


async def test_mail_uses_gmail_with_starttls(monkeypatch):
    sent = {}

    async def fake_send(message, **kwargs):
        sent["message"] = message
        sent.update(kwargs)

    monkeypatch.setattr(mail_module.aiosmtplib, "send", fake_send)
    await MailClient().send(MailMessage(to="a@b.com", subject="Hi", body="Body"))
    assert sent["hostname"] == "smtp.gmail.com"
    assert sent["port"] == 587
    assert sent["start_tls"] is True
    assert sent["message"]["To"] == "a@b.com"
    assert sent["message"]["Subject"] == "Hi"


def test_encrypted_secret_round_trips_and_is_not_plain():
    sealed = encrypt_secret("refresh-token-value")
    assert "refresh-token-value" not in sealed
    assert decrypt_secret(sealed) == "refresh-token-value"
