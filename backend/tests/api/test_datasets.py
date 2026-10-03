from io import BytesIO
from unittest.mock import patch
from datetime import date
import numpy as np
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

from app.db.session import get_db
from app.main import app


def _make_geotiff_bytes() -> bytes:
    buffer = BytesIO()
    data = np.zeros((3, 2, 2), dtype=np.uint16)

    with rasterio.open(
        buffer,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=from_origin(500000, 2000000, 10, 10),
        nodata=0,
    ) as dst:
        dst.write(data)

    return buffer.getvalue()


def _client_with_mock_db():
    from unittest.mock import MagicMock

    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app), db


def test_upload_dataset_returns_canonical_response(tmp_path) -> None:
    client, _ = _client_with_mock_db()

    from app.api.routes import datasets

    original_service = datasets.DatasetService

    class TestDatasetService(original_service):
        def __init__(self, db):
            super().__init__(
                db=db,
                storage_root=tmp_path / "datasets",
            )

    try:
        with patch(
            "app.api.routes.datasets.DatasetService",
            TestDatasetService,
        ):
            response = client.post(
                "/api/datasets/upload",
                files={
                    "file": (
                        "sample.tif",
                        _make_geotiff_bytes(),
                        "image/tiff",
                    )
                },
                data={
                    "display_name": "Demo region 2026",
                    "metadata_json": (
                        '{"acquisition_date":"2026-09-15",'
                        '"capabilities":["ndvi","water"],'
                        '"water_methods":["ndwi","mndwi"]}'
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert set(data) == {
        "dataset_id",
        "display_name",
        "year",
        "coverage_available",
        "acquisition_date",
        "supported_indicators",
        "water_methods",
        "bounds_wgs84",
        "resolution_metres",
        "quality_mask_available",
        "warnings",
    }

    assert data["dataset_id"]
    assert data["display_name"] == "Demo region 2026"
    assert data["year"] == 2026
    assert data["coverage_available"] is True
    assert data["acquisition_date"] == "2026-09-15"
    assert data["supported_indicators"] == ["ndvi", "water"]
    assert data["water_methods"] == ["ndwi", "mndwi"]
    assert data["resolution_metres"] == 10.0
    assert data["quality_mask_available"] is False
    assert data["warnings"] == []

    assert len(data["bounds_wgs84"]) == 4
    assert 74.9 < data["bounds_wgs84"][0] < 75.1


def test_upload_dataset_rejects_invalid_metadata_json() -> None:
    client, _ = _client_with_mock_db()

    try:
        response = client.post(
            "/api/datasets/upload",
            files={
                "file": (
                    "sample.tif",
                    _make_geotiff_bytes(),
                    "image/tiff",
                )
            },
            data={
                "display_name": "Demo region",
                "metadata_json": "not-valid-json",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["message"] == (
        "Expecting value: line 1 column 1 (char 0)"
    )


def test_upload_dataset_requires_acquisition_date(tmp_path) -> None:
    client, _ = _client_with_mock_db()

    from app.api.routes import datasets

    original_service = datasets.DatasetService

    class TestDatasetService(original_service):
        def __init__(self, db):
            super().__init__(
                db=db,
                storage_root=tmp_path / "datasets",
            )

    try:
        with patch(
            "app.api.routes.datasets.DatasetService",
            TestDatasetService,
        ):
            response = client.post(
                "/api/datasets/upload",
                files={
                    "file": (
                        "sample.tif",
                        _make_geotiff_bytes(),
                        "image/tiff",
                    )
                },
                data={
                    "display_name": "Demo region",
                    "metadata_json": "{}",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "Acquisition date is required in metadata_json."
    )

def test_list_datasets_returns_datasets() -> None:
    from unittest.mock import MagicMock

    client, db = _client_with_mock_db()

    dataset = MagicMock()
    dataset.id = "test-dataset-id"
    dataset.display_name = "Demo region"
    dataset.year = 2026
    dataset.acquisition_date = date(2026, 9, 15)
    dataset.capabilities = ["ndvi", "water"]
    dataset.crs = "EPSG:32643"
    dataset.bounds = {
        "left": 500000.0,
        "bottom": 1999980.0,
        "right": 500020.0,
        "top": 2000000.0,
    }
    dataset.resolution = {"x": 10.0, "y": 10.0}
    dataset.manifest = {
        "water_methods": ["ndwi"],
    }
    dataset.quality_metadata = None

    with patch(
        "app.api.routes.datasets.DatasetService.list_datasets",
        return_value=[dataset],
    ):
        try:
            response = client.get("/api/datasets")
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1

def test_list_datasets_filters_by_capability() -> None:
    client, _ = _client_with_mock_db()

    with patch(
        "app.api.routes.datasets.DatasetService.list_datasets",
        return_value=[],
    ) as list_datasets:
        try:
            response = client.get("/api/datasets?capability=water")
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    list_datasets.assert_called_once_with(capability="water")