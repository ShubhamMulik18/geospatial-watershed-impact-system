from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.dataset import DatasetResponse


def test_dataset_response_matches_contract():
    response = DatasetResponse(
        dataset_id="dataset-2021",
        display_name="Demo region 2021",
        year=2021,
        coverage_available=True,
        acquisition_date=date(2021, 2, 15),
        supported_indicators=["ndvi", "water"],
        water_methods=["ndwi", "mndwi"],
        bounds_wgs84=(74.0, 16.5, 74.5, 17.0),
        resolution_metres=20,
        quality_mask_available=True,
        warnings=[],
    )

    assert response.model_dump() == {
        "dataset_id": "dataset-2021",
        "display_name": "Demo region 2021",
        "year": 2021,
        "coverage_available": True,
        "acquisition_date": date(2021, 2, 15),
        "supported_indicators": ["ndvi", "water"],
        "water_methods": ["ndwi", "mndwi"],
        "bounds_wgs84": (74.0, 16.5, 74.5, 17.0),
        "resolution_metres": 20.0,
        "quality_mask_available": True,
        "warnings": [],
    }


def test_dataset_response_allows_missing_resolution():
    response = DatasetResponse(
        dataset_id="dataset-2021",
        display_name="Demo region 2021",
        year=2021,
        coverage_available=False,
        acquisition_date=date(2021, 2, 15),
        supported_indicators=[],
        water_methods=[],
        bounds_wgs84=(74.0, 16.5, 74.5, 17.0),
        resolution_metres=None,
        quality_mask_available=False,
        warnings=["Resolution is unavailable."],
    )

    assert response.resolution_metres is None
    assert response.coverage_available is False


@pytest.mark.parametrize(
    "bounds",
    [
        (181.0, 16.5, 74.5, 17.0),
        (74.0, 91.0, 74.5, 17.0),
        (74.0, 16.5, -181.0, 17.0),
        (74.0, 16.5, 74.5, -91.0),
    ],
)
def test_dataset_response_rejects_invalid_bounds(bounds):
    with pytest.raises(ValidationError):
        DatasetResponse(
            dataset_id="dataset-2021",
            display_name="Demo region 2021",
            year=2021,
            coverage_available=True,
            acquisition_date=date(2021, 2, 15),
            supported_indicators=["ndvi"],
            water_methods=[],
            bounds_wgs84=bounds,
            resolution_metres=20,
            quality_mask_available=True,
        )


@pytest.mark.parametrize("resolution", [0, -1])
def test_dataset_response_rejects_invalid_resolution(resolution):
    with pytest.raises(ValidationError):
        DatasetResponse(
            dataset_id="dataset-2021",
            display_name="Demo region 2021",
            year=2021,
            coverage_available=True,
            acquisition_date=date(2021, 2, 15),
            supported_indicators=["ndvi"],
            water_methods=[],
            bounds_wgs84=(74.0, 16.5, 74.5, 17.0),
            resolution_metres=resolution,
            quality_mask_available=True,
        )


@pytest.mark.parametrize(
    "resolution",
    [float("nan"), float("inf"), float("-inf")],
)
def test_dataset_response_rejects_non_finite_resolution(resolution):
    with pytest.raises(ValidationError):
        DatasetResponse(
            dataset_id="dataset-2021",
            display_name="Demo region 2021",
            year=2021,
            coverage_available=True,
            acquisition_date=date(2021, 2, 15),
            supported_indicators=["ndvi"],
            water_methods=[],
            bounds_wgs84=(74.0, 16.5, 74.5, 17.0),
            resolution_metres=resolution,
            quality_mask_available=True,
        )