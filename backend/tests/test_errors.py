"""Every error has the frontend `ApiErrorInfo` shape: {status, reason, message}."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.errors import AppError
from app.main import app

router = APIRouter()


class Body(BaseModel):
    count: int


@router.get("/test/app-error")
async def _app_error() -> None:
    raise AppError(409, "jobAlreadyRunning", "Another job is already running.")


@router.post("/test/validation")
async def _validation(body: Body) -> None:
    return None


@router.get("/test/crash")
async def _crash() -> None:
    raise RuntimeError("secret internal detail")


app.include_router(router)


async def test_app_error_keeps_status_reason_and_message(client):
    response = await client.get("/test/app-error")
    assert response.status_code == 409
    assert response.json() == {
        "status": 409,
        "reason": "jobAlreadyRunning",
        "message": "Another job is already running.",
    }


async def test_unknown_route_is_404_in_the_same_shape(client):
    response = await client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"status": 404, "reason": "notFound", "message": "Not Found"}


async def test_invalid_body_is_400_invalid_request(client):
    response = await client.post("/test/validation", json={"count": "many"})
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == 400
    assert body["reason"] == "invalidRequest"
    assert "count" in body["message"]


async def test_unexpected_error_hides_internal_details(client):
    response = await client.get("/test/crash")
    assert response.status_code == 500
    assert response.json() == {
        "status": 500,
        "reason": "internalError",
        "message": "Something went wrong on the server.",
    }
