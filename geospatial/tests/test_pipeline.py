import numpy as np
import rasterio
from rasterio.transform import from_origin

from geospatial.contracts import AnalysisRequest, GeospatialResult
from geospatial.pipeline import run_analysis


def test_pipeline_reads_raster_and_calculates_ndvi(tmp_path):
    raster_path = tmp_path / "input.tif"
    output_dir = tmp_path / "output"

    raster_data = np.zeros((5, 4, 4), dtype=np.float32)
    raster_data[2] = 0.6
    raster_data[3] = 0.2
    raster_data[4] = 0.8

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=4,
        width=4,
        count=5,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(74.0, 17.0, 0.001, 0.001),
        nodata=-9999.0,
    ) as dst:
        dst.write(raster_data)

    request = AnalysisRequest(
        analysis_id="test-001",
        polygon={
            "type": "Polygon",
            "coordinates": [[
                [74.000, 16.996],
                [74.004, 16.996],
                [74.004, 17.000],
                [74.000, 17.000],
                [74.000, 16.996],
            ]],
        },
        dataset_specs=[
            {
                "dataset_id": "test-dataset",
                "path": str(raster_path),
                "bands": {"red": 4, "nir": 5, "green": 3},
                "band_scaling": {
                    "red": {"scale": 1.0, "offset": 0.0},
                    "nir": {"scale": 1.0, "offset": 0.0},
                    "green": {"scale": 1.0, "offset": 0.0},
                },
            }
        ],
        indicators=["ndvi"],
    )

    result = run_analysis(request, output_dir)

    assert isinstance(result, GeospatialResult)
    assert np.isclose(result.metrics["mean_ndvi"], 0.6)
    assert len(result.artifacts) == 1

    output_raster = output_dir / result.artifacts[0].relative_path
    assert output_raster.exists()

    with rasterio.open(output_raster) as src:
        output = src.read(1, masked=True)
        assert src.crs.to_string() == "EPSG:4326"
        assert np.isclose(float(output.mean()), 0.6)
def test_pipeline_compares_two_datasets(tmp_path):
    output_dir = tmp_path / "output"
    dataset_specs = []

    # Create two synthetic datasets with different NDVI values.
    for dataset_id, nir_value in [
        ("dataset-2020", 0.8),
        ("dataset-2023", 0.6),
    ]:
        raster_path = tmp_path / f"{dataset_id}.tif"

        raster_data = np.zeros((5, 4, 4), dtype=np.float32)
        raster_data[2] = 0.6  # Green
        raster_data[3] = 0.2  # Red
        raster_data[4] = nir_value  # NIR

        with rasterio.open(
            raster_path,
            "w",
            driver="GTiff",
            height=4,
            width=4,
            count=5,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(74.0, 17.0, 0.001, 0.001),
            nodata=-9999.0,
        ) as dst:
            dst.write(raster_data)

        dataset_specs.append(
            {
                "dataset_id": dataset_id,
                "path": str(raster_path),
                "bands": {"red": 4, "nir": 5, "green": 3},
                "band_scaling": {
                    "red": {"scale": 1.0, "offset": 0.0},
                    "nir": {"scale": 1.0, "offset": 0.0},
                    "green": {"scale": 1.0, "offset": 0.0},
                },
            }
        )

    request = AnalysisRequest(
        analysis_id="comparison-test",
        polygon={
            "type": "Polygon",
            "coordinates": [[
                [74.000, 16.996],
                [74.004, 16.996],
                [74.004, 17.000],
                [74.000, 17.000],
                [74.000, 16.996],
            ]],
        },
        dataset_specs=dataset_specs,
        indicators=["ndvi"],
    )

    result = run_analysis(request, output_dir)

    assert isinstance(result, GeospatialResult)
    assert len(result.series) == 2
    assert len(result.comparisons) == 1

    comparison = result.comparisons[0]

    assert comparison["from_dataset"] == "dataset-2020"
    assert comparison["to_dataset"] == "dataset-2023"
    assert "mean_ndvi" in comparison["indicators"]
    assert comparison["indicators"]["mean_ndvi"]["absolute_change"] < 0