from pathlib import Path
import sys
from typing import Any, Callable

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.integrations.geospatial.base import (
    AnalysisResult,
    DatasetInspection,
    GeospatialAdapter,
)


class ProductionGeospatialAdapter(GeospatialAdapter):
    """Production adapter calling the authoritative geospatial pipeline."""

    def inspect_dataset(
        self,
        dataset_spec: dict[str, Any],
    ) -> DatasetInspection:
        from geospatial.raster_processing.inspect import inspect_dataset

        path = dataset_spec.get("path") or dataset_spec.get("raster_path")
        if not path:
            return DatasetInspection(
                dataset_id=str(dataset_spec.get("dataset_id", "")),
                compatible=False,
                metadata={},
                errors=("Dataset path is missing.",),
            )

        p = Path(path)
        if not p.is_absolute() and not p.exists():
            if (_repo_root / p).exists():
                path = str(_repo_root / p)

        try:
            meta = inspect_dataset(Path(path))
            return DatasetInspection(
                dataset_id=str(dataset_spec.get("dataset_id", "")),
                compatible=True,
                metadata=meta,
                errors=(),
            )
        except Exception as exc:
            return DatasetInspection(
                dataset_id=str(dataset_spec.get("dataset_id", "")),
                compatible=False,
                metadata={},
                errors=(str(exc),),
            )

    def run_analysis(
        self,
        request: dict[str, Any],
        output_dir: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> AnalysisResult:
        from geospatial.contracts import AnalysisRequest
        from geospatial.pipeline import run_analysis as run_geospatial_pipeline

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        polygon = request["polygon"]
        if not isinstance(polygon, dict) and hasattr(polygon, "__geo_interface__"):
            polygon = polygon.__geo_interface__

        dataset_specs = (
            request.get("dataset_specs")
            or request.get("datasets")
            or []
        )
        if not dataset_specs:
            raise ValueError("No dataset specifications provided for analysis.")

        resolved_specs = []
        for spec in dataset_specs:
            resolved_spec = dict(spec)

            if not resolved_spec.get("path"):
                meta = resolved_spec.get("metadata") or {}
                if meta.get("path"):
                    resolved_spec["path"] = meta["path"]
                elif meta.get("raster_path"):
                    resolved_spec["path"] = meta["raster_path"]

            if resolved_spec.get("path"):
                p = Path(resolved_spec["path"])
                if not p.is_absolute() and not p.exists():
                    if (_repo_root / p).exists():
                        resolved_spec["path"] = str(_repo_root / p)

            manifest = (
                resolved_spec.get("manifest")
                or resolved_spec.get("metadata", {}).get("manifest")
                or {}
            )

            if not isinstance(resolved_spec.get("bands"), dict):
                if isinstance(manifest.get("bands"), dict):
                    resolved_spec["bands"] = manifest["bands"]
                elif isinstance(
                    resolved_spec.get("metadata", {}).get("bands"), dict
                ):
                    resolved_spec["bands"] = resolved_spec["metadata"]["bands"]

            if "band_scaling" not in resolved_spec and "band_scaling" in manifest:
                resolved_spec["band_scaling"] = manifest["band_scaling"]

            resolved_specs.append(resolved_spec)

        proc_cfg = dict(request.get("processing_config", {}))
        proc_cfg.setdefault("generate_previews", True)

        analysis_req = AnalysisRequest(
            analysis_id=str(request["analysis_id"]),
            polygon=polygon,
            dataset_specs=resolved_specs,
            indicators=list(request["indicators"]),
            processing_config=proc_cfg,
        )

        geo_progress_callback = None
        if progress_callback is not None:
            def geo_progress_callback(pct: Any) -> None:
                progress_callback(f"processing_{pct}%")

        geo_result = run_geospatial_pipeline(
            request=analysis_req,
            output_dir=output_dir,
            progress_callback=geo_progress_callback,
        )

        artifacts_data = [
            {
                "artifact_id": artifact.artifact_id,
                "kind": artifact.kind,
                "relative_path": artifact.relative_path,
                "dataset_id": artifact.dataset_id,
            }
            for artifact in geo_result.artifacts
        ]

        return AnalysisResult(
            metrics=geo_result.metrics,
            series=geo_result.series,
            comparisons=geo_result.comparisons,
            quality=geo_result.quality,
            warnings=list(geo_result.warnings),
            provenance=dict(geo_result.provenance),
            artifacts=artifacts_data,
        )

