from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.integrations.geospatial.base import AnalysisResult, DatasetInspection
from app.integrations.geospatial.production_adapter import (
    ProductionGeospatialAdapter,
)


def _create_synthetic_raster(
    path: Path,
    crs: str = "EPSG:4326",
    nir_val: float = 0.8,
    red_val: float = 0.2,
    green_val: float = 0.6,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raster_data = np.zeros((5, 4, 4), dtype=np.float32)
    raster_data[2] = green_val  # Band 3
    raster_data[3] = red_val    # Band 4
    raster_data[4] = nir_val    # Band 5

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=4,
        width=4,
        count=5,
        dtype="float32",
        crs=crs,
        transform=from_origin(74.0, 17.0, 0.001, 0.001),
        nodata=-9999.0,
    ) as dst:
        dst.write(raster_data)


def test_production_adapter_inspect_missing_path() -> None:
    adapter = ProductionGeospatialAdapter()
    inspection = adapter.inspect_dataset({"dataset_id": "ds-1"})

    assert isinstance(inspection, DatasetInspection)
    assert not inspection.compatible
    assert "Dataset path is missing." in inspection.errors


def test_production_adapter_inspect_valid_raster(tmp_path: Path) -> None:
    raster_path = tmp_path / "test.tif"
    _create_synthetic_raster(raster_path)

    adapter = ProductionGeospatialAdapter()
    inspection = adapter.inspect_dataset({
        "dataset_id": "ds-1",
        "path": str(raster_path),
    })

    assert isinstance(inspection, DatasetInspection)
    assert inspection.compatible
    assert inspection.metadata["band_count"] == 5
    assert inspection.metadata["crs"] == "EPSG:4326"


def test_production_adapter_run_analysis_end_to_end(tmp_path: Path) -> None:
    raster1 = tmp_path / "r1.tif"
    raster2 = tmp_path / "r2.tif"
    output_dir = tmp_path / "outputs"

    _create_synthetic_raster(raster1, nir_val=0.8, red_val=0.2)
    _create_synthetic_raster(raster2, nir_val=0.6, red_val=0.2)

    adapter = ProductionGeospatialAdapter()

    progress_reports = []

    def on_progress(stage: str) -> None:
        progress_reports.append(stage)

    request = {
        "analysis_id": "analysis-geo-001",
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [74.000, 16.996],
                [74.004, 16.996],
                [74.004, 17.000],
                [74.000, 17.000],
                [74.000, 16.996],
            ]],
        },
        "indicators": ["ndvi"],
        "dataset_specs": [
            {
                "dataset_id": "dataset-2021",
                "path": str(raster1),
                "manifest": {
                    "bands": {"red": 4, "nir": 5, "green": 3},
                    "band_scaling": {
                        "red": {"scale": 1.0, "offset": 0.0},
                        "nir": {"scale": 1.0, "offset": 0.0},
                        "green": {"scale": 1.0, "offset": 0.0},
                    },
                },
            },
            {
                "dataset_id": "dataset-2023",
                "path": str(raster2),
                "manifest": {
                    "bands": {"red": 4, "nir": 5, "green": 3},
                    "band_scaling": {
                        "red": {"scale": 1.0, "offset": 0.0},
                        "nir": {"scale": 1.0, "offset": 0.0},
                        "green": {"scale": 1.0, "offset": 0.0},
                    },
                },
            },
        ],
    }

    result = adapter.run_analysis(
        request=request,
        output_dir=output_dir,
        progress_callback=on_progress,
    )

    assert isinstance(result, AnalysisResult)
    assert "mean_ndvi" in result.metrics
    assert len(result.series) == 2
    assert len(result.comparisons) == 1
    assert len(result.artifacts) == 4
    kinds = {a["kind"] for a in result.artifacts}
    assert "ndvi_raster" in kinds
    assert "preview_ndvi" in kinds

    # Check artifact structure matches backend AnalysisResult
    first_artifact = result.artifacts[0]
    assert "artifact_id" in first_artifact
    assert first_artifact["kind"] == "ndvi_raster"
    assert first_artifact["dataset_id"] == "dataset-2021"
    assert (output_dir / first_artifact["relative_path"]).exists()

    # Verify progress was communicated
    assert len(progress_reports) > 0
    assert "processing_100%" in progress_reports[-1]


def test_production_adapter_empty_datasets_raises(tmp_path: Path) -> None:
    adapter = ProductionGeospatialAdapter()
    with pytest.raises(ValueError, match="No dataset specifications"):
        adapter.run_analysis(
            request={
                "analysis_id": "test-1",
                "polygon": {"type": "Polygon", "coordinates": []},
                "indicators": ["ndvi"],
                "dataset_specs": [],
            },
            output_dir=tmp_path / "out",
        )
