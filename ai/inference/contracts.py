"""Result format shared by the AI predictor and the backend.

This module uses only the Python standard library. Importing it does not load a
model, read photographs or download anything. It does not calculate predictions.

The future predictor must call validate_labels() with the public labels loaded
from the model bundle before returning a result. The bundle loader must separately
check that the top candidate belongs to that model's ordered trained classes.

threshold=None means no threshold has been selected. It always requires review.
The current backend database cannot store None in its threshold column; Person 2
must resolve that before persistence. See README.md in this folder.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from math import isfinite
import re


UNKNOWN_CLASS_ID = "other_unknown"


def _text(value: object, name: str, max_length: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > max_length
    ):
        raise ValueError(
            f"{name} must be nonblank text, without surrounding spaces, "
            f"and at most {max_length} characters."
        )


def _probability(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.0 <= value <= 1.0
        or not isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number from 0 to 1.")
    return float(value)


@dataclass(frozen=True, kw_only=True)
class PredictionResult:
    """One internal AI result; photo and prediction IDs belong to the backend.

    confidence is the top trained candidate's softmax score, including when the
    public class is Other/Unknown. It is not an Other/Unknown probability or an
    accuracy measurement. model_hash is the lowercase SHA-256 of the exact saved
    weights file loaded for inference. model_version identifies its bundle.

    Contract validation cannot establish whether a numeric threshold was measured
    properly. The bundle records its provenance. The development predictor must
    require review for every result, even if a provisional threshold is supplied.
    """

    class_id: str
    predicted_class: str
    confidence: float
    requires_verification: bool
    top_candidate_class_id: str
    threshold: float | None
    model_version: str
    model_hash: str

    def __post_init__(self) -> None:
        for name in ("class_id", "top_candidate_class_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", value):
                raise ValueError(f"{name} must be a snake_case class ID.")
        _text(self.predicted_class, "predicted_class", 256)
        _text(self.model_version, "model_version", 128)
        if not isinstance(self.model_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", self.model_hash):
            raise ValueError("model_hash must be a lowercase, 64-character SHA-256 digest.")
        if not isinstance(self.requires_verification, bool):
            raise ValueError("requires_verification must be True or False.")
        object.__setattr__(self, "confidence", _probability(self.confidence, "confidence"))
        if self.threshold is not None:
            object.__setattr__(self, "threshold", _probability(self.threshold, "threshold"))

        # Other/Unknown is currently a fallback, not a trained output class.
        if self.top_candidate_class_id == UNKNOWN_CLASS_ID:
            raise ValueError("top_candidate_class_id must name a trained intervention class.")
        if self.class_id not in (self.top_candidate_class_id, UNKNOWN_CLASS_ID):
            raise ValueError("class_id must be the top candidate or other_unknown.")
        if self.threshold is None and not self.requires_verification:
            raise ValueError("An unselected threshold requires human verification.")
        if self.class_id == UNKNOWN_CLASS_ID and not self.requires_verification:
            raise ValueError("Other/Unknown requires human verification.")
        if self.threshold is not None and self.confidence < self.threshold:
            if self.class_id != UNKNOWN_CLASS_ID:
                raise ValueError("A score below the threshold must return other_unknown.")

    def validate_labels(self, public_labels: Mapping[str, str]) -> None:
        """Check IDs and display text against the public config/bundle labels.

        Pass {class_id: label}, built from classes.json or the exported bundle.
        This avoids keeping a second hard-coded list of class names in this file.
        """
        if not isinstance(public_labels, Mapping):
            raise ValueError("public_labels must map class IDs to display labels.")
        for class_id in (self.class_id, self.top_candidate_class_id):
            if class_id not in public_labels:
                raise ValueError(f"Class ID is absent from the public labels: {class_id}.")
        if self.predicted_class != public_labels[self.class_id]:
            raise ValueError("predicted_class does not match the configured display label.")

    def to_dict(self) -> dict[str, str | float | bool | None]:
        """Return all eight internal fields; do not send this directly to the API."""
        return asdict(self)

    def to_public_fields(self) -> dict[str, str | float | bool]:
        """Return only AI-owned fields allowed by backend PredictionResponse.

        Person 2 adds prediction_id and photo_id. Internal metadata belongs in
        backend persistence, not in the current strict public response schema.
        """
        return {
            "class_id": self.class_id,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "requires_verification": self.requires_verification,
            "model_version": self.model_version,
        }
