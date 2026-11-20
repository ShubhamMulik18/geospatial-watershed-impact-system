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
        p = Path(bundle_dir)
        if not p.is_absolute() and not p.exists():
            repo_root = Path(__file__).resolve().parents[4]
            if (repo_root / p).exists():
                p = repo_root / p

        from ai.inference.predictor import load_predictor

        self._predictor = load_predictor(
            p,
            device=device,
        )

    def predict(self, photo_path: Path) -> PredictionResult:
        p = Path(photo_path)
        if not p.is_absolute() and not p.exists():
            repo_root = Path(__file__).resolve().parents[4]
            if (repo_root / p).exists():
                p = repo_root / p

        if not p.is_file():
            raise FileNotFoundError(f"Photo file does not exist: {photo_path}")

        result: Any = self._predictor.predict(
            image_path=p,
        )

        warnings: list[str] = []
        if getattr(result, "requires_verification", False):
            warnings.append("Human verification required: development model prediction.")
        if getattr(result, "threshold", None) is None:
            warnings.append("Confidence threshold is unset; top candidate returned for review.")

        return PredictionResult(
            class_id=result.class_id,
            predicted_class=result.predicted_class,
            confidence=result.confidence,
            requires_verification=result.requires_verification,
            top_candidate_class_id=result.top_candidate_class_id,
            threshold=result.threshold,
            model_version=result.model_version,
            model_hash=result.model_hash,
            warnings=warnings,
        )
