"""Base for every schema that crosses a layer or goes to the browser.

Fields are snake_case in Python and camelCase in JSON, so responses match
`frontend/src/services/types.ts` exactly (e.g. picture_url -> pictureUrl).
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # build with snake_case names in Python
        from_attributes=True,  # repositories build schemas from ORM rows
        serialize_by_alias=True,  # FastAPI responses come out in camelCase
    )


class ErrorResponse(ApiModel):
    """Frontend `ApiErrorInfo`. Used for every error response and for job item errors."""

    status: int
    reason: str
    message: str
