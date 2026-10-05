import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.analysis import Analysis
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.repositories.analysis_worker_repository import AnalysisWorkerRepository
from app.schemas.analysis import AnalysisStatus


def test_claim_next_analysis_sets_queue_and_lease() -> None:
    db = SessionLocal()

    photo = Photo(
        id=uuid.uuid4(),
        safe_path="photos/worker-test.jpg",
        original_name="worker-test.jpg",
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
        polygon="SRID=4326;POLYGON((73.0 18.0,73.01 18.0,73.01 18.01,73.0 18.01,73.0 18.0))",
        indicators=["ndvi"],
        status=AnalysisStatus.CREATED.value,
    )

    try:
        db.add_all([photo, prediction, analysis])
        db.commit()

        repository = AnalysisWorkerRepository()

        claimed = repository.claim_next_analysis(
            db=db,
            lease_seconds=300,
        )

        assert claimed is not None
        assert claimed.id == analysis.id
        assert claimed.status == AnalysisStatus.QUEUED.value
        assert claimed.worker_heartbeat_at is not None
        assert claimed.worker_lease_expires_at is not None

        now = datetime.now(timezone.utc)
        assert claimed.worker_lease_expires_at > now
        assert claimed.worker_lease_expires_at <= now + timedelta(seconds=301)

        db.commit()

        second_claim = repository.claim_next_analysis(
            db=db,
            lease_seconds=300,
        )

        assert second_claim is None

        db.rollback()

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Analysis).where(Analysis.id == analysis.id))
        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.commit()
        db.close()

def test_recover_expired_analysis_marks_failed() -> None:
    db = SessionLocal()

    photo = Photo(
        id=uuid.uuid4(),
        safe_path="photos/worker-recovery-test.jpg",
        original_name="worker-recovery-test.jpg",
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
        polygon="SRID=4326;POLYGON((73.0 18.0,73.01 18.0,73.01 18.01,73.0 18.01,73.0 18.0))",
        indicators=["ndvi"],
        status=AnalysisStatus.QUEUED.value,
        worker_lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    try:
        db.add_all([photo, prediction, analysis])
        db.commit()

        repository = AnalysisWorkerRepository()

        recovered = repository.recover_expired_analyses(db)

        assert recovered == 1
        assert analysis.status == AnalysisStatus.FAILED.value
        assert analysis.error is not None
        assert "lease expired" in analysis.error.lower()

        db.commit()

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Analysis).where(Analysis.id == analysis.id))
        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.commit()
        db.close()

def test_renew_lease_updates_running_analysis() -> None:
    db = SessionLocal()

    photo = Photo(
        id=uuid.uuid4(),
        safe_path="photos/worker-renew-test.jpg",
        original_name="worker-renew-test.jpg",
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
        polygon="SRID=4326;POLYGON((73.0 18.0,73.01 18.0,73.01 18.01,73.0 18.01,73.0 18.0))",
        indicators=["ndvi"],
        status=AnalysisStatus.RUNNING.value,
        worker_lease_expires_at=datetime.now(timezone.utc),
    )

    try:
        db.add_all([photo, prediction, analysis])
        db.commit()

        repository = AnalysisWorkerRepository()

        renewed = repository.renew_lease(
            db=db,
            analysis_id=analysis.id,
            lease_seconds=300,
        )

        assert renewed is True
        assert analysis.worker_heartbeat_at is not None
        assert analysis.worker_lease_expires_at is not None

        now = datetime.now(timezone.utc)
        assert analysis.worker_lease_expires_at > now
        assert analysis.worker_lease_expires_at <= now + timedelta(seconds=301)

        db.commit()

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Analysis).where(Analysis.id == analysis.id))
        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.commit()
        db.close()