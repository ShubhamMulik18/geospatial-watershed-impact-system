"""Predict one local photograph using an already exported watershed bundle.

Backend usage:
    predictor = load_predictor(bundle_dir, device="cpu")  # once at startup
    result = predictor.predict(image_path=stored_photo_path)  # per photograph

From the project root:
    .venv-ai/bin/python -m ai.inference.predictor --bundle PATH --image PATH

The CLI writes the internal result as JSON to stdout and a development reminder
to stderr. It never trains, downloads weights or writes photographs/results.
With the current bundle the threshold is unset, so every top candidate is a
provisional suggestion requiring human review, including high-scoring candidates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch

from ai.inference.contracts import PredictionResult, UNKNOWN_CLASS_ID
from ai.inference.model_loader import load_model
from ai.inference.preprocess import preprocess_image


class Predictor:
    """Keep one verified model in memory and reuse it for successive images.

    The backend resolves uploaded photo IDs to trusted local paths. HTTP, database
    access, GPS extraction and user corrections remain outside this module.
    """

    def __init__(self, bundle_dir: str | Path, *, device: str = "cpu") -> None:
        self._loaded = load_model(bundle_dir, device=device)

    def predict(self, image_path: str | Path) -> PredictionResult:
        """Return one result; invalid images raise ValueError, never a fake label.

        An unexpected tensor/model output raises RuntimeError. Bundle problems
        are raised during load_predictor(), before image requests are handled.
        Confidence is the top candidate's softmax score, not measured accuracy.
        """
        image = preprocess_image(image_path)
        if (not isinstance(image, torch.Tensor) or tuple(image.shape) != (3, 224, 224)
                or image.dtype != torch.float32 or image.device.type != "cpu"
                or not torch.isfinite(image).all().item()):
            raise RuntimeError("Preprocessing must return a finite CPU float32 tensor of shape (3, 224, 224).")

        loaded = self._loaded
        with torch.inference_mode():
            logits = loaded.model(image.unsqueeze(0))
            if (not isinstance(logits, torch.Tensor) or tuple(logits.shape) != (1, len(loaded.class_ids))
                    or logits.dtype != torch.float32 or logits.device.type != "cpu"
                    or not torch.isfinite(logits).all().item()):
                raise RuntimeError("Model must return finite CPU float32 logits for one image and the trained classes.")
            probabilities = torch.softmax(logits, dim=1)
            if not torch.isfinite(probabilities).all().item():
                raise RuntimeError("Model returned invalid class probabilities.")
            score, index = probabilities[0].max(dim=0)
            confidence = float(score.item())
            # A tie uses the first maximum in the bundle's trained class order.
            top_candidate = loaded.class_ids[int(index.item())]

        # The current loader accepts only threshold=None with forced review.
        # This numeric-cutoff branch preserves the contract for a future validated
        # bundle format; it does not provide a threshold override or select one.
        below_threshold = loaded.threshold is not None and confidence < loaded.threshold
        class_id = UNKNOWN_CLASS_ID if below_threshold else top_candidate
        result = PredictionResult(
            class_id=class_id,
            predicted_class=loaded.public_labels[class_id],
            confidence=confidence,
            requires_verification=(loaded.always_requires_verification
                                   or loaded.threshold is None or below_threshold),
            top_candidate_class_id=top_candidate,
            threshold=loaded.threshold,
            model_version=loaded.model_version,
            model_hash=loaded.model_hash,
        )
        result.validate_labels(loaded.public_labels)
        return result


def load_predictor(bundle_dir: str | Path, *, device: str = "cpu") -> Predictor:
    """Create one reusable predictor; the current bundle supports CPU only."""
    return Predictor(bundle_dir, device=device)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify one photo using a watershed development model bundle.")
    parser.add_argument("--bundle", type=Path, required=True, help="Exported bundle directory")
    parser.add_argument("--image", type=Path, required=True, help="Existing local photograph")
    args = parser.parse_args(argv)
    try:
        result = load_predictor(args.bundle).predict(image_path=args.image)
        print(json.dumps(result.to_dict(), indent=2, allow_nan=False))
        print("Development prediction only; human verification is required. Confidence is not measured accuracy.",
              file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        print("STOPPED: Prediction interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, ImportError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
