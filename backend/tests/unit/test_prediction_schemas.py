import pytest
from pydantic import ValidationError

from app.schemas.prediction import PredictionResponse


def test_prediction_response_matches_contract():
    response = PredictionResponse(
        prediction_id="prediction-001",
        photo_id="photo-001",
        class_id="check_dam",
        predicted_class="Check Dam",
        confidence=0.92,
        requires_verification=False,
        model_version="intervention-mobilenetv2-v1",
    )

    assert response.model_dump() == {
        "prediction_id": "prediction-001",
        "photo_id": "photo-001",
        "class_id": "check_dam",
        "predicted_class": "Check Dam",
        "confidence": 0.92,
        "requires_verification": False,
        "model_version": "intervention-mobilenetv2-v1",
    }


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_prediction_response_rejects_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        PredictionResponse(
            prediction_id="prediction-001",
            photo_id="photo-001",
            class_id="check_dam",
            predicted_class="Check Dam",
            confidence=confidence,
            requires_verification=False,
            model_version="intervention-mobilenetv2-v1",
        )


@pytest.mark.parametrize(
    "confidence",
    [float("nan"), float("inf"), float("-inf")],
)
def test_prediction_response_rejects_non_finite_confidence(confidence):
    with pytest.raises(ValidationError):
        PredictionResponse(
            prediction_id="prediction-001",
            photo_id="photo-001",
            class_id="check_dam",
            predicted_class="Check Dam",
            confidence=confidence,
            requires_verification=False,
            model_version="intervention-mobilenetv2-v1",
        )