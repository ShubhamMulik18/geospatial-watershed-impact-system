from io import BytesIO
from pathlib import Path
from datetime import date
import numpy as np
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin
from sqlalchemy import delete, select

from app.db.session import SessionLocal, get_db
from app.main import app
from app.models.dataset import Dataset


def _make_geotiff() -> bytes:
    data = np.zeros((3, 2, 2), dtype=np.uint16)
    buffer = BytesIO()

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


def test_upload_dataset_api_persists_to_postgresql(tmp_path: Path) -> None:
    db = SessionLocal()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/datasets/upload",
            files={
                "file": (
                    "api-integration-dataset.tif",
                    _make_geotiff(),
                    "image/tiff",
                )
            },
            data={
                "display_name": "API Integration Dataset 2026",
                "metadata_json": (
                    '{"acquisition_date":"2026-09-15",'
                    '"capabilities":["ndvi","water"],'
                    '"water_methods":["ndwi"]}'
                ),
            },
        )

        assert response.status_code == 201

        payload = response.json()

        assert payload["display_name"] == "API Integration Dataset 2026"
        assert payload["year"] == 2026
        assert payload["acquisition_date"] == "2026-09-15"
        assert payload["supported_indicators"] == ["ndvi", "water"]
        assert payload["water_methods"] == ["ndwi"]
        assert payload["coverage_available"] is True
        assert payload["resolution_metres"] == 10.0

        dataset_id = payload["dataset_id"]

        persisted = db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        ).scalar_one()

        assert persisted.display_name == "API Integration Dataset 2026"
        assert persisted.year == 2026
        assert persisted.crs == "EPSG:32643"
        assert persisted.capabilities == ["ndvi", "water"]
        assert persisted.sha256
        assert Path(persisted.path).exists()

    finally:
        app.dependency_overrides.clear()

        if db.in_transaction():
            db.rollback()

        db.execute(
            delete(Dataset).where(
                Dataset.display_name == "API Integration Dataset 2026"
            )
        )
        db.commit()
        db.close()

def test_list_datasets_api_filters_by_capability() -> None:
    db = SessionLocal()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        dataset = Dataset(
            display_name="Catalogue Integration Dataset 2026",
            acquisition_date=date(2026, 9, 15),
            year=2026,
            path="uploads/datasets/catalogue-test.tif",
            sha256="b" * 64,
            crs="EPSG:32643",
            transform={
                "a": 10.0,
                "b": 0.0,
                "c": 500000.0,
                "d": 0.0,
                "e": -10.0,
                "f": 2000000.0,
            },
            resolution={"x": 10.0, "y": 10.0},
            bounds={
                "left": 500000.0,
                "bottom": 1999980.0,
                "right": 500020.0,
                "top": 2000000.0,
            },
            bands=[
                {"index": 1, "dtype": "uint16", "nodata": 0},
            ],
            scale={"1": 1.0},
            offset={"1": 0.0},
            quality_metadata=None,
            capabilities=["ndvi", "water"],
            manifest={"water_methods": ["ndwi"]},
        )

        db.add(dataset)
        db.commit()

        response = client.get("/api/datasets?capability=water")

        assert response.status_code == 200

        payload = response.json()

        assert len(payload) >= 1
        assert any(
            item["dataset_id"] == str(dataset.id)
            for item in payload
        )

        matching = next(
            item for item in payload
            if item["dataset_id"] == str(dataset.id)
        )

        assert matching["supported_indicators"] == ["ndvi", "water"]
        assert matching["water_methods"] == ["ndwi"]

    finally:
        app.dependency_overrides.clear()

        db.execute(
            delete(Dataset).where(
                Dataset.display_name == "Catalogue Integration Dataset 2026"
            )
        )
        db.commit()
        db.close()