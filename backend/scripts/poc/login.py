"""PoC 2: two-step Google sign-in (SPEC.md 3-2) and refresh token issue / refresh.

Run from backend/:  uv run python -m scripts.poc.login
A browser opens twice: first basic sign-in, then the YouTube permission.
"""

import asyncio
import secrets
import webbrowser
from urllib.parse import parse_qs, urlparse

import httpx

from app.clients.errors import ExternalApiError
from app.clients.google_oauth_client import BASIC_SCOPES, YOUTUBE_SCOPE, GoogleOAuthClient
from scripts.poc.common import REDIRECT_URI, save_refresh_token, save_results

CALLBACK_PATH = urlparse(REDIRECT_URI).path
PORT = urlparse(REDIRECT_URI).port
WAIT_SECONDS = 600

_DONE_PAGE = (
    "<html><body style='font-family:sans-serif;background:#0A0A0A;color:#F5F5F5;padding:40px'>"
    "<h2>{title}</h2><p>You can close this tab and go back to Claude Code.</p></body></html>"
)


async def wait_for_code(auth_url: str, state: str) -> str:
    """Opens the browser and waits for Google to redirect back to localhost with ?code=."""
    loop = asyncio.get_running_loop()
    result: asyncio.Future[dict[str, str]] = loop.create_future()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request_line = (await reader.readline()).decode(errors="replace")
        while (await reader.readline()) not in (b"\r\n", b"\n", b""):
            pass  # skip headers
        parts = request_line.split()
        url = urlparse(parts[1]) if len(parts) > 1 else urlparse("/")
        if url.path != CALLBACK_PATH:
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        else:
            query = {key: values[0] for key, values in parse_qs(url.query).items()}
            ok = "code" in query and query.get("state") == state
            page = _DONE_PAGE.format(title="Signed in." if ok else "Sign-in did not finish.").encode()
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                + f"Content-Length: {len(page)}\r\nConnection: close\r\n\r\n".encode()
                + page
            )
            if not result.done():
                result.set_result(query)
        await writer.drain()
        writer.close()

    # Browsers may resolve "localhost" to either IPv4 or IPv6.
    server = await asyncio.start_server(handle, host=["127.0.0.1", "::1"], port=PORT)
    try:
        print(f"\nIf the browser does not open, copy this link into it:\n{auth_url}\n", flush=True)
        webbrowser.open(auth_url)
        query = await asyncio.wait_for(result, timeout=WAIT_SECONDS)
    finally:
        server.close()
        await server.wait_closed()

    if "error" in query:
        raise SystemExit(f"Google returned an error: {query['error']}")
    if query.get("state") != state:
        raise SystemExit("The sign-in response did not match this request (state mismatch).")
    return query["code"]


async def main() -> None:
    results: dict = {}
    async with httpx.AsyncClient(timeout=30) as http:
        oauth = GoogleOAuthClient(http)

        print("Step 1 of 2: basic Google sign-in (openid email profile).", flush=True)
        state = secrets.token_urlsafe(16)
        code = await wait_for_code(
            oauth.authorization_url(scopes=BASIC_SCOPES, redirect_uri=REDIRECT_URI, state=state), state
        )
        step1 = await oauth.exchange_code(code, REDIRECT_URI)
        profile = await oauth.get_profile(step1.access_token.get_secret_value())
        results["step1"] = {"scopes": step1.scopes, "refreshTokenIssued": step1.refresh_token is not None}
        print(f"  Signed in as {profile.email}.", flush=True)

        print("Step 2 of 2: YouTube permission (offline access).", flush=True)
        state = secrets.token_urlsafe(16)
        code = await wait_for_code(
            oauth.authorization_url(
                scopes=[YOUTUBE_SCOPE], redirect_uri=REDIRECT_URI, state=state, offline=True, login_hint=profile.email
            ),
            state,
        )
        step2 = await oauth.exchange_code(code, REDIRECT_URI)
        results["step2"] = {
            "scopes": step2.scopes,
            "refreshTokenIssued": step2.refresh_token is not None,
            "accessTokenExpiresIn": step2.expires_in,
        }
        if step2.refresh_token is None:
            save_results("login", results)
            raise SystemExit("No refresh token was issued in step 2. See data/poc/login.json.")

        try:
            refreshed = await oauth.refresh(step2.refresh_token.get_secret_value())
            again = await oauth.get_profile(refreshed.access_token.get_secret_value())
            results["refresh"] = {
                "ok": True,
                "scopes": refreshed.scopes,
                "newRefreshTokenIssued": refreshed.refresh_token is not None,
                "sameAccount": again.google_sub == profile.google_sub,
            }
        except ExternalApiError as e:
            results["refresh"] = {"ok": False, "error": e.error.model_dump()}

        save_refresh_token(step2.refresh_token.get_secret_value())

    path = save_results("login", results)
    print("\nDone.", flush=True)
    print(f"  Step 1 scopes: {' '.join(results['step1']['scopes'])}")
    print(f"  Step 2 scopes: {' '.join(results['step2']['scopes'])}")
    print(f"  Refresh token issued: {results['step2']['refreshTokenIssued']}")
    print(f"  Refresh works: {results['refresh']['ok']}")
    print(f"  Saved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
