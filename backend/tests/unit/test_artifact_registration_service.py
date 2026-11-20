import hashlib
from pathlib import Path
from unittest.mock import MagicMock
import uuid

import pytest

from app.services.artifact_registration_service import ArtifactRegistrationService


def _make_service(tmp_path: Path):
    db = MagicMock()
    storage_root = tmp_path / "artifacts"
    storage_root.mkdir(parents=True, exist_ok=True)
    repository = MagicMock()
    service = ArtifactRegistrationService(
        db=db,
        storage_root=storage_root,
        repository=repository,
    )
    analysis_id = uuid.uuid4()
    output_dir = storage_root / str(analysis_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    return service, analysis_id, output_dir, db, repository


def test_register_artifact_records_hash_size_and_relative_path(tmp_path: Path) -> None:
    service, analysis_id, output_dir, db, repository = _make_service(tmp_path)

    raster_file = output_dir / "ndvi.tif"
    content = b"fake-geotiff-bytes"
    raster_file.write_bytes(content)

    mock_artifact = MagicMock()
    repository.add.return_value = mock_artifact

    result = service.register_artifacts(
        analysis_id=analysis_id,
        output_dir=output_dir,
        artifacts=[
            {
                "kind": "ndvi_raster",
                "relative_path": "ndvi.tif",
                "dataset_id": "dataset-1",
            }
        ],
    )

    assert result == [mock_artifact]
    repository.add.assert_called_once()
    _, kwargs = repository.add.call_args
    assert kwargs["analysis_id"] == analysis_id
    assert kwargs["kind"] == "ndvi_raster"
    assert kwargs["safe_relative_path"] == f"{analysis_id}/ndvi.tif"
    assert kwargs["mime_type"] == "image/tiff"
    assert kwargs["sha256"] == hashlib.sha256(content).hexdigest()
    assert kwargs["byte_size"] == len(content)
    assert kwargs["metadata"] == {"dataset_id": "dataset-1"}
    db.commit.assert_not_called()


def test_register_artifact_rejects_missing_file(tmp_path: Path) -> None:
    service, analysis_id, output_dir, db, repository = _make_service(tmp_path)

    with pytest.raises(FileNotFoundError):
        service.register_artifacts(
            analysis_id=analysis_id,
            output_dir=output_dir,
            artifacts=[
                {
                    "kind": "ndvi_raster",
                    "relative_path": "missing.tif",
                }
            ],
        )

    repository.add.assert_not_called()


def test_register_artifact_rejects_path_traversal(tmp_path: Path) -> None:
    service, analysis_id, output_dir, db, repository = _make_service(tmp_path)

    with pytest.raises(ValueError, match="escapes"):
        service.register_artifacts(
            analysis_id=analysis_id,
            output_dir=output_dir,
            artifacts=[
                {
                    "kind": "ndvi_raster",
                    "relative_path": "../outside.tif",
                }
            ],
        )

    repository.add.assert_not_called()


def test_register_artifact_rejects_mismatched_output_directory(tmp_path: Path) -> None:
    service, analysis_id, output_dir, db, repository = _make_service(tmp_path)
    wrong_output = tmp_path / "wrong-output"
    wrong_output.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="must match"):
        service.register_artifacts(
            analysis_id=analysis_id,
            output_dir=wrong_output,
            artifacts=[
                {
                    "kind": "ndvi_raster",
                    "relative_path": "ndvi.tif",
                }
            ],
        )

    repository.add.assert_not_called()

