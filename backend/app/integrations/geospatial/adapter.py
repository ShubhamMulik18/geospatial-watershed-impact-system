from pathlib import Path
from typing import Any, Callable

from app.integrations.geospatial.base import (
    AnalysisResult,
    DatasetInspection,
    GeospatialAdapter,
)


class DevelopmentGeospatialAdapter(GeospatialAdapter):
    """Explicit development adapter; does not perform scientific analysis."""

    def inspect_dataset(
        self,
        dataset_spec: dict[str, Any],
    ) -> DatasetInspection:
        dataset_id = str(dataset_spec.get("dataset_id", ""))

        return DatasetInspection(
            dataset_id=dataset_id,
            compatible=True,
            metadata=dict(dataset_spec),
            errors=(),
        )

    def run_analysis(
        self,
        request: dict[str, Any],
        output_dir: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> AnalysisResult:
        if progress_callback is not None:
            progress_callback("processing")

        output_dir.mkdir(parents=True, exist_ok=True)

        return AnalysisResult(
            metrics={},
            series=[],
            comparisons=[],
            quality={},
            warnings=[
                "Development geospatial adapter does not perform scientific analysis."
            ],
            provenance={
                "adapter": "development-mock-v1",
            },
            artifacts=[],
        )
