from datetime import date, datetime, timezone
from math import isfinite
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def validate_finite(value: float) -> float:
    """Reject NaN and infinite numeric values."""
    if not isfinite(value):
        raise ValueError("Value must be finite.")
    return value


FiniteFloat = Annotated[float, AfterValidator(validate_finite)]

Latitude = Annotated[
    FiniteFloat,
    Field(ge=-90.0, le=90.0),
]

Longitude = Annotated[
    FiniteFloat,
    Field(ge=-180.0, le=180.0),
]

Confidence = Annotated[
    FiniteFloat,
    Field(ge=0.0, le=1.0),
]


class SchemaBase(BaseModel):
    """Base configuration shared by public API schemas."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


def validate_utc_datetime(value: datetime) -> datetime:
    """Require timezone-aware UTC datetimes."""
    if value.tzinfo is None:
        raise ValueError("Datetime must include a timezone.")

    if value.utcoffset() is None:
        raise ValueError("Datetime must include a valid timezone.")

    if value.astimezone(timezone.utc) != value:
        raise ValueError("Datetime must be expressed in UTC.")

    return value


UTCDatetime = Annotated[
    datetime,
    AfterValidator(validate_utc_datetime),
]


AcquisitionDate = date


class BoundsWGS84(SchemaBase):
    """
    WGS84 bounding box represented as:
    [min_longitude, min_latitude, max_longitude, max_latitude]
    """

    min_longitude: Longitude
    min_latitude: Latitude
    max_longitude: Longitude
    max_latitude: Latitude

    def as_list(self) -> list[float]:
        return [
            self.min_longitude,
            self.min_latitude,
            self.max_longitude,
            self.max_latitude,
        ]