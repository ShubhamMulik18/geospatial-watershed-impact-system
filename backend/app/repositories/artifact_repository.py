import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact


class ArtifactRepository:
    """Database operations for analysis artifacts."""

    def add(
        self,
        db: Session,
        *,
        analysis_id: uuid.UUID,
        kind: str,
        safe_relative_path: str,
        mime_type: str,
        sha256: str,
        byte_size: int,
        metadata: dict | None = None,
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            kind=kind,
            safe_relative_path=safe_relative_path,
            mime_type=mime_type,
            sha256=sha256,
            byte_size=byte_size,
            metadata_json=metadata,
        )

        db.add(artifact)
        db.flush()

        return artifact

    def get_for_analysis(
        self,
        db: Session,
        *,
        analysis_id: uuid.UUID,
        artifact_id: uuid.UUID,
    ) -> Artifact | None:
        return db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.analysis_id == analysis_id,
            )
        ).scalar_one_or_none()

    def list_for_analysis(
        self,
        db: Session,
        *,
        analysis_id: uuid.UUID,
    ) -> list[Artifact]:
        return list(
            db.execute(
                select(Artifact)
                .where(Artifact.analysis_id == analysis_id)
                .order_by(Artifact.created_at, Artifact.id)
            )
            .scalars()
            .all()
        )