from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.integrations.ai.base import AIAdapter
from app.models.photo import Photo
from app.models.prediction import Prediction


class PredictionService:
    """Application service for photo-level AI predictions."""

    def __init__(
        self,
        db: Session,
        ai_adapter: AIAdapter,
    ) -> None:
        self.db = db
        self.ai_adapter = ai_adapter

    def create_prediction(self, photo_id: str) -> Prediction:
        try:
            photo_uuid = uuid.UUID(photo_id)
        except ValueError as exc:
            raise NotFoundError("Photo not found.") from exc

        photo = self.db.get(Photo, photo_uuid)
        if photo is None:
            raise NotFoundError("Photo not found.")

        photo_path = Path(photo.safe_path)
        if not photo_path.is_file():
            raise AppError(
                "Stored photo file is unavailable.",
                status_code=500,
                code="PHOTO_FILE_UNAVAILABLE",
            )

        result = self.ai_adapter.predict(photo_path)

        prediction = Prediction(
            photo_id=photo.id,
            model_version=result.model_version,
            model_hash=result.model_hash,
            class_id=result.class_id,
            predicted_label=result.predicted_class,
            confidence=result.confidence,
            top_candidate_class_id=result.top_candidate_class_id,
            threshold=result.threshold,
            review_flag=result.requires_verification,
        )

        self.db.add(prediction)
        self.db.flush()

        return prediction
