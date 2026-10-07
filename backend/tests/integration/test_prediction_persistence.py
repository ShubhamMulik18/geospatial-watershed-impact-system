import uuid
from pathlib import Path

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.integrations.ai.base import PredictionResult
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.services.prediction_service import PredictionService


class FakeAIAdapter:
    def __init__(self) -> None:
        self.received_path: Path | None = None

    def predict(self, photo_path: Path) -> PredictionResult:
        self.received_path = photo_path
        return PredictionResult(
            class_id="check_dam",
            predicted_class="Check Dam",
            confidence=0.91,
            requires_verification=False,
            top_candidate_class_id="check_dam",
            threshold=0.80,
            model_version="integration-model-v1",
            model_hash="a" * 64,
        )


def test_prediction_persists_ai_result() -> None:
    db = SessionLocal()

    photo_id = uuid.uuid4()
    photo_path = Path("uploads/photos/integration-prediction.jpg")

    photo = Photo(
        id=photo_id,
        safe_path=str(photo_path),
        original_name="integration-prediction.jpg",
        mime_type="image/jpeg",
        byte_size=5,
        sha256="b" * 64,
        exif_status="missing",
    )

    adapter = FakeAIAdapter()

    try:
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(b"photo")

        db.add(photo)
        db.commit()

        service = PredictionService(
            db=db,
            ai_adapter=adapter,
        )

        prediction = service.create_prediction(str(photo_id))
        db.commit()

        persisted = db.execute(
            select(Prediction).where(Prediction.id == prediction.id)
        ).scalar_one()

        assert persisted.photo_id == photo_id
        assert persisted.model_version == "integration-model-v1"
        assert persisted.model_hash == "a" * 64
        assert persisted.class_id == "check_dam"
        assert persisted.predicted_label == "Check Dam"
        assert persisted.confidence == 0.91
        assert persisted.top_candidate_class_id == "check_dam"
        assert persisted.threshold == 0.80
        assert persisted.review_flag is False

        assert adapter.received_path == photo_path

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(
            delete(Prediction).where(Prediction.photo_id == photo_id)
        )
        db.execute(
            delete(Photo).where(Photo.id == photo_id)
        )
        db.commit()
        db.close()

        if photo_path.exists():
            photo_path.unlink()
