import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.analysis import Analysis
from app.models.artifact import Artifact
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.analysis import AnalysisStatus


client = TestClient(app)


def _create_analysis(db, suffix: str) -> Analysis:
    photo = Photo(
        id=uuid.uuid4(),
        safe_path=f"photos/artifact-api-{suffix}.jpg",
        original_name=f"artifact-api-{suffix}.jpg",
        mime_type="image/jpeg",
        byte_size=1024,
        sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        exif_status="valid",
    )

    prediction = Prediction(
        id=uuid.uuid4(),
        photo_id=photo.id,
        model_version="test-model-v1",
        model_hash="test-model-hash",
        class_id="check_dam",
        predicted_label="Check Dam",
        confidence=0.92,
        top_candidate_class_id="check_dam",
        threshold=0.5,
        review_flag=False,
    )

    analysis = Analysis(
        id=uuid.uuid4(),
        photo_id=photo.id,
        prediction_id=prediction.id,
        prediction_snapshot={
            "class": "Check Dam",
            "class_id": "1",
            "confidence": 0.92,
            "requires_verification": False,
            "model_version": "test-model-v1",
        },
        polygon=(
            "SRID=4326;POLYGON(("
            "73.0 18.0,73.01 18.0,73.01 18.01,"
            "73.0 18.01,73.0 18.0))"
        ),
        indicators=["ndvi"],
        status=AnalysisStatus.CREATED.value,
    )

    db.add_all([photo, prediction, analysis])
    db.commit()

    return analysis


def test_download_artifact_returns_registered_file() -> None:
    db = SessionLocal()
    analysis = _create_analysis(db, "download")

    settings = get_settings()
    storage_root = Path(settings.artifact_storage_root)
    relative_path = Path(str(analysis.id)) / "result.txt"
    artifact_path = storage_root / relative_path

    artifact = None

    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(b"artifact-test-content")

        artifact = ArtifactRepository().add(
            db=db,
            analysis_id=analysis.id,
            kind="test_result",
            safe_relative_path=relative_path.as_posix(),
            mime_type="text/plain",
            sha256="a" * 64,
            byte_size=len(b"artifact-test-content"),
        )
        db.commit()

        response = client.get(
            f"/api/analyses/{analysis.id}/artifacts/{artifact.id}"
        )

        assert response.status_code == 200
        assert response.content == b"artifact-test-content"
        assert response.headers["content-type"].startswith("text/plain")

    finally:
        if db.in_transaction():
            db.rollback()

        if artifact_path.exists():
            artifact_path.unlink()

        db.execute(delete(Artifact).where(Artifact.analysis_id == analysis.id))
        db.execute(delete(Analysis).where(Analysis.id == analysis.id))
        db.execute(
            delete(Prediction).where(Prediction.photo_id == analysis.photo_id)
        )
        db.execute(
            delete(Photo).where(Photo.id == analysis.photo_id)
        )
        db.commit()
        db.close()


def test_download_artifact_rejects_artifact_from_another_analysis() -> None:
    db = SessionLocal()
    analysis_one = _create_analysis(db, "scope-one")
    analysis_two = _create_analysis(db, "scope-two")

    artifact_path = (
        Path(get_settings().artifact_storage_root)
        / str(analysis_one.id)
        / "private.txt"
    )

    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(b"private-content")

        artifact = ArtifactRepository().add(
            db=db,
            analysis_id=analysis_one.id,
            kind="private",
            safe_relative_path=artifact_path.relative_to(
                Path(get_settings().artifact_storage_root)
            ).as_posix(),
            mime_type="text/plain",
            sha256="b" * 64,
            byte_size=len(b"private-content"),
        )
        db.commit()

        response = client.get(
            f"/api/analyses/{analysis_two.id}/artifacts/{artifact.id}"
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NotFoundError"

    finally:
        if db.in_transaction():
            db.rollback()

        if artifact_path.exists():
            artifact_path.unlink()

        db.execute(
            delete(Artifact).where(
                Artifact.analysis_id.in_(
                    [analysis_one.id, analysis_two.id]
                )
            )
        )
        db.execute(
            delete(Analysis).where(
                Analysis.id.in_(
                    [analysis_one.id, analysis_two.id]
                )
            )
        )
        db.execute(
            delete(Prediction).where(
                Prediction.photo_id.in_(
                    [analysis_one.photo_id, analysis_two.photo_id]
                )
            )
        )
        db.execute(
            delete(Photo).where(
                Photo.id.in_(
                    [analysis_one.photo_id, analysis_two.photo_id]
                )
            )
        )
        db.commit()
        db.close()
