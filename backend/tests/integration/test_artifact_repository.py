import uuid

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.analysis import Analysis
from app.models.artifact import Artifact
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.analysis import AnalysisStatus


def _create_analysis(db, suffix: str) -> Analysis:
    photo = Photo(
        id=uuid.uuid4(),
        safe_path=f"photos/artifact-{suffix}.jpg",
        original_name=f"artifact-{suffix}.jpg",
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
        label_id=1,
        predicted_label="Check Dam",
        confidence=0.92,
        top_candidate="Check Dam",
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


def test_add_and_get_artifact_for_analysis() -> None:
    db = SessionLocal()
    analysis = _create_analysis(db, "add-get")

    try:
        repository = ArtifactRepository()

        artifact = repository.add(
            db=db,
            analysis_id=analysis.id,
            kind="ndvi_raster",
            safe_relative_path=f"{analysis.id}/ndvi.tif",
            mime_type="image/tiff",
            sha256="a" * 64,
            byte_size=2048,
            metadata={"dataset_id": "dataset-1"},
        )

        assert artifact.id is not None
        assert artifact.analysis_id == analysis.id
        assert artifact.kind == "ndvi_raster"
        assert artifact.safe_relative_path == f"{analysis.id}/ndvi.tif"
        assert artifact.mime_type == "image/tiff"
        assert artifact.sha256 == "a" * 64
        assert artifact.byte_size == 2048
        assert artifact.metadata_json == {"dataset_id": "dataset-1"}

        db.commit()

        loaded = repository.get_for_analysis(
            db=db,
            analysis_id=analysis.id,
            artifact_id=artifact.id,
        )

        assert loaded is not None
        assert loaded.id == artifact.id

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Artifact).where(Artifact.analysis_id == analysis.id))
        db.execute(delete(Analysis).where(Analysis.id == analysis.id))
        db.execute(delete(Prediction).where(Prediction.photo_id == analysis.photo_id))
        db.execute(delete(Photo).where(Photo.id == analysis.photo_id))
        db.commit()
        db.close()


def test_get_artifact_rejects_artifact_from_another_analysis() -> None:
    db = SessionLocal()
    analysis_one = _create_analysis(db, "scope-one")
    analysis_two = _create_analysis(db, "scope-two")

    try:
        repository = ArtifactRepository()

        artifact = repository.add(
            db=db,
            analysis_id=analysis_one.id,
            kind="preview",
            safe_relative_path=f"{analysis_one.id}/preview.png",
            mime_type="image/png",
            sha256="b" * 64,
            byte_size=512,
        )

        db.commit()

        result = repository.get_for_analysis(
            db=db,
            analysis_id=analysis_two.id,
            artifact_id=artifact.id,
        )

        assert result is None

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Artifact).where(
            Artifact.analysis_id.in_([analysis_one.id, analysis_two.id])
        ))
        db.execute(delete(Analysis).where(
            Analysis.id.in_([analysis_one.id, analysis_two.id])
        ))
        db.execute(delete(Prediction).where(
            Prediction.photo_id.in_([analysis_one.photo_id, analysis_two.photo_id])
        ))
        db.execute(delete(Photo).where(
            Photo.id.in_([analysis_one.photo_id, analysis_two.photo_id])
        ))
        db.commit()
        db.close()


def test_list_artifacts_for_analysis_is_scoped() -> None:
    db = SessionLocal()
    analysis_one = _create_analysis(db, "list-one")
    analysis_two = _create_analysis(db, "list-two")

    try:
        repository = ArtifactRepository()

        first = repository.add(
            db=db,
            analysis_id=analysis_one.id,
            kind="preview",
            safe_relative_path=f"{analysis_one.id}/preview.png",
            mime_type="image/png",
            sha256="c" * 64,
            byte_size=100,
        )

        second = repository.add(
            db=db,
            analysis_id=analysis_two.id,
            kind="preview",
            safe_relative_path=f"{analysis_two.id}/preview.png",
            mime_type="image/png",
            sha256="d" * 64,
            byte_size=200,
        )

        db.commit()

        artifacts = repository.list_for_analysis(
            db=db,
            analysis_id=analysis_one.id,
        )

        assert [artifact.id for artifact in artifacts] == [first.id]
        assert second.id not in {artifact.id for artifact in artifacts}

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Artifact).where(
            Artifact.analysis_id.in_([analysis_one.id, analysis_two.id])
        ))
        db.execute(delete(Analysis).where(
            Analysis.id.in_([analysis_one.id, analysis_two.id])
        ))
        db.execute(delete(Prediction).where(
            Prediction.photo_id.in_([analysis_one.photo_id, analysis_two.photo_id])
        ))
        db.execute(delete(Photo).where(
            Photo.id.in_([analysis_one.photo_id, analysis_two.photo_id])
        ))
        db.commit()
        db.close()