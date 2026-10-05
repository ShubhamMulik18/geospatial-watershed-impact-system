"""Load an exported development bundle on CPU, without training or downloads.

From the project root:
    .venv-ai/bin/python -m ai.inference.model_loader --bundle PATH --check

Only bundles exported by ai.training.export_model are supported. Load files from
your own team: checksums detect mismatched files, not an untrusted publisher.
The returned model produces logits. Photo prediction belongs in predictor.py.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import pickle
import re
import sys
from types import MappingProxyType

import torch

from ai.inference.model import WatershedMobileNetV2


PREPROCESSING = {
    "profile": "mobilenet_v2_imagenet1k_v2", "exif_orientation": True, "color_mode": "RGB",
    "alpha_background": "white", "resize_shorter_edge": 232, "center_crop": [224, 224],
    "interpolation": "bilinear", "antialias": True, "pixel_scale": 1.0 / 255.0,
    "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225],
}
DEVELOPMENT_POLICY = {
    "threshold": None, "threshold_status": "unselected",
    "always_requires_verification": True, "fallback_class_id": "other_unknown",
    "unselected_action": "return_top_candidate_for_review",
}
LIMITATION = "Development model on a small collection; scores do not establish reliable real-world accuracy."


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def read_json_bytes(data: bytes, name: str) -> dict:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{name}: duplicate JSON key {key!r}.")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_pairs)
        if not isinstance(value, dict):
            raise ValueError(f"{name} must contain a JSON object.")
        json_bytes(value)  # Reject NaN/infinity, including in nested metadata.
        return value
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Cannot read {name}: {exc}") from exc


def validate_model_version(value: object) -> str:
    if (not isinstance(value, str) or len(value) > 128
            or not re.fullmatch(r"dev-[A-Za-z0-9][A-Za-z0-9._-]*", value)):
        raise ValueError("Use a development model version such as dev-20261005-v1 (maximum 128 characters).")
    return value


def read_public_classes(data: bytes) -> dict[str, str]:
    document = read_json_bytes(data, "classes.json")
    if set(document) != {"schema_version", "classes"} or document["schema_version"] != "1.0":
        raise ValueError("Unsupported classes.json format.")
    rows = document["classes"]
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError("This baseline requires four public intervention classes plus other_unknown.")
    labels = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"class_id", "label"}:
            raise ValueError("Each public class must contain class_id and label.")
        class_id, label = row["class_id"], row["label"]
        if not isinstance(class_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", class_id):
            raise ValueError("Invalid public class ID.")
        if class_id in labels:
            raise ValueError(f"Duplicate public class ID: {class_id}.")
        if not isinstance(label, str) or not label.strip() or label != label.strip() or len(label) > 256:
            raise ValueError("Public display labels must be nonblank text of at most 256 characters.")
        labels[class_id] = label
    if "other_unknown" not in labels or "plantation" in labels:
        raise ValueError("The current scope includes other_unknown and excludes plantation.")
    return labels


def validate_class_order(class_ids: object, labels: Mapping[str, str]) -> tuple[str, ...]:
    expected = [class_id for class_id in labels if class_id != "other_unknown"]
    if not isinstance(class_ids, list) or class_ids != expected:
        raise ValueError("Trained class order must match the public classes, excluding other_unknown.")
    return tuple(class_ids)


def load_torch_bytes(data: bytes, name: str):
    try:
        return torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)
    except (OSError, EOFError, RuntimeError, ValueError, pickle.UnpicklingError) as exc:
        raise ValueError(f"Cannot load {name} as a weights-only CPU file: {exc}") from exc


def restore_model(state: object, class_ids: tuple[str, ...]) -> WatershedMobileNetV2:
    """Strictly rebuild the shared architecture; never load pretrained weights."""
    with torch.random.fork_rng(devices=[]):
        model = WatershedMobileNetV2(class_ids, pretrained=False, freeze_backbone=True)
    expected = model.state_dict()
    if not isinstance(state, Mapping) or set(state) != set(expected):
        raise ValueError("Saved weights do not match the shared MobileNetV2 state_dict keys.")
    for name, reference in expected.items():
        tensor = state[name]
        if (not isinstance(tensor, torch.Tensor) or tensor.layout != torch.strided
                or tensor.device.type != "cpu" or tensor.shape != reference.shape
                or tensor.dtype != reference.dtype or not torch.isfinite(tensor).all().item()):
            raise ValueError(f"Invalid saved weight tensor: {name}.")
    model.load_state_dict(state, strict=True)
    model.requires_grad_(False)
    model.eval()
    return model


def check_model_output(model: WatershedMobileNetV2) -> torch.Tensor:
    """Use one synthetic tensor for a software check, not an accuracy result."""
    with torch.inference_mode():
        logits = model(torch.zeros(1, 3, 224, 224, dtype=torch.float32))
    if (tuple(logits.shape) != (1, len(model.class_ids)) or logits.dtype != torch.float32
            or logits.device.type != "cpu" or not torch.isfinite(logits).all().item()):
        raise ValueError("Expected finite CPU float32 logits with one column per trained class.")
    return logits


@dataclass(frozen=True)
class LoadedModel:
    model: WatershedMobileNetV2
    class_ids: tuple[str, ...]
    public_labels: Mapping[str, str]
    model_version: str
    model_hash: str
    threshold: float | None
    always_requires_verification: bool


def load_model(bundle_dir: str | Path, *, device: str = "cpu") -> LoadedModel:
    """Load a complete portable bundle; no project config or training data needed."""
    if device != "cpu":
        raise ValueError("This development loader supports device='cpu' only.")
    directory = Path(bundle_dir).resolve()
    metadata = read_json_bytes((directory / "metadata.json").read_bytes(), "bundle metadata.json")
    fields = {"schema_version", "purpose", "model_version", "architecture", "weights_file", "model_hash",
              "classes_file", "classes_sha256", "class_ids", "preprocessing", "decision_policy",
              "training", "export", "test_evaluated", "limitations"}
    if set(metadata) != fields:
        raise ValueError("Unexpected bundle metadata fields; use this project's development exporter.")
    if (metadata["schema_version"] != "1.0" or metadata["purpose"] != "development_inference"
            or metadata["architecture"] != "mobilenet_v2" or metadata["test_evaluated"] is not False):
        raise ValueError("Unsupported development bundle format or evaluation status.")
    version = validate_model_version(metadata["model_version"])
    if metadata["weights_file"] != "model.pt" or metadata["classes_file"] != "classes.json":
        raise ValueError("Bundle files must be named model.pt and classes.json.")
    if json_bytes(metadata["preprocessing"]) != json_bytes(PREPROCESSING):
        raise ValueError("Bundle preprocessing does not match the shared MobileNetV2 V2 profile.")
    if json_bytes(metadata["decision_policy"]) != json_bytes(DEVELOPMENT_POLICY):
        raise ValueError("This development bundle must keep its threshold unset and require review.")
    classes_data = (directory / "classes.json").read_bytes()
    weights_data = (directory / "model.pt").read_bytes()
    if sha256_bytes(classes_data) != metadata["classes_sha256"]:
        raise ValueError("Class-file SHA-256 mismatch. Keep the exported bundle files together.")
    if sha256_bytes(weights_data) != metadata["model_hash"]:
        raise ValueError("Model SHA-256 mismatch. Keep the exported bundle files together.")
    labels = read_public_classes(classes_data)
    class_ids = validate_class_order(metadata["class_ids"], labels)
    model = restore_model(load_torch_bytes(weights_data, "model.pt"), class_ids)
    return LoadedModel(model, class_ids, MappingProxyType(labels), version,
                       metadata["model_hash"], None, True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify and load a watershed development model bundle on CPU.")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        loaded = load_model(args.bundle)
        logits = check_model_output(loaded.model)
        print(f"Model version: {loaded.model_version}")
        print("Class order: " + ", ".join(loaded.class_ids))
        print(f"CPU output shape: {tuple(logits.shape)}")
        print("Threshold: unselected; every development prediction requires human review.")
        print("PASS: Bundle integrity and CPU loading checks completed.")
        print("Synthetic tensor check only; no photograph predictions or accuracy measurements.")
        return 0
    except (OSError, ValueError, RuntimeError, ImportError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
