from geospatial.contracts import AnalysisRequest
from geospatial.pipeline import run_analysis


def test_pipeline_accepts_dataset_band_mapping(tmp_path):
    request = AnalysisRequest(
        analysis_id="test-001",
        polygon={"type": "Polygon"},
        dataset_specs=[
            {
                "dataset_id": "test-dataset",
                "bands": {
                    "red": 4,
                    "nir": 5,
                    "green": 3,
                },
            }
        ],
        indicators=["ndvi"],
    )

    result = run_analysis(request, tmp_path)

    assert "metrics" in result
    assert "statistics" in result
    assert "mean_ndvi" in result["metrics"]
    assert "mean_ndwi" in result["metrics"]