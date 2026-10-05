"""Export a completed development run as a portable, CPU-loadable model bundle.

Run with python -m ai.training.export_model. --check is read-only; --write creates
a NEW versioned folder under ai/models/. Existing bundles are never overwritten.
This does not train, download weights, read field photos or select a threshold.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import io
import math
from pathlib import Path
import platform
import shutil
import sys

import torch

from ai.inference.model_loader import (
    DEVELOPMENT_POLICY, LIMITATION, PREPROCESSING, check_model_output, json_bytes,
    load_model, load_torch_bytes, read_json_bytes, read_public_classes, restore_model,
    sha256_bytes, validate_class_order, validate_model_version,
)


def _require_same(actual: object, expected: object, name: str) -> None:
    if json_bytes(actual) != json_bytes(expected):
        raise ValueError(f"{name} does not match the completed training run or supported baseline.")


def _validate_counts_and_metrics(counts: object, metrics: object, class_ids: tuple[str, ...]) -> None:
    if not isinstance(counts, dict) or set(counts) != {"train", "validation", "test"}:
        raise ValueError("Training metadata must record train, validation and test counts.")
    for split, count in counts.items():
        if not isinstance(count, dict) or set(count) != {"photos", "sites", "classes"}:
            raise ValueError(f"Invalid {split} counts.")
        if any(type(count[key]) is not int or count[key] < 1 for key in ("photos", "sites")):
            raise ValueError(f"Missing positive photograph/site counts for {split}.")
        classes = count["classes"]
        if (not isinstance(classes, dict) or set(classes) != set(class_ids)
                or any(type(n) is not int or n < 0 for n in classes.values())
                or sum(classes.values()) != count["photos"] or count["sites"] > count["photos"]):
            raise ValueError(f"Inconsistent class counts for {split}.")
    if not isinstance(metrics, dict) or metrics.get("samples") != counts["validation"]["photos"]:
        raise ValueError("Validation sample count does not match the training metadata.")
    for key in ("loss", "accuracy", "macro_f1"):
        value = metrics.get(key)
        if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                or (key != "loss" and value > 1)):
            raise ValueError(f"Invalid validation metric: {key}.")


def prepare_bundle(checkpoint_path: Path, classes_path: Path, model_version: str) -> tuple[dict, dict, torch.Tensor]:
    """Check inputs and serialize an export in memory; no directories are created."""
    model_version = validate_model_version(model_version)
    checkpoint_path, classes_path = checkpoint_path.resolve(), classes_path.resolve()
    metadata_path = checkpoint_path.parent / "metadata.json"
    sources = {path: path.read_bytes() for path in (checkpoint_path, classes_path, metadata_path)}
    checkpoint = load_torch_bytes(sources[checkpoint_path], "training checkpoint")
    run = read_json_bytes(sources[metadata_path], "training metadata.json")
    labels = read_public_classes(sources[classes_path])
    required = {"format_version", "purpose", "architecture", "initial_weights", "backbone_frozen",
                "class_ids", "preprocessing", "seed", "epoch", "validation_metrics", "input_fingerprints",
                "package_versions", "confidence_threshold", "test_evaluated", "model_state_dict"}
    if not isinstance(checkpoint, dict) or set(checkpoint) != required:
        raise ValueError("Checkpoint format does not match this project's development trainer.")
    fixed = {"format_version": "1.0", "purpose": "development_checkpoint", "architecture": "mobilenet_v2",
             "initial_weights": "IMAGENET1K_V2", "backbone_frozen": True,
             "confidence_threshold": None, "test_evaluated": False}
    for key, expected in fixed.items():
        _require_same(checkpoint[key], expected, f"Checkpoint {key}")
    if run.get("status") != "completed" or run.get("purpose") != "development" or run.get("schema_version") != "1.0":
        raise ValueError("Export requires metadata.json from a completed development training run.")
    _require_same(checkpoint["preprocessing"], PREPROCESSING, "Preprocessing")
    class_ids = validate_class_order(checkpoint["class_ids"], labels)
    for key in ("architecture", "initial_weights", "backbone_frozen", "class_ids", "preprocessing", "seed",
                "input_fingerprints", "package_versions", "confidence_threshold", "test_evaluated"):
        if key not in run:
            raise ValueError(f"Training metadata is missing {key}.")
        _require_same(run[key], checkpoint[key], f"Training metadata {key}")
    _require_same(run.get("best_epoch"), checkpoint["epoch"], "Best checkpoint epoch")
    _require_same(run.get("best_validation"), checkpoint["validation_metrics"], "Best validation metrics")
    epoch, completed = checkpoint["epoch"], run.get("epochs_completed")
    if type(epoch) is not int or type(completed) is not int or not 1 <= epoch <= completed:
        raise ValueError("Invalid checkpoint epoch or completed-epoch count.")
    if type(run.get("epochs_requested")) is not int or completed != run["epochs_requested"]:
        raise ValueError("All requested development epochs must have completed before export.")
    fingerprints = checkpoint["input_fingerprints"]
    if (not isinstance(fingerprints, dict)
            or fingerprints.get("classes_sha256") != sha256_bytes(sources[classes_path])):
        raise ValueError("classes.json differs from the file used for training. Use that run's original class file.")
    _validate_counts_and_metrics(run.get("counts"), checkpoint["validation_metrics"], class_ids)
    model = restore_model(checkpoint["model_state_dict"], class_ids)
    reference_logits = check_model_output(model)
    weights_buffer = io.BytesIO()
    torch.save({name: value.detach().cpu().clone() for name, value in model.state_dict().items()}, weights_buffer)
    weights = weights_buffer.getvalue()
    metadata = {
        "schema_version": "1.0", "purpose": "development_inference", "model_version": model_version,
        "architecture": "mobilenet_v2", "weights_file": "model.pt", "model_hash": sha256_bytes(weights),
        "classes_file": "classes.json", "classes_sha256": sha256_bytes(sources[classes_path]),
        "class_ids": list(class_ids), "preprocessing": PREPROCESSING, "decision_policy": DEVELOPMENT_POLICY,
        "training": {"checkpoint_sha256": sha256_bytes(sources[checkpoint_path]),
                     "run_metadata_sha256": sha256_bytes(sources[metadata_path]),
                     "epoch": epoch, "seed": checkpoint["seed"], "counts": run["counts"],
                     "validation_metrics": checkpoint["validation_metrics"],
                     "input_fingerprints": fingerprints, "package_versions": checkpoint["package_versions"]},
        "export": {"created_at": datetime.now(timezone.utc).isoformat(), "python_version": platform.python_version(),
                   "package_versions": {name: version(name) for name in ("torch", "torchvision", "Pillow")}},
        "test_evaluated": False,
        "limitations": [LIMITATION, "No held-out test evaluation or confidence-threshold selection has been performed.",
                        "Other/Unknown is a review fallback; it is not a trained class."],
    }
    counts, metrics = run["counts"], checkpoint["validation_metrics"]
    card = (
        f"Watershed Development Model: {model_version}\n\n"
        f"{LIMITATION}\n\n"
        f"Architecture: MobileNetV2, initialized for training with ImageNet V2 weights.\n"
        f"Trained output order: {', '.join(class_ids)}.\n"
        f"Selected checkpoint epoch: {epoch}.\n"
        f"Training photos: {counts['train']['photos']}; validation photos: {counts['validation']['photos']}; "
        f"reserved test photos: {counts['test']['photos']}.\n"
        f"Recorded validation macro F1: {metrics['macro_f1']:.4f}.\n"
        f"Recorded validation loss: {metrics['loss']:.4f}.\n\n"
        "These are the training run's recorded validation results, not new export measurements.\n"
        "Held-out test evaluation: not performed. Confidence threshold: unselected.\n"
        "Every development prediction requires human review. The proposed predictor returns\n"
        "the top candidate for review while the threshold is unset. No new threshold is assigned.\n"
        "Other/Unknown is a fallback, not a trained output.\n\n"
        "Keep model.pt, classes.json, metadata.json and this card together.\n"
        "The CPU loader checks weights, class order, hashes and preprocessing. It needs the\n"
        "shared AI Python code and compatible torch/torchvision/Pillow packages on the target\n"
        "machine. Exporting does not package a Python environment or prove cross-platform compatibility.\n"
        "The backend endpoint, database mapping and unset-threshold handling remain separate integration work.\n"
    )
    files = {"model.pt": weights, "classes.json": sources[classes_path],
             "MODEL_CARD.md": card.encode("utf-8"), "metadata.json": json_bytes(metadata)}
    return files, sources, reference_logits


def write_bundle(destination: Path, files: dict[str, bytes], sources: dict[Path, bytes],
                 reference_logits: torch.Tensor) -> Path:
    """Create a new bundle and verify it; remove only this new folder on failure."""
    for path, original in sources.items():
        if path.read_bytes() != original:
            raise ValueError(f"Export input changed: {path.name}. Run the check again.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)  # Never overwrite even an empty existing bundle.
    try:
        for filename, data in files.items():
            (destination / filename).write_bytes(data)
        restored = load_model(destination)
        if not torch.equal(check_model_output(restored.model), reference_logits):
            raise ValueError("Reloaded model output differs from the source checkpoint.")
        for path, original in sources.items():
            if path.read_bytes() != original:
                raise ValueError(f"Export input changed: {path.name}. Run the check again.")
    except BaseException:
        shutil.rmtree(destination)
        raise
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a completed watershed development model without retraining.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Check source files and CPU model; write nothing")
    mode.add_argument("--write", action="store_true", help="Create and reload a new versioned development bundle")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--classes", type=Path, default=Path("ai/config/classes.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("ai/models/bundles"))
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve()
        paths = [p.resolve() if p.is_absolute() else (root / p).resolve()
                 for p in (args.checkpoint, args.classes, args.output_dir)]
        checkpoint, classes, output = paths
        models = (root / "ai/models").resolve()
        if not models.is_relative_to(root) or not output.is_relative_to(models):
            raise ValueError("Export output must stay inside this project's ignored ai/models/ directory.")
        destination = output / validate_model_version(args.model_version)
        if destination.exists():
            raise ValueError(f"Bundle already exists: {destination}. Use a new model version; no files were overwritten.")
        print("Mode: " + ("export check (read-only)" if args.check else "development model export"), flush=True)
        files, sources, logits = prepare_bundle(checkpoint, classes, args.model_version)
        metadata = read_json_bytes(files["metadata.json"], "prepared metadata")
        print("Class order: " + ", ".join(metadata["class_ids"]))
        print(f"Source checkpoint epoch: {metadata['training']['epoch']}")
        print(f"CPU output shape: {tuple(logits.shape)}")
        print("Threshold: unselected; every development prediction requires human review.")
        if args.check:
            print(f"Proposed bundle folder: {destination}")
            print("PASS: Export preflight completed. No files were written.")
        else:
            write_bundle(destination, files, sources, logits)
            print(f"Bundle: {destination}")
            print("PASS: Development bundle exported and reloaded successfully on CPU.")
        print("No model was trained or downloaded. No photograph predictions or new accuracy results were produced.")
        return 0
    except KeyboardInterrupt:
        print("STOPPED: Export interrupted; do not record a completed export.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, ImportError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
