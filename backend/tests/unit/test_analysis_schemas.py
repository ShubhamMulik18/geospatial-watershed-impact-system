from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
    Indicator,
    ReportStatus,
)


def sample_request() -> dict:
    return {
        "photo_id": "photo-001",
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [74.24, 16.70],
                    [74.25, 16.70],
                    [74.25, 16.71],
                    [74.24, 16.71],
                    [74.24, 16.70],
                ]
            ],
        },
        "dataset_ids": ["dataset-2021", "dataset-2026"],
        "indicators": ["ndvi", "water"],
    }


def test_analysis_request_matches_contract():
    request = AnalysisRequest(**sample_request())

    assert request.photo_id == "photo-001"
    assert request.polygon.type == "Polygon"
    assert request.dataset_ids == ["dataset-2021", "dataset-2026"]
    assert request.indicators == [Indicator.NDVI, Indicator.WATER]


def test_analysis_request_rejects_multipolygon():
    payload = sample_request()
    payload["polygon"] = {
        "type": "MultiPolygon",
        "coordinates": [],
    }

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_requires_two_distinct_datasets():
    payload = sample_request()
    payload["dataset_ids"] = ["dataset-2021", "dataset-2021"]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_requires_at_least_two_datasets():
    payload = sample_request()
    payload["dataset_ids"] = ["dataset-2021"]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_rejects_empty_dataset_id():
    payload = sample_request()
    payload["dataset_ids"] = ["dataset-2021", ""]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_rejects_invalid_coordinates():
    payload = sample_request()
    payload["polygon"]["coordinates"][0][0] = [181.0, 16.70]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)

def test_analysis_request_rejects_unclosed_polygon():
    payload = sample_request()
    payload["polygon"]["coordinates"][0][-1] = [74.24, 16.71]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_rejects_self_intersecting_polygon():
    payload = sample_request()
    payload["polygon"]["coordinates"] = [
        [
            [74.24, 16.70],
            [74.25, 16.71],
            [74.25, 16.70],
            [74.24, 16.71],
            [74.24, 16.70],
        ]
    ]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_request_rejects_invalid_indicator():
    payload = sample_request()
    payload["indicators"] = ["unknown_indicator"]

    with pytest.raises(ValidationError):
        AnalysisRequest(**payload)


def test_analysis_response_accepts_completed_contract():
    response = AnalysisResponse(
        schema_version="1.0",
        analysis_id="analysis-001",
        status=AnalysisStatus.COMPLETED,
        stage="finished",
        inputs=sample_request(),
        prediction={
            "class": "Check Dam",
            "class_id": "check_dam",
            "confidence": 0.92,
            "requires_verification": False,
            "model_version": "intervention-mobilenetv2-v1",
        },
        metrics={
            "ndvi_before": 0.42,
            "ndvi_after": 0.57,
            "ndvi_change": 0.15,
            "water_before_hectares": 3.1,
            "water_after_hectares": 5.8,
            "water_change_hectares": 2.7,
            "water_change_percent": 87.096774,
        },
        series=[
            {
                "dataset_id": "dataset-2021",
                "date": date(2021, 2, 15),
                "ndvi_mean": 0.42,
                "water_hectares": 3.1,
            },
            {
                "dataset_id": "dataset-2026",
                "date": date(2026, 2, 17),
                "ndvi_mean": 0.57,
                "water_hectares": 5.8,
            },
        ],
        warnings=[
            "Observed change does not prove that the intervention caused the change."
        ],
        report_status=ReportStatus.NOT_REQUESTED,
        error=None,
    )

    assert response.analysis_id == "analysis-001"
    assert response.status == AnalysisStatus.COMPLETED
    assert response.stage == "finished"
    assert response.prediction is not None
    assert response.prediction.class_name == "Check Dam"
    assert response.metrics is not None
    assert response.metrics.ndvi_change == 0.15
    assert response.series[0].dataset_id == "dataset-2021"


def test_analysis_response_defaults_are_safe_for_early_lifecycle():
    response = AnalysisResponse(
        schema_version="1.0",
        analysis_id="analysis-001",
        status=AnalysisStatus.QUEUED,
        stage="queued",
        inputs=sample_request(),
    )

    assert response.prediction is None
    assert response.metrics is None
    assert response.series == []
    assert response.comparisons == []
    assert response.layers == []
    assert response.quality is None
    assert response.warnings == []
    assert response.provenance is None
    assert response.report_status == ReportStatus.NOT_REQUESTED
    assert response.error is None


@pytest.mark.parametrize(
    "status",
    [
        "created",
        "queued",
        "running",
        "completed",
        "failed",
    ],
)
def test_supported_analysis_status_values(status):
    response = AnalysisResponse(
        schema_version="1.0",
        analysis_id="analysis-001",
        status=status,
        stage="test",
        inputs=sample_request(),
    )

    assert response.status.value == status


def test_analysis_response_serializes_prediction_class_as_class():
    response = AnalysisResponse(
        schema_version="1.0",
        analysis_id="analysis-001",
        status=AnalysisStatus.COMPLETED,
        stage="finished",
        inputs=sample_request(),
        prediction={
            "class": "Check Dam",
            "class_id": "check_dam",
            "confidence": 0.92,
            "requires_verification": False,
            "model_version": "intervention-mobilenetv2-v1",
        },
    )

    dumped = response.model_dump(by_alias=True)

    assert dumped["prediction"]["class"] == "Check Dam"