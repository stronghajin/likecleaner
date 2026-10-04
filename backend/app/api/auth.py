from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentSession, Db, Http, write_session
from app.core.errors import AppError
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.get("/api/auth/google/login")
async def login(request: Request, http: Http) -> RedirectResponse:
    """Starts Google sign-in (step 1)."""
    result = auth_service.start_login(http)
    write_session(request, result.session)
    return RedirectResponse(result.redirect_to, status_code=302)


@router.get("/api/auth/google/callback")
async def callback(
    request: Request,
    db: Db,
    http: Http,
    session: CurrentSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Google sends the browser back here after step 1 and step 2."""
    result = await auth_service.handle_callback(db, http, session, code=code, state=state, error=error)
    write_session(request, result.session)
    return RedirectResponse(result.redirect_to, status_code=302)


@router.post("/api/auth/logout", status_code=204)
async def logout(request: Request) -> Response:
    """Ends the session only; Google tokens are kept (SPEC.md 3-4)."""
    request.session.clear()
    return Response(status_code=204)


@router.get("/api/me")
async def me(request: Request, db: Db, session: CurrentSession) -> UserResponse:
    """The signed-in user with status active / disabled / not_registered (DECISIONS.md 56)."""
    user = await auth_service.get_me(db, session)
    if user is None:
        request.session.clear()
        raise AppError(401, "notSignedIn", "Please sign in to continue.")
    return user
