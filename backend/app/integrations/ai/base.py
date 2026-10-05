from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PredictionResult:
    class_id: str
    predicted_class: str
    confidence: float
    requires_verification: bool
    model_version: str
    model_hash: str | None = None


class AIAdapter(ABC):
    """Backend-facing contract for photo classification."""

    @abstractmethod
    def predict(self, photo_path: Path) -> PredictionResult:
        """Run inference for a trusted photo path."""
        raise NotImplementedError
