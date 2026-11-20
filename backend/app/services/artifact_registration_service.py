import mimetypes
from pathlib import Path
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.models.artifact import Artifact
from app.repositories.artifact_repository import ArtifactRepository
from app.utils.file_hash import calculate_file_sha256


class ArtifactRegistrationService:
    """Register persisted analysis output files into the database."""

    def __init__(
        self,
        db: Session,
        storage_root: Path,
        repository: ArtifactRepository | None = None,
    ) -> None:
        self.db = db
        self.storage_root = Path(storage_root).resolve()
        self.repository = repository or ArtifactRepository()

    def register_artifacts(
        self,
        *,
        analysis_id: uuid.UUID | str,
        output_dir: Path,
        artifacts: list[Any],
    ) -> list[Artifact]:
        """Validate generated artifact files and register them in the artifacts table."""
        if not artifacts:
            return []

        try:
            analysis_uuid = (
                analysis_id
                if isinstance(analysis_id, uuid.UUID)
                else uuid.UUID(str(analysis_id))
            )
        except ValueError:
            analysis_uuid = analysis_id

        expected_dir = (self.storage_root / str(analysis_id)).resolve()
        actual_dir = Path(output_dir).resolve()

        if actual_dir != expected_dir:
            raise ValueError(
                f"Output directory '{actual_dir}' must match analysis storage "
                f"directory '{expected_dir}'."
            )

        registered: list[Artifact] = []

        for item in artifacts:
            if isinstance(item, dict):
                kind = item.get("kind", "")
                rel_path = item.get("relative_path", "")
                dataset_id = item.get("dataset_id")
                metadata = dict(item.get("metadata") or {})
            else:
                kind = getattr(item, "kind", "")
                rel_path = getattr(item, "relative_path", "")
                dataset_id = getattr(item, "dataset_id", None)
                metadata = dict(getattr(item, "metadata", None) or {})

            if not rel_path:
                continue

            rel_path_obj = Path(rel_path)
            if rel_path_obj.is_absolute():
                raise ValueError("Artifact path escapes output directory.")

            artifact_path = (actual_dir / rel_path_obj).resolve()

            try:
                artifact_path.relative_to(actual_dir)
            except ValueError as exc:
                raise ValueError("Artifact path escapes output directory.") from exc

            if not artifact_path.is_file():
                raise FileNotFoundError(
                    f"Artifact file not found: {artifact_path}"
                )

            byte_size = artifact_path.stat().st_size
            sha256 = calculate_file_sha256(artifact_path)

            extension = artifact_path.suffix.lower()
            mime_type_map = {
                ".tif": "image/tiff",
                ".tiff": "image/tiff",
                ".jp2": "image/jp2",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".pdf": "application/pdf",
                ".json": "application/json",
            }
            mime_type = mime_type_map.get(
                extension,
                mimetypes.guess_type(artifact_path)[0] or "application/octet-stream",
            )

            safe_relative_path = f"{analysis_id}/{rel_path_obj.as_posix()}"

            if dataset_id is not None and "dataset_id" not in metadata:
                metadata["dataset_id"] = str(dataset_id)

            artifact = self.repository.add(
                db=self.db,
                analysis_id=analysis_uuid,
                kind=kind,
                safe_relative_path=safe_relative_path,
                mime_type=mime_type,
                sha256=sha256,
                byte_size=byte_size,
                metadata=metadata or None,
            )
            registered.append(artifact)

        return registered

