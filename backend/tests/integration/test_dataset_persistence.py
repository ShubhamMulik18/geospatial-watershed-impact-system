from io import BytesIO
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService


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


def test_dataset_persists_to_postgresql(tmp_path: Path) -> None:
    data = _make_geotiff()
    db = SessionLocal()

    try:
        service = DatasetService(
            db=db,
            storage_root=tmp_path / "datasets",
        )

        dataset = service.create_dataset(
            stream=BytesIO(data),
            original_name="integration-dataset.tif",
            display_name="Integration Dataset 2026",
            metadata={
                "acquisition_date": "2026-09-15",
                "capabilities": ["ndvi", "water"],
            },
        )

        db.commit()

        persisted = db.execute(
            select(Dataset).where(Dataset.id == dataset.id)
        ).scalar_one()

        assert persisted.display_name == "Integration Dataset 2026"
        assert persisted.acquisition_date.isoformat() == "2026-09-15"
        assert persisted.year == 2026
        assert persisted.crs == "EPSG:32643"
        assert persisted.resolution == {"x": 10.0, "y": 10.0}
        assert persisted.bounds == {
            "left": 500000.0,
            "bottom": 1999980.0,
            "right": 500020.0,
            "top": 2000000.0,
        }
        assert persisted.capabilities == ["ndvi", "water"]
        assert persisted.sha256 == dataset.sha256
        assert Path(persisted.path).read_bytes() == data

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(
            delete(Dataset).where(
                Dataset.display_name == "Integration Dataset 2026"
            )
        )
        db.commit()
        db.close()

def test_dataset_requires_acquisition_date(tmp_path: Path) -> None:
    data = _make_geotiff()
    db = SessionLocal()
    storage_root = tmp_path / "datasets"

    try:
        service = DatasetService(
            db=db,
            storage_root=storage_root,
        )

        try:
            service.create_dataset(
                stream=BytesIO(data),
                original_name="missing-date.tif",
                display_name="Missing Date Dataset",
                metadata={
                    "capabilities": ["ndvi"],
                },
            )
        except ValueError as exc:
            assert str(exc) == "Acquisition date is required in metadata_json."
        else:
            raise AssertionError(
                "DatasetService should reject missing acquisition date."
            )

        assert not list(storage_root.glob("*"))

    finally:
        if db.in_transaction():
            db.rollback()
        db.close()

def test_dataset_rejects_file_over_size_limit(tmp_path: Path) -> None:
    data = _make_geotiff()
    db = SessionLocal()
    storage_root = tmp_path / "datasets"

    try:
        service = DatasetService(
            db=db,
            storage_root=storage_root,
            max_size_bytes=100,
        )

        try:
            service.create_dataset(
                stream=BytesIO(data),
                original_name="oversized.tif",
                display_name="Oversized Dataset",
                metadata={
                    "acquisition_date": "2026-09-15",
                },
            )
        except Exception as exc:
            assert "maximum allowed size" in str(exc)
        else:
            raise AssertionError(
                "DatasetService should reject an oversized dataset."
            )

        assert not list(storage_root.glob("*"))

    finally:
        if db.in_transaction():
            db.rollback()
        db.close()
