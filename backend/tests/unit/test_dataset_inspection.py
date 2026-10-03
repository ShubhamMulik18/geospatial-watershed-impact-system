from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.storage.dataset_inspection import inspect_dataset


def test_inspect_dataset_extracts_geotiff_metadata(tmp_path: Path) -> None:
    path = tmp_path / "sample.tif"

    data = np.zeros((3, 2, 2), dtype=np.uint16)

    with rasterio.open(
        path,
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

    inspection = inspect_dataset(path)

    assert inspection.crs == "EPSG:32643"
    assert inspection.resolution == {"x": 10.0, "y": 10.0}
    assert inspection.bounds == {
        "left": 500000.0,
        "bottom": 1999980.0,
        "right": 500020.0,
        "top": 2000000.0,
    }
    assert inspection.width == 2
    assert inspection.height == 2
    assert inspection.count == 3
    assert inspection.nodata == 0.0

    assert inspection.bands == [
        {"index": 1, "dtype": "uint16", "nodata": 0.0},
        {"index": 2, "dtype": "uint16", "nodata": 0.0},
        {"index": 3, "dtype": "uint16", "nodata": 0.0},
    ]

    assert inspection.scale == {
        "1": 1.0,
        "2": 1.0,
        "3": 1.0,
    }

    assert inspection.offset == {
        "1": 0.0,
        "2": 0.0,
        "3": 0.0,
    }

    assert inspection.acquisition_date is None


def test_inspect_dataset_rejects_missing_crs(tmp_path: Path) -> None:
    path = tmp_path / "missing_crs.tif"

    data = np.zeros((1, 2, 2), dtype=np.uint16)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="uint16",
        transform=from_origin(500000, 2000000, 10, 10),
    ) as dst:
        dst.write(data)

    import pytest

    with pytest.raises(ValueError, match="CRS is missing"):
        inspect_dataset(path)