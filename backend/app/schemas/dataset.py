from datetime import date
from typing import Annotated

from pydantic import Field

from .common import FiniteFloat, SchemaBase


BoundsWGS84 = Annotated[
    tuple[
        Annotated[FiniteFloat, Field(ge=-180.0, le=180.0)],
        Annotated[FiniteFloat, Field(ge=-90.0, le=90.0)],
        Annotated[FiniteFloat, Field(ge=-180.0, le=180.0)],
        Annotated[FiniteFloat, Field(ge=-90.0, le=90.0)],
    ],
    Field(min_length=4, max_length=4),
]


class DatasetResponse(SchemaBase):
    """Canonical public dataset catalogue response."""

    dataset_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    year: int = Field(ge=1)
    coverage_available: bool
    acquisition_date: date
    supported_indicators: list[str] = Field(default_factory=list)
    water_methods: list[str] = Field(default_factory=list)
    bounds_wgs84: BoundsWGS84
    resolution_metres: FiniteFloat | None = Field(default=None, gt=0)
    quality_mask_available: bool
    warnings: list[str] = Field(default_factory=list)