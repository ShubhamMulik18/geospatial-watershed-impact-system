import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.artifact_repository import ArtifactRepository
from app.storage.artifact_storage import ArtifactStorage


class ArtifactService:
    """Application service for registered analysis artifacts."""

    def __init__(
        self,
        db: Session,
        storage_root: Path,
        repository: ArtifactRepository | None = None,
    ) -> None:
        self.db = db
        self.repository = repository or ArtifactRepository()
        self.storage = ArtifactStorage(storage_root)

    def get_artifact_file(
        self,
        *,
        analysis_id: uuid.UUID,
        artifact_id: uuid.UUID,
    ) -> tuple[Path, str, str]:
        """Return a registered artifact file and its serving metadata."""
        artifact = self.repository.get_for_analysis(
            db=self.db,
            analysis_id=analysis_id,
            artifact_id=artifact_id,
        )

        if artifact is None:
            raise NotFoundError("Artifact not found.")

        path = self.storage.ensure_exists(artifact.safe_relative_path)

        return path, artifact.mime_type, artifact.kind