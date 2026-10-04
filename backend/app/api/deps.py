"""Shared request dependencies: DB session, HTTP client, session cookie, active-user gate."""

from typing import Annotated

import httpx
from fastapi import Depends, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.auth import SessionState
from app.schemas.user import UserRecord
from app.services import auth_service

Db = Annotated[AsyncSession, Depends(get_db)]


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


Http = Annotated[httpx.AsyncClient, Depends(get_http)]


def read_session(request: Request) -> SessionState:
    try:
        return SessionState.model_validate(request.session)
    except ValidationError:
        return SessionState()  # cookie from an older version: treat as signed out


def write_session(request: Request, state: SessionState) -> None:
    request.session.clear()
    request.session.update(state.model_dump(mode="json", exclude_none=True))


CurrentSession = Annotated[SessionState, Depends(read_session)]


async def require_active_user(db: Db, session: CurrentSession) -> UserRecord:
    """Add to every YouTube-related route: 401 notSignedIn / 403 accessDenied otherwise."""
    return await auth_service.require_active(db, session)


ActiveUser = Annotated[UserRecord, Depends(require_active_user)]
