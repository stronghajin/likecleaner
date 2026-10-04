from app.schemas.common import ErrorResponse


class ExternalApiError(Exception):
    """A Google / YouTube call failed. `error` has the same shape as every other error ({status, reason, message})."""

    def __init__(self, error: ErrorResponse) -> None:
        super().__init__(f"{error.status} {error.reason}: {error.message}")
        self.error = error
