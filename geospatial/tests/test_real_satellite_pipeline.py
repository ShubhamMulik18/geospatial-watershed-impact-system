from pathlib import Path
from PIL import Image
import pytest

from geospatial.contracts import AnalysisRequest, GeospatialResult
from geospatial.pipeline import run_analysis


def test_real_sentinel2_multi_year_analysis(tmp_path: Path):
    sat_2020 = Path("sample_data/satellite/2020")
    sat_2023 = Path("sample_data/satellite/2023")

    if not sat_2020.exists() or not sat_2023.exists():
        pytest.skip("Sample satellite data directories not found")

    output_dir = tmp_path / "analysis_output"

    polygon = {
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
    }

    request = AnalysisRequest(
        analysis_id="real-sat-test-001",
        polygon=polygon,
        dataset_specs=[
            {
                "dataset_id": "sentinel2-2020",
                "path": str(sat_2020.resolve()),
            },
            {
                "dataset_id": "sentinel2-2023",
                "path": str(sat_2023.resolve()),
            },
        ],
        indicators=["ndvi", "water"],
        processing_config={"generate_previews": True, "water_threshold": 0.0},
    )

    result = run_analysis(request, output_dir)

    assert isinstance(result, GeospatialResult)

    # 1. Environmental metrics calculated
    assert "ndvi_before" in result.metrics
    assert "ndvi_after" in result.metrics
    assert "ndvi_change" in result.metrics
    assert -1.0 <= result.metrics["ndvi_before"] <= 1.0
    assert -1.0 <= result.metrics["ndvi_after"] <= 1.0

    assert "water_before_hectares" in result.metrics
    assert "water_after_hectares" in result.metrics
    assert result.metrics["water_before_hectares"] >= 0.0

    # Verify water area is honestly derived and does not falsely equate to the entire common valid area
    assert result.metrics["water_before_hectares"] < result.quality["common_valid_hectares"]
    assert result.metrics["mean_mndwi"] < 0.5
    assert result.metrics["water_before_hectares"] == pytest.approx(0.37, abs=0.05)
    assert result.metrics["water_after_hectares"] == pytest.approx(0.64, abs=0.05)

    # 2. Quality and cloud mask handling
    assert result.quality["cloud_mask_available"]["sentinel2-2020"] is True
    assert result.quality["cloud_mask_available"]["sentinel2-2023"] is True
    assert result.quality["common_valid_fraction"] > 0.5
    assert result.quality["aoi_hectares"] > 0.0

    # 3. Series and Comparisons
    assert len(result.series) == 2
    assert result.series[0]["dataset_id"] == "sentinel2-2020"
    assert result.series[1]["dataset_id"] == "sentinel2-2023"
    assert len(result.comparisons) == 1

    # 4. Artifacts generated (2 indicators * 2 formats (GeoTIFF + PNG preview) * 2 datasets = 8 artifacts)
    assert len(result.artifacts) == 8

    # Verify previews are readable PNG images
    preview_artifacts = [a for a in result.artifacts if a.kind.startswith("preview_")]
    assert len(preview_artifacts) == 4
    for a in preview_artifacts:
        p_path = output_dir / a.relative_path
        assert p_path.is_file()
        with Image.open(p_path) as img:
            assert img.mode == "RGBA"
            assert img.size[0] > 0
            assert img.size[1] > 0

