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
            top_candidate_class_id="check_dam",
            threshold=None,
            model_version="development-mock-v1",
            model_hash="c9be1e9db3b66570b508644e9c88efbb0ca50a4f2d9a7efd7ae4e30302964c9b",
        )