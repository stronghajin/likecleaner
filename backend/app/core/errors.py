"""Every error response has the same shape: {status, reason, message} (frontend `ApiErrorInfo`)."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Raised by services for expected failures, e.g. AppError(409, "jobAlreadyRunning", "…")."""

    def __init__(self, status: int, reason: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.message = message


def _respond(status: int, reason: str, message: str) -> JSONResponse:
    body = ErrorResponse(status=status, reason=reason, message=message)
    return JSONResponse(status_code=status, content=body.model_dump(by_alias=True))


_HTTP_REASONS = {
    401: "notSignedIn",
    403: "forbidden",
    404: "notFound",
    405: "methodNotAllowed",
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _respond(exc.status, exc.reason, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(part) for part in first.get("loc", ()))
        detail = first.get("msg", "Invalid request.")
        return _respond(400, "invalidRequest", f"{where}: {detail}" if where else detail)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        reason = _HTTP_REASONS.get(exc.status_code, "httpError")
        return _respond(exc.status_code, reason, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Log the details on the server; never send internals (or secrets) to the browser.
        logger.exception("Unhandled error", exc_info=exc)
        return _respond(500, "internalError", "Something went wrong on the server.")
