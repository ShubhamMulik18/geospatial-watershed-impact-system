from pathlib import Path
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.ai.adapter import DevelopmentAIAdapter
from app.integrations.ai.base import AIAdapter
from app.integrations.geospatial.adapter import DevelopmentGeospatialAdapter
from app.integrations.geospatial.base import GeospatialAdapter
from app.repositories.analysis_worker_repository import AnalysisWorkerRepository


class AnalysisWorker:
    """Polls and processes analysis jobs using backend adapters."""

    def __init__(
        self,
        db: Session,
        repository: AnalysisWorkerRepository | None = None,
        ai_adapter: AIAdapter | None = None,
        geospatial_adapter: GeospatialAdapter | None = None,
    ) -> None:
        settings = get_settings()

        self.db = db
        self.repository = repository or AnalysisWorkerRepository()
        self.ai_adapter = ai_adapter or DevelopmentAIAdapter()
        self.geospatial_adapter = (
            geospatial_adapter or DevelopmentGeospatialAdapter()
        )

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

    @staticmethod
    def _resolve_photo_path(safe_path: str) -> Path:
        """Resolve a persisted photo path and require the file to exist."""
        photo_path = Path(safe_path).resolve()

        if not photo_path.is_file():
            raise FileNotFoundError(
                f"Stored analysis photo is missing: {safe_path}"
            )

        return photo_path

    def run_prediction(self, analysis):
        """Run AI prediction for the analysis photo."""
        photo_path = self._resolve_photo_path(analysis.photo.safe_path)
        return self.ai_adapter.predict(photo_path)

    def process_job(self, analysis) -> None:
        """Process one claimed analysis job through the adapter pipeline."""
        try:
            self.start_job(analysis)

            self.run_prediction(analysis)

            output_dir = self.artifact_storage_root / str(analysis.id)

            request = {
                "analysis_id": str(analysis.id),
                "polygon": analysis.polygon,
                "indicators": analysis.indicators,
                "datasets": [
                    {
                        "dataset_id": str(link.dataset_id),
                        "metadata": link.dataset_metadata_snapshot,
                        "sha256": link.dataset_sha256,
                    }
                    for link in sorted(
                        analysis.dataset_links,
                        key=lambda link: link.sequence,
                    )
                ],
            }

            progress_callback = self._build_progress_callback(analysis)

            self.geospatial_adapter.run_analysis(
                request=request,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

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