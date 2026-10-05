from datetime import date
from enum import StrEnum


from pydantic import Field, field_validator

from .common import SchemaBase


class AnalysisStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"

class Indicator(StrEnum):
    NDVI = "ndvi"
    WATER = "water"

class AnalysisMetrics(SchemaBase):
    """Computed environmental metrics for an analysis."""

    ndvi_before: float | None = None
    ndvi_after: float | None = None
    ndvi_change: float | None = None

    water_before_hectares: float | None = None
    water_after_hectares: float | None = None
    water_change_hectares: float | None = None
    water_change_percent: float | None = None

class AnalysisSeriesPoint(SchemaBase):
    """One chronological dataset measurement in an analysis."""

    dataset_id: str = Field(min_length=1)
    date: date
    ndvi_mean: float | None = None
    water_hectares: float | None = None

class AnalysisComparison(SchemaBase):
    """Before/after comparison between two datasets."""

    before_dataset_id: str = Field(min_length=1)
    after_dataset_id: str = Field(min_length=1)

    ndvi_change: float | None = None
    water_change_hectares: float | None = None
    water_change_percent: float | None = None

    ndvi_change_unavailable_reason: str | None = None
    water_change_unavailable_reason: str | None = None

class AnalysisQuality(SchemaBase):
    """Quality and coverage information for an analysis."""

    aoi_hectares: float | None = None
    common_valid_hectares: float | None = None
    common_valid_fraction: float | None = None
    per_dataset_valid_fraction: dict[str, float] = Field(default_factory=dict)
    cloud_mask_available: dict[str, bool] = Field(default_factory=dict)
    comparison_limitations: list[str] = Field(default_factory=list)

class AnalysisProvenance(SchemaBase):
    """Reproducibility metadata for an analysis."""

    model_version: str | None = None
    model_hash: str | None = None
    pipeline_version: str | None = None

    input_hashes: dict[str, str] = Field(default_factory=dict)

    date_ordering: list[str] = Field(default_factory=list)

    target_crs: str | None = None
    target_grid: str | None = None
    target_resolution: float | None = None

    band_mappings: dict[str, str] = Field(default_factory=dict)
    resampling: str | None = None
    water_method: str | None = None
    water_threshold: float | None = None
    coverage_threshold: float | None = None

    processing_timestamp: str | None = None

class LayerDescriptor(SchemaBase):
    """Descriptor for a generated analytical map layer."""

    layer_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)

    preview_url: str | None = None
    download_url: str | None = None

    bounds_wgs84: tuple[float, float, float, float]

    preview_crs: str = Field(min_length=1)

    legend: dict[str, object] = Field(default_factory=dict)

class AnalysisError(SchemaBase):
    """Error information stored on a failed analysis."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, object] = Field(default_factory=dict)

class AnalysisInputs(SchemaBase):
    """Inputs persisted with an analysis."""

    photo_id: str = Field(min_length=1)
    polygon: AnalysisPolygon
    dataset_ids: list[str] = Field(min_length=2)
    indicators: list[Indicator] = Field(min_length=1)

    @field_validator("dataset_ids")
    @classmethod
    def validate_dataset_ids(cls, value: list[str]) -> list[str]:
        if any(not dataset_id.strip() for dataset_id in value):
            raise ValueError("Dataset IDs must not be empty.")

        if len(set(value)) < 2:
            raise ValueError("At least two distinct dataset IDs are required.")

        return value

class PredictionSnapshot(SchemaBase):
    """Prediction state captured when an analysis is created."""

    class_name: str = Field(alias="class", min_length=1)
    class_id: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    requires_verification: bool
    model_version: str = Field(min_length=1)

class AnalysisPolygon(SchemaBase):
    """GeoJSON Polygon structure used by the analysis request."""

    type: str = Field(pattern=r"^Polygon$")
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(
        cls,
        value: list[list[list[float]]],
    ) -> list[list[list[float]]]:
        if not value:
            raise ValueError("Polygon coordinates must not be empty.")

        if not value[0]:
            raise ValueError("Polygon exterior ring must not be empty.")

        for ring in value:
            for position in ring:
                if len(position) != 2:
                    raise ValueError(
                        "Polygon positions must contain longitude and latitude."
                    )

                longitude, latitude = position

                if not -180.0 <= longitude <= 180.0:
                    raise ValueError("Longitude must be between -180 and 180.")

                if not -90.0 <= latitude <= 90.0:
                    raise ValueError("Latitude must be between -90 and 90.")

        for ring in value:
            if len(ring) < 4:
                raise ValueError(
                    "Polygon rings must contain at least four positions."
                )

            if ring[0] != ring[-1]:
                raise ValueError("Polygon rings must be closed.")

        exterior = value[0]

        def segments_intersect(
            a: list[float],
            b: list[float],
            c: list[float],
            d: list[float],
        ) -> bool:
            def orientation(
                p: list[float],
                q: list[float],
                r: list[float],
            ) -> float:
                return (
                    (q[1] - p[1]) * (r[0] - q[0])
                    - (q[0] - p[0]) * (r[1] - q[1])
                )

            def on_segment(
                p: list[float],
                q: list[float],
                r: list[float],
            ) -> bool:
                return (
                    min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
                    and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
                )

            o1 = orientation(a, b, c)
            o2 = orientation(a, b, d)
            o3 = orientation(c, d, a)
            o4 = orientation(c, d, b)

            if (
                o1 == 0
                and on_segment(a, c, b)
                or o2 == 0
                and on_segment(a, d, b)
                or o3 == 0
                and on_segment(c, a, d)
                or o4 == 0
                and on_segment(c, b, d)
            ):
                return True

            return (
                (o1 > 0) != (o2 > 0)
                and (o3 > 0) != (o4 > 0)
            )

        segments = list(zip(exterior, exterior[1:]))

        for index, (start_a, end_a) in enumerate(segments):
            for other_index, (start_b, end_b) in enumerate(segments):
                if other_index <= index + 1:
                    continue

                if (
                    index == 0
                    and other_index == len(segments) - 1
                ):
                    continue

                if segments_intersect(
                    start_a,
                    end_a,
                    start_b,
                    end_b,
                ):
                    raise ValueError(
                        "Polygon exterior ring must not self-intersect."
                    )

        return value


class AnalysisRequest(SchemaBase):
    """Canonical request used to create an analysis."""

    photo_id: str = Field(min_length=1)
    polygon: AnalysisPolygon
    dataset_ids: list[str] = Field(min_length=2)
    indicators: list[Indicator] = Field(min_length=1)

    @field_validator("dataset_ids")
    @classmethod
    def validate_dataset_ids(cls, value: list[str]) -> list[str]:
        if any(not dataset_id.strip() for dataset_id in value):
            raise ValueError("Dataset IDs must not be empty.")

        if len(set(value)) < 2:
            raise ValueError("At least two distinct dataset IDs are required.")

        return value

class AnalysisResponse(SchemaBase):
    """Canonical public analysis lifecycle response."""

    schema_version: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)

    status: AnalysisStatus
    stage: str = Field(min_length=1)

    inputs: AnalysisInputs

    prediction: PredictionSnapshot | None = None

    metrics: AnalysisMetrics | None = None
    series: list[AnalysisSeriesPoint] = Field(default_factory=list)
    comparisons: list[AnalysisComparison] = Field(default_factory=list)
    layers: list[LayerDescriptor] = Field(default_factory=list)

    quality: AnalysisQuality | None = None
    warnings: list[str] = Field(default_factory=list)

    provenance: AnalysisProvenance | None = None

    report_status: ReportStatus = ReportStatus.NOT_REQUESTED

    error: AnalysisError | None = None