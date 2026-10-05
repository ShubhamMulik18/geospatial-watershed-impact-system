from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisStatus


class AnalysisWorkerRepository:
    """Database operations used by the analysis worker."""

    def claim_next_analysis(
        self,
        db: Session,
        lease_seconds: int,
    ) -> Analysis | None:
        now = datetime.now(timezone.utc)

        analysis = db.execute(
            select(Analysis)
            .where(Analysis.status == AnalysisStatus.CREATED.value)
            .order_by(Analysis.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).scalar_one_or_none()

        if analysis is None:
            return None

        analysis.status = AnalysisStatus.QUEUED.value
        analysis.worker_heartbeat_at = now
        analysis.worker_lease_expires_at = now + timedelta(
            seconds=lease_seconds
        )

        db.flush()
        return analysis

    def get_analysis(
        self,
        db: Session,
        analysis_id: uuid.UUID,
    ) -> Analysis | None:
        return db.get(Analysis, analysis_id)

    def recover_expired_analyses(self, db: Session) -> int:
        """Mark expired queued/running analyses as failed."""
        now = datetime.now(timezone.utc)

        analyses = db.execute(
            select(Analysis)
            .where(
                Analysis.status.in_(
                    [
                        AnalysisStatus.QUEUED.value,
                        AnalysisStatus.RUNNING.value,
                    ]
                ),
                Analysis.worker_lease_expires_at.is_not(None),
                Analysis.worker_lease_expires_at < now,
            )
            .with_for_update(skip_locked=True)
        ).scalars().all()

        for analysis in analyses:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error = (
                "Worker lease expired. The analysis was interrupted; "
                "please create a new analysis to retry."
            )
            analysis.worker_heartbeat_at = now

        db.flush()
        return len(analyses)

    def renew_lease(
        self,
        db: Session,
        analysis_id: uuid.UUID,
        lease_seconds: int,
    ) -> bool:
        """Extend the lease for a currently running analysis."""
        analysis = db.execute(
            select(Analysis)
            .where(
                Analysis.id == analysis_id,
                Analysis.status == AnalysisStatus.RUNNING.value,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if analysis is None:
            return False

        now = datetime.now(timezone.utc)

        analysis.worker_heartbeat_at = now
        analysis.worker_lease_expires_at = now + timedelta(
            seconds=lease_seconds
        )

        db.flush()
        return True
