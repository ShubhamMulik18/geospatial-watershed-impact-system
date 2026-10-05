from pathlib import Path

from app.integrations.ai.base import AIAdapter, PredictionResult


class DevelopmentAIAdapter(AIAdapter):
    """Explicit development adapter; never represents production inference."""

    def predict(self, photo_path: Path) -> PredictionResult:
        if not photo_path.is_file():
            raise FileNotFoundError(f"Photo does not exist: {photo_path}")

        return PredictionResult(
            class_id="other_unknown",
            predicted_class="Other/Unknown",
            confidence=0.0,
            requires_verification=True,
            model_version="development-mock-v1",
            model_hash=None,
        )
