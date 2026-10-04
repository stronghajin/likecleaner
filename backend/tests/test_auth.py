"""Sign-in flow, /api/me, the active-user gate and the admin command, with a fake Google (respx)."""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from fastapi import APIRouter

from app.api.deps import ActiveUser
from app.clients.google_oauth_client import AUTH_URL, TOKEN_URL, USERINFO_URL, YOUTUBE_SCOPE
from app.core.db import SessionFactory
from app.core.errors import AppError
from app.core.security import decrypt_secret
from app.main import app
from app.repositories import token_repository, user_repository
from app.services import auth_service
from scripts import users as users_cli

BASIC = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"

# A route behind the active-user gate, standing in for the YouTube APIs that come in P2-4.
_gate = APIRouter()


@_gate.get("/api/test/active-only")
async def _active_only(user: ActiveUser) -> dict:
    return {"email": user.email}


app.include_router(_gate)


class FakeGoogle:
    """Token endpoint: code "c1" = step 1, "c2" = step 2. Userinfo answers for `self.sub` / `self.email`."""

    def __init__(self, email: str, sub: str) -> None:
        self.email, self.sub = email, sub
        self.step2_scope = f"{BASIC} {YOUTUBE_SCOPE}"
        self.refresh_error: str | None = None

    def token(self, request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode())
        if form["grant_type"] == ["refresh_token"]:
            if self.refresh_error:
                return httpx.Response(400, json={"error": self.refresh_error})
            return httpx.Response(200, json={"access_token": "fresh", "expires_in": 3599, "scope": self.step2_scope})
        if form["code"] == ["c1"]:
            return httpx.Response(200, json={"access_token": "a1", "expires_in": 3599, "scope": BASIC})
        return httpx.Response(
            200,
            json={"access_token": "a2", "expires_in": 3599, "scope": self.step2_scope, "refresh_token": "the-refresh"},
        )

    def userinfo(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"sub": self.sub, "email": self.email, "name": "Hajin", "picture": "https://pic"})


@pytest.fixture
def google():
    with respx.mock(assert_all_called=False) as mock:
        fake = FakeGoogle("me@example.com", "sub-me")
        mock.post(TOKEN_URL).mock(side_effect=fake.token)
        mock.get(USERINFO_URL).mock(side_effect=fake.userinfo)
        yield fake


def _state_of(location: str) -> str:
    return parse_qs(urlparse(location).query)["state"][0]


async def _start(client: httpx.AsyncClient) -> str:
    response = await client.get("/api/auth/google/login")
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(AUTH_URL)
    query = parse_qs(urlparse(location).query)
    assert query["prompt"] == ["select_account"]
    assert query["redirect_uri"] == ["http://localhost:5173/api/auth/google/callback"]
    return _state_of(location)


async def _callback(client: httpx.AsyncClient, **params: str) -> httpx.Response:
    response = await client.get("/api/auth/google/callback", params=params)
    assert response.status_code == 302
    return response


async def _register(email: str) -> None:
    assert await users_cli.run("add", email) == 0


async def _set(email: str, command: str) -> None:
    assert await users_cli.run(command, email) == 0


# --- not registered / disabled -------------------------------------------------


async def test_unregistered_email_sees_access_denied_with_its_email(client, google):
    google.email = "stranger@example.com"
    state = await _start(client)
    response = await _callback(client, code="c1", state=state)
    assert response.headers["location"] == "/"

    me = await client.get("/api/me")
    assert me.status_code == 200
    assert me.json() == {
        "id": "",
        "email": "stranger@example.com",
        "name": "Hajin",
        "pictureUrl": "https://pic",
        "status": "not_registered",
    }
    blocked = await client.get("/api/test/active-only")
    assert (blocked.status_code, blocked.json()["reason"]) == (401, "notSignedIn")


async def test_disabled_user_is_denied_at_sign_in(client, google):
    google.email = "off@example.com"
    await _register("off@example.com")
    await _set("off@example.com", "disable")
    response = await _callback(client, code="c1", state=await _start(client))
    assert response.headers["location"] == "/"
    assert (await client.get("/api/me")).json()["status"] == "disabled"


async def test_denied_user_registered_later_is_asked_to_sign_in_again(client, google):
    google.email = "later@example.com"
    await _callback(client, code="c1", state=await _start(client))
    await _register("later@example.com")
    assert (await client.get("/api/me")).status_code == 401


# --- active ----------------------------------------------------------------------


async def test_first_sign_in_asks_for_youtube_then_saves_an_encrypted_token(client, google):
    google.email, google.sub = "First@Example.com", "sub-first"
    await _register("first@example.com")

    step1 = await _callback(client, code="c1", state=await _start(client))
    step2_url = step1.headers["location"]
    query = parse_qs(urlparse(step2_url).query)
    assert query["scope"] == [YOUTUBE_SCOPE]
    assert query["access_type"] == ["offline"]
    assert query["login_hint"] == ["first@example.com"]
    # Not signed in until step 2 finishes.
    assert (await client.get("/api/me")).status_code == 401

    # /api/me cleared the session above, so start again from step 1.
    step1 = await _callback(client, code="c1", state=await _start(client))
    done = await _callback(client, code="c2", state=_state_of(step1.headers["location"]))
    assert done.headers["location"] == "/"

    me = (await client.get("/api/me")).json()
    assert (me["email"], me["name"], me["status"]) == ("first@example.com", "Hajin", "active")
    assert (await client.get("/api/test/active-only")).json() == {"email": "first@example.com"}

    async with SessionFactory() as db:
        user = await user_repository.get_by_email(db, "first@example.com")
        assert user.google_sub == "sub-first"
        saved = await token_repository.get(db, user.id)
    assert saved.refresh_token != "the-refresh"
    assert decrypt_secret(saved.refresh_token) == "the-refresh"
    assert YOUTUBE_SCOPE in saved.scopes
    # The cookie never carries tokens.
    assert "the-refresh" not in client.cookies.get("lc_session", "")


async def test_second_sign_in_skips_the_youtube_step(client, google):
    google.email, google.sub = "again@example.com", "sub-again"
    await _register("again@example.com")
    step1 = await _callback(client, code="c1", state=await _start(client))
    await _callback(client, code="c2", state=_state_of(step1.headers["location"]))
    assert (await client.post("/api/auth/logout")).status_code == 204
    assert (await client.get("/api/me")).status_code == 401

    response = await _callback(client, code="c1", state=await _start(client))
    assert response.headers["location"] == "/"
    assert (await client.get("/api/me")).json()["status"] == "active"


async def test_disabling_blocks_a_signed_in_user_right_away(client, google):
    google.email, google.sub = "now@example.com", "sub-now"
    await _register("now@example.com")
    step1 = await _callback(client, code="c1", state=await _start(client))
    await _callback(client, code="c2", state=_state_of(step1.headers["location"]))

    await _set("now@example.com", "disable")
    assert (await client.get("/api/me")).json()["status"] == "disabled"
    blocked = await client.get("/api/test/active-only")
    assert (blocked.status_code, blocked.json()["reason"]) == (403, "accessDenied")

    await _set("now@example.com", "enable")
    assert (await client.get("/api/test/active-only")).status_code == 200


async def test_youtube_permission_unticked_goes_back_with_a_message(client, google):
    google.email, google.sub = "untick@example.com", "sub-untick"
    google.step2_scope = BASIC  # YouTube box unticked on Google's screen
    await _register("untick@example.com")
    step1 = await _callback(client, code="c1", state=await _start(client))
    response = await _callback(client, code="c2", state=_state_of(step1.headers["location"]))
    assert response.headers["location"] == "/?signin_error=youtube_permission"
    assert (await client.get("/api/me")).status_code == 401


async def test_youtube_step_cancelled_goes_back_with_a_message(client, google):
    google.email, google.sub = "cancel@example.com", "sub-cancel"
    await _register("cancel@example.com")
    step1 = await _callback(client, code="c1", state=await _start(client))
    response = await _callback(client, error="access_denied", state=_state_of(step1.headers["location"]))
    assert response.headers["location"] == "/?signin_error=youtube_permission"


async def test_wrong_state_is_ignored(client, google):
    google.email = "state@example.com"
    await _register("state@example.com")
    await _start(client)
    response = await _callback(client, code="c1", state="not-the-right-state")
    assert response.headers["location"] == "/"
    assert (await client.get("/api/me")).status_code == 401


async def test_logout_ends_the_session(client, google):
    google.email = "bye@example.com"
    await _callback(client, code="c1", state=await _start(client))
    assert (await client.get("/api/me")).status_code == 200
    await client.post("/api/auth/logout")
    assert (await client.get("/api/me")).status_code == 401


# --- access token (used from P2-4) -----------------------------------------------


async def test_removed_google_access_asks_for_youtube_again(client, google):
    google.email, google.sub = "revoked@example.com", "sub-revoked"
    await _register("revoked@example.com")
    step1 = await _callback(client, code="c1", state=await _start(client))
    await _callback(client, code="c2", state=_state_of(step1.headers["location"]))

    async with SessionFactory() as db, httpx.AsyncClient() as http:
        user = await user_repository.get_by_email(db, "revoked@example.com")
        tokens = await auth_service.get_access_token(db, http, user.id)
        assert tokens.access_token.get_secret_value() == "fresh"

        google.refresh_error = "invalid_grant"
        with pytest.raises(AppError) as caught:
            await auth_service.get_access_token(db, http, user.id)
        assert caught.value.reason == "youtubeReauthRequired"
        assert await token_repository.get(db, user.id) is None

    # The next sign-in goes through the YouTube step again.
    step1 = await _callback(client, code="c1", state=await _start(client))
    assert step1.headers["location"].startswith(AUTH_URL)


# --- admin command ------------------------------------------------------------------


async def test_admin_command(capsys):
    assert await users_cli.run("add", "  Cmd@Example.com ") == 0
    assert "Added cmd@example.com (active)" in capsys.readouterr().out

    assert await users_cli.run("add", "cmd@example.com") == 1
    assert "already registered" in capsys.readouterr().err

    assert await users_cli.run("add", "not-an-email") == 1
    assert "not an email address" in capsys.readouterr().err

    assert await users_cli.run("disable", "nobody@example.com") == 1
    assert "not registered" in capsys.readouterr().err

    assert await users_cli.run("disable", "cmd@example.com") == 0
    assert "now disabled" in capsys.readouterr().out
    assert await users_cli.run("list", None) == 0
    line = next(l for l in capsys.readouterr().out.splitlines() if l.startswith("cmd@example.com"))
    assert "disabled" in line and "never signed in" in line and "YouTube not connected" in line
