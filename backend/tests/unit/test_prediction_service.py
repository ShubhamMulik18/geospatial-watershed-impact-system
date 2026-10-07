import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import AppError, NotFoundError
from app.integrations.ai.base import PredictionResult
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.services.prediction_service import PredictionService


class FakeAIAdapter:
    def __init__(self, result: PredictionResult) -> None:
        self.result = result
        self.received_path: Path | None = None

    def predict(self, photo_path: Path) -> PredictionResult:
        self.received_path = photo_path
        return self.result


def _prediction_result() -> PredictionResult:
    return PredictionResult(
        class_id="check_dam",
        predicted_class="Check Dam",
        confidence=0.91,
        requires_verification=False,
        top_candidate_class_id="check_dam",
        threshold=0.80,
        model_version="test-model-v1",
        model_hash="a" * 64,
    )


def test_create_prediction_maps_ai_result_to_prediction(tmp_path: Path) -> None:
    db = MagicMock()
    photo_path = tmp_path / "photo.jpg"
    photo_path.write_bytes(b"photo")

    photo = Photo(
        id=uuid.uuid4(),
        safe_path=str(photo_path),
        original_name="field-photo.jpg",
        mime_type="image/jpeg",
        byte_size=5,
        sha256="b" * 64,
        exif_status="missing",
    )

    db.get.return_value = photo

    adapter = FakeAIAdapter(_prediction_result())
    service = PredictionService(
        db=db,
        ai_adapter=adapter,
    )

    prediction = service.create_prediction(str(photo.id))

    assert isinstance(prediction, Prediction)
    assert prediction.photo_id == photo.id
    assert prediction.class_id == "check_dam"
    assert prediction.predicted_label == "Check Dam"
    assert prediction.confidence == 0.91
    assert prediction.review_flag is False
    assert prediction.top_candidate_class_id == "check_dam"
    assert prediction.threshold == 0.80
    assert prediction.model_version == "test-model-v1"
    assert prediction.model_hash == "a" * 64

    assert adapter.received_path == photo_path
    db.add.assert_called_once_with(prediction)
    db.flush.assert_called_once()


def test_create_prediction_rejects_missing_photo() -> None:
    db = MagicMock()
    db.get.return_value = None

    adapter = FakeAIAdapter(_prediction_result())
    service = PredictionService(
        db=db,
        ai_adapter=adapter,
    )

    with pytest.raises(NotFoundError, match="Photo not found"):
        service.create_prediction("00000000-0000-0000-0000-000000000000")

    assert adapter.received_path is None
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_create_prediction_rejects_unavailable_photo_file(
    tmp_path: Path,
) -> None:
    db = MagicMock()

    photo = Photo(
        id=uuid.uuid4(),
        safe_path=str(tmp_path / "missing.jpg"),
        original_name="field-photo.jpg",
        mime_type="image/jpeg",
        byte_size=5,
        sha256="b" * 64,
        exif_status="missing",
    )

    db.get.return_value = photo

    adapter = FakeAIAdapter(_prediction_result())
    service = PredictionService(
        db=db,
        ai_adapter=adapter,
    )

    with pytest.raises(AppError, match="Stored photo file is unavailable"):
        service.create_prediction(str(photo.id))

    db.add.assert_not_called()
    db.flush.assert_not_called()
    assert adapter.received_path is None
