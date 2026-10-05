from pathlib import Path

from app.integrations.geospatial.adapter import DevelopmentGeospatialAdapter


def test_development_geospatial_adapter_inspects_dataset() -> None:
    spec = {
        "dataset_id": "dataset-001",
        "display_name": "Development Dataset",
        "crs": "EPSG:32643",
    }

    result = DevelopmentGeospatialAdapter().inspect_dataset(spec)

    assert result.dataset_id == "dataset-001"
    assert result.compatible is True
    assert result.metadata == spec
    assert result.errors == ()


def test_development_geospatial_adapter_returns_explicit_mock_result(
    tmp_path: Path,
) -> None:
    stages: list[str] = []

    result = DevelopmentGeospatialAdapter().run_analysis(
        request={"analysis_id": "analysis-001"},
        output_dir=tmp_path,
        progress_callback=stages.append,
    )

    assert stages == ["processing"]
    assert tmp_path.is_dir()
    assert result.metrics == {}
    assert result.series == []
    assert result.comparisons == []
    assert result.quality == {}
    assert result.artifacts == []
    assert result.provenance == {"adapter": "development-mock-v1"}
    assert result.warnings == [
        "Development geospatial adapter does not perform scientific analysis."
    ]
