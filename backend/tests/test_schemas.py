from app.schemas.common import ApiModel


class _Example(ApiModel):
    picture_url: str
    retry_at: str


def test_json_uses_camel_case_like_the_frontend_types():
    model = _Example(picture_url="https://example.com/a.png", retry_at="2026-10-03T00:00:00Z")
    assert model.model_dump() == {"pictureUrl": "https://example.com/a.png", "retryAt": "2026-10-03T00:00:00Z"}


def test_accepts_both_camel_and_snake_case_input():
    assert _Example.model_validate({"pictureUrl": "x", "retryAt": "y"}).picture_url == "x"
    assert _Example(picture_url="x", retry_at="y").retry_at == "y"
