from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class DatasetInspection:
    dataset_id: str
    compatible: bool
    metadata: dict[str, Any]
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisResult:
    metrics: dict[str, Any]
    series: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    quality: dict[str, Any]
    warnings: list[str]
    provenance: dict[str, Any]
    artifacts: list[dict[str, Any]]


class GeospatialAdapter(ABC):
    """Backend-facing contract for scientific geospatial processing."""

    @abstractmethod
    def inspect_dataset(self, dataset_spec: dict[str, Any]) -> DatasetInspection:
        """Inspect dataset compatibility without running the full analysis."""
        raise NotImplementedError

    @abstractmethod
    def run_analysis(
        self,
        request: dict[str, Any],
        output_dir: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> AnalysisResult:
        """Run scientific processing using resolved backend-owned inputs."""
        raise NotImplementedError
