from pathlib import Path
from typing import Any

from app.integrations.ai.base import AIAdapter, PredictionResult


class ProductionAIAdapter(AIAdapter):
    """Backend adapter for the validated Person 3 AI predictor."""

    def __init__(
        self,
        bundle_dir: Path,
        *,
        device: str = "cpu",
    ) -> None:
        from ai.inference.predictor import load_predictor

        self._predictor = load_predictor(
            bundle_dir,
            device=device,
        )

    def predict(self, photo_path: Path) -> PredictionResult:
        result: Any = self._predictor.predict(
            image_path=photo_path,
        )

        return PredictionResult(
            class_id=result.class_id,
            predicted_class=result.predicted_class,
            confidence=result.confidence,
            requires_verification=result.requires_verification,
            top_candidate_class_id=result.top_candidate_class_id,
            threshold=result.threshold,
            model_version=result.model_version,
            model_hash=result.model_hash,
        )
