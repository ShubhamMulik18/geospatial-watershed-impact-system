from pydantic import Field

from .common import SchemaBase


class ErrorBody(SchemaBase):
    """Shared public API error object."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(SchemaBase):
    """Shared public API error envelope."""

    error: ErrorBody