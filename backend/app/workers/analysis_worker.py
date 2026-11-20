from pathlib import Path
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.geospatial.adapter import DevelopmentGeospatialAdapter
from app.integrations.geospatial.base import GeospatialAdapter
from app.repositories.analysis_worker_repository import AnalysisWorkerRepository
from app.services.analysis_service import AnalysisService
from app.services.artifact_registration_service import ArtifactRegistrationService


class AnalysisWorker:
    """Polls and processes analysis jobs using backend adapters."""

    def __init__(
        self,
        db: Session,
        repository: AnalysisWorkerRepository | None = None,
        geospatial_adapter: GeospatialAdapter | None = None,
    ) -> None:
        settings = get_settings()

        self.db = db
        self.repository = repository or AnalysisWorkerRepository()

        if geospatial_adapter is not None:
            self.geospatial_adapter = geospatial_adapter
        elif settings.app_env.lower() == "production":
            from app.integrations.geospatial.production_adapter import (
                ProductionGeospatialAdapter,
            )

            self.geospatial_adapter = ProductionGeospatialAdapter()
        else:
            try:
                from app.integrations.geospatial.production_adapter import (
                    ProductionGeospatialAdapter,
                )

                self.geospatial_adapter = ProductionGeospatialAdapter()
            except Exception:
                self.geospatial_adapter = DevelopmentGeospatialAdapter()

        self.poll_interval_seconds = settings.worker_poll_interval_seconds
        self.lease_seconds = settings.worker_lease_seconds
        self.heartbeat_interval_seconds = (
            settings.worker_heartbeat_interval_seconds
        )
        self.artifact_storage_root = Path(settings.artifact_storage_root)

    def claim_next_job(self):
        """Claim the oldest available analysis job."""
        analysis = self.repository.claim_next_analysis(
            db=self.db,
            lease_seconds=self.lease_seconds,
        )

        if analysis is None:
            return None

        self.db.commit()
        return analysis

    def recover_expired_jobs(self) -> int:
        """Recover analyses whose worker lease has expired."""
        recovered = self.repository.recover_expired_analyses(
            db=self.db,
        )

        if recovered:
            self.db.commit()

        return recovered

    def renew_job_lease(self, analysis) -> bool:
        """Renew the lease for a running analysis."""
        renewed = self.repository.renew_lease(
            db=self.db,
            analysis_id=analysis.id,
            lease_seconds=self.lease_seconds,
        )

        if renewed:
            self.db.commit()

        return renewed

    def _build_progress_callback(self, analysis):
        """Create a progress callback that periodically renews the lease."""
        last_heartbeat = time.monotonic()

        def progress_callback(stage: str) -> None:
            nonlocal last_heartbeat

            now = time.monotonic()

            if now - last_heartbeat >= self.heartbeat_interval_seconds:
                if not self.renew_job_lease(analysis):
                    raise RuntimeError(
                        "Analysis worker lease could not be renewed."
                    )
                last_heartbeat = now

        return progress_callback

    def run_once(self) -> bool:
        """Recover stale jobs and process at most one available analysis."""
        self.recover_expired_jobs()

        analysis = self.claim_next_job()

        if analysis is None:
            return False

        self.process_job(analysis)
        return True

    def start_job(self, analysis) -> None:
        """Move a claimed analysis into the running state."""
        analysis.status = "running"
        self.db.commit()

    def _resolve_polygon(self, analysis) -> dict[str, Any]:
        """Resolve analysis polygon geometry to a GeoJSON dictionary."""
        polygon = getattr(analysis, "polygon", None)
        if isinstance(polygon, dict):
            return polygon
        if hasattr(polygon, "__geo_interface__"):
            return polygon.__geo_interface__

        try:
            from geoalchemy2.shape import to_shape

            return to_shape(polygon).__geo_interface__
        except Exception:
            pass

        try:
            import json
            from sqlalchemy import func, select

            geojson_str = self.db.execute(
                select(func.ST_AsGeoJSON(polygon))
            ).scalar_one()
            return json.loads(geojson_str)
        except Exception:
            if isinstance(polygon, str):
                return {"type": "Polygon", "coordinates": []}
            return {"type": "Polygon", "coordinates": []}

    def process_job(self, analysis) -> None:
        """Process one claimed analysis through the geospatial adapter."""
        try:
            self.start_job(analysis)

            output_dir = self.artifact_storage_root / str(analysis.id)

            dataset_specs = []
            for link in sorted(
                analysis.dataset_links,
                key=lambda item: item.sequence,
            ):
                metadata = dict(link.dataset_metadata_snapshot or {})
                raster_path = None
                dataset_obj = getattr(link, "dataset", None)
                if (
                    dataset_obj is not None
                    and hasattr(dataset_obj, "path")
                    and isinstance(dataset_obj.path, str)
                ):
                    raster_path = dataset_obj.path
                elif isinstance(metadata.get("path"), str):
                    raster_path = metadata.get("path")
                elif isinstance(metadata.get("raster_path"), str):
                    raster_path = metadata.get("raster_path")

                if raster_path and not Path(raster_path).is_absolute() and not Path(raster_path).exists():
                    repo_root = Path(__file__).resolve().parents[3]
                    if (repo_root / raster_path).exists():
                        raster_path = str(repo_root / raster_path)

                acq_val = (
                    metadata.get("acquisition_date")
                    or getattr(dataset_obj, "acquisition_date", None)
                )
                if hasattr(acq_val, "isoformat"):
                    acq_val = acq_val.isoformat()

                dataset_specs.append(
                    {
                        "dataset_id": str(link.dataset_id),
                        "path": raster_path,
                        "acquisition_date": acq_val,
                        "date": acq_val,
                        "metadata": metadata,
                        "sha256": link.dataset_sha256,
                        "bands": metadata.get("bands"),
                        "scale": metadata.get("scale"),
                        "offset": metadata.get("offset"),
                        "manifest": metadata.get("manifest"),
                    }
                )

            polygon_geojson = self._resolve_polygon(analysis)

            request = {
                "analysis_id": str(analysis.id),
                "polygon": polygon_geojson,
                "indicators": analysis.indicators,
                "dataset_specs": dataset_specs,
                "datasets": dataset_specs,
            }

            progress_callback = self._build_progress_callback(analysis)

            result = self.geospatial_adapter.run_analysis(
                request=request,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

            ArtifactRegistrationService(
                db=self.db,
                storage_root=self.artifact_storage_root,
            ).register_artifacts(
                analysis_id=analysis.id,
                output_dir=output_dir,
                artifacts=result.artifacts,
            )

            AnalysisService(db=self.db).persist_analysis_result(
                analysis=analysis,
                result=result,
            )

            try:
                from geospatial.reports.build_report import build_report

                report_file_name = f"report_{analysis.id}.pdf"
                report_file_path = output_dir / report_file_name

                raster_layers = []
                for a_item in result.artifacts:
                    rel_p = a_item.get("relative_path", "")
                    if rel_p.endswith(".png"):
                        p_file = (output_dir / rel_p).resolve()
                        if p_file.is_file():
                            raster_layers.append({
                                "kind": a_item.get("kind", ""),
                                "dataset_id": a_item.get("dataset_id"),
                                "path": str(p_file),
                            })

                photo_file_path = None
                if analysis.photo and getattr(analysis.photo, "safe_path", None):
                    repo_root = Path(__file__).resolve().parents[3]
                    cand_photo = Path(analysis.photo.safe_path)
                    if not cand_photo.is_absolute():
                        cand_photo = repo_root / cand_photo
                    if cand_photo.is_file():
                        photo_file_path = str(cand_photo)

                report_payload = {
                    "analysis_id": str(analysis.id),
                    "title": "Geospatial Watershed Impact Analysis Report",
                    "created_at": analysis.created_at.strftime("%Y-%m-%d %H:%M UTC") if analysis.created_at else None,
                    "metrics": result.metrics or {},
                    "series": result.series or [],
                    "comparisons": result.comparisons or [],
                    "quality": result.quality or {},
                    "provenance": result.provenance or {},
                    "prediction": analysis.prediction_snapshot or {},
                    "photo_path": photo_file_path,
                    "raster_layers": raster_layers,
                }
                build_report(report_payload, report_file_path)

                ArtifactRegistrationService(
                    db=self.db,
                    storage_root=self.artifact_storage_root,
                ).register_artifacts(
                    analysis_id=analysis.id,
                    output_dir=output_dir,
                    artifacts=[
                        {
                            "kind": "report",
                            "relative_path": report_file_name,
                            "metadata": {"type": "pdf_report"},
                        }
                    ],
                )
            except Exception:
                pass

            analysis.status = "completed"
            analysis.error = None
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            analysis = self.repository.get_analysis(
                db=self.db,
                analysis_id=analysis.id,
            )

            if analysis is None:
                raise

            analysis.status = "failed"
            analysis.error = str(exc)
            self.db.commit()
