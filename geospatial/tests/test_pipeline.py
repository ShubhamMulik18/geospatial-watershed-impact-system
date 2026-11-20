from datetime import date
import numpy as np
import pytest
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
                "acquisition_date": "2020-01-01",
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


def test_pipeline_order_invariance_chronological_sort(tmp_path):
    """
    Regardless of input order ([2023, 2020] vs [2020, 2023]), datasets
    must always be sorted chronologically so earliest is Before and latest is After.
    """
    output_dir = tmp_path / "output_inv"

    specs = {}
    for dataset_id, nir_val, acq_date in [
        ("dataset-2020", 0.8, "2020-05-15"),
        ("dataset-2023", 0.6, "2023-11-20"),
    ]:
        raster_path = tmp_path / f"{dataset_id}.tif"
        raster_data = np.zeros((5, 4, 4), dtype=np.float32)
        raster_data[2] = 0.6
        raster_data[3] = 0.2
        raster_data[4] = nir_val

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

        specs[dataset_id] = {
            "dataset_id": dataset_id,
            "acquisition_date": acq_date,
            "path": str(raster_path),
            "bands": {"red": 4, "nir": 5, "green": 3},
            "band_scaling": {
                "red": {"scale": 1.0, "offset": 0.0},
                "nir": {"scale": 1.0, "offset": 0.0},
                "green": {"scale": 1.0, "offset": 0.0},
            },
        }

    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [74.000, 16.996],
            [74.004, 16.996],
            [74.004, 17.000],
            [74.000, 17.000],
            [74.000, 16.996],
        ]],
    }

    # Pass in REVERSED order (2023 first, then 2020)
    req_reversed = AnalysisRequest(
        analysis_id="test-reversed",
        polygon=polygon,
        dataset_specs=[specs["dataset-2023"], specs["dataset-2020"]],
        indicators=["ndvi"],
    )
    result_reversed = run_analysis(req_reversed, output_dir / "rev")

    # Pass in NORMAL order (2020 first, then 2023)
    req_normal = AnalysisRequest(
        analysis_id="test-normal",
        polygon=polygon,
        dataset_specs=[specs["dataset-2020"], specs["dataset-2023"]],
        indicators=["ndvi"],
    )
    result_normal = run_analysis(req_normal, output_dir / "norm")

    # Both must have identical series and metrics order
    assert result_reversed.series[0]["dataset_id"] == "dataset-2020"
    assert result_reversed.series[1]["dataset_id"] == "dataset-2023"
    assert result_reversed.metrics["ndvi_before"] == result_normal.metrics["ndvi_before"]
    assert result_reversed.metrics["ndvi_after"] == result_normal.metrics["ndvi_after"]
    assert result_reversed.metrics["ndvi_change"] == result_normal.metrics["ndvi_change"]
    # 2020 (NIR 0.8) -> NDVI 0.6, 2023 (NIR 0.6) -> NDVI 0.5; change is negative (0.5 - 0.6 = -0.1)
    assert result_reversed.metrics["ndvi_change"] == pytest.approx(-0.1)


def test_pipeline_rejects_missing_acquisition_date(tmp_path):
    """
    Datasets without an acquisition date in metadata, path, or id must be rejected with ValueError.
    """
    raster_path = tmp_path / "unknown.tif"
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
        dst.write(np.zeros((5, 4, 4), dtype=np.float32))

    request = AnalysisRequest(
        analysis_id="invalid-date-test",
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
                "dataset_id": "no-date-dataset",
                "path": str(raster_path),
                "bands": {"red": 4, "nir": 5, "green": 3},
            }
        ],
        indicators=["ndvi"],
    )

    with pytest.raises(ValueError, match="does not contain a valid or parseable acquisition date"):
        run_analysis(request, tmp_path / "err_out")
