"""A fake Google sign-in shared by the tests (respx). Code "c1" = step 1, "c2" = step 2."""

from urllib.parse import parse_qs, urlparse

import httpx

from app.clients.google_oauth_client import AUTH_URL, YOUTUBE_SCOPE
from scripts import users as users_cli

BASIC = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"


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


def state_of(location: str) -> str:
    return parse_qs(urlparse(location).query)["state"][0]


async def start(client: httpx.AsyncClient) -> str:
    response = await client.get("/api/auth/google/login")
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(AUTH_URL)
    query = parse_qs(urlparse(location).query)
    assert query["prompt"] == ["select_account"]
    assert query["redirect_uri"] == ["http://localhost:5173/api/auth/google/callback"]
    return state_of(location)


async def callback(client: httpx.AsyncClient, **params: str) -> httpx.Response:
    response = await client.get("/api/auth/google/callback", params=params)
    assert response.status_code == 302
    return response


async def register(email: str) -> None:
    assert await users_cli.run("add", email) == 0


async def set_status(email: str, command: str) -> None:
    assert await users_cli.run(command, email) == 0


async def sign_in_active(client: httpx.AsyncClient, google: FakeGoogle, email: str, sub: str) -> None:
    """Registers `email` and signs in through both steps."""
    google.email, google.sub = email, sub
    await register(email)
    step1 = await callback(client, code="c1", state=await start(client))
    await callback(client, code="c2", state=state_of(step1.headers["location"]))
