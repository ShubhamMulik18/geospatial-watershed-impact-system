from datetime import date
from enum import StrEnum

from pydantic import Field

from .common import Latitude, Longitude, SchemaBase


class EXIFStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"
    INVALID = "invalid"


class PhotoResponse(SchemaBase):
    """Canonical public response for a processed photo upload."""

    photo_id: str = Field(min_length=1)
    latitude: Latitude | None = None
    longitude: Longitude | None = None
    capture_date: date | None = None
    exif_status: EXIFStatus
    warnings: list[str] = Field(default_factory=list)