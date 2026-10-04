"""Train the first watershed development classifier on CPU.

Save as ai/training/train.py. Run from the project root:
    .venv-ai/bin/python -m ai.training.train --check
    .venv-ai/bin/python -m ai.training.train --development-run

--check validates configuration and loads train/validation tensors. It does
not construct a model, download weights, create a run directory or train.
--development-run repeats these checks, loads ImageNet MobileNetV2 V2 weights
(downloading them if necessary), and trains only the new classification head.

Requires the existing train.yaml, split_dataset.py, dataset.py, model.py,
preprocess.py and validate_dataset.py. Paths in YAML are project-relative.
Only the currently configured CPU/frozen-backbone/Adam baseline is supported.
Unsupported or misspelled options fail instead of being silently ignored.

Only training tensors update parameters. Validation chooses best.pt by macro
F1 across the fixed class order, then lower validation loss to break ties.
Precision/recall/F1 use zero when their denominator is zero. Per-class support
and the confusion matrix (true rows, predicted columns) are also recorded.
The dataset's integrity checks hash ALL manifest files, including test files;
this trainer never constructs test tensors or calculates test predictions.

Each run creates a new directory inside ai/models/ containing best.pt,
history.json, metadata.json and config.yaml. These stay under the existing
ignored models folder. The checkpoint contains a state_dict, ordered classes,
preprocessing and provenance, not a pickled model or a resumable optimizer.
It is a DEVELOPMENT checkpoint, not the final backend inference bundle.
No confidence threshold, Other/Unknown prediction or test result is produced.

With the current 7 train / 4 validation photos, use this to check the training
pipeline. The resulting scores cannot establish reliable real-world accuracy.
Keep configuration, manifest and photographs unchanged during a run.

References:
https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html
https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path, PurePosixPath, PureWindowsPath

if __name__ == "__main__" and not __package__:
    raise SystemExit("From the project root, run: .venv-ai/bin/python -m ai.training.train --check")

import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader

from ai.inference.model import WatershedMobileNetV2
from ai.training.dataset import WatershedDataset
from ai.training.split_dataset import Settings, read_settings
from ai.training.validate_dataset import load_class_ids, load_records, resolve_image

PROFILE = "mobilenet_v2_imagenet1k_v2"
PREPROCESSING = {
    "profile": PROFILE, "exif_orientation": True, "color_mode": "RGB",
    "alpha_background": "white", "resize_shorter_edge": 232,
    "center_crop": [224, 224], "interpolation": "bilinear", "antialias": True,
    "pixel_scale": 1.0 / 255.0,
    "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225],
}
LIMITATION = "Development run on a small collection; scores are not reliable real-world accuracy estimates."


@dataclass(frozen=True)
class TrainSettings:
    shared: Settings
    output_dir: Path
    epochs: int
    batch_size: int
    learning_rate: float
    weight_decay: float


@dataclass
class PreparedRun:
    settings: TrainSettings
    train: WatershedDataset
    validation: WatershedDataset
    source_bytes: dict[Path, bytes]
    image_signatures: dict[Path, tuple[int, ...]]
    counts: dict
    fingerprints: dict[str, str]


def _keys(mapping, expected: set[str], name: str) -> None:
    if not isinstance(mapping, dict) or set(mapping) != expected:
        raise ValueError(f"{name} must contain exactly: {', '.join(sorted(expected))}.")


def read_train_settings(config: Path, project_root: Path) -> TrainSettings:
    # Reuse the existing duplicate-key, schema, seed, split and input-path checks.
    shared = read_settings(config, project_root)
    doc = yaml.safe_load(shared.config_bytes.decode("utf-8-sig"))
    _keys(doc, {"schema_version", "seed", "paths", "split", "model", "preprocessing", "training"}, "train.yaml")
    _keys(doc["paths"], {"data_dir", "manifest", "classes", "output_dir"}, "paths")
    _keys(doc["model"], {"architecture", "pretrained_weights", "freeze_backbone", "class_ids"}, "model")
    _keys(doc["preprocessing"], {"profile"}, "preprocessing")
    fields = {"epochs", "batch_size", "device", "num_workers", "optimizer", "learning_rate",
              "weight_decay", "loss", "class_weighting", "checkpoint_metric", "checkpoint_mode"}
    _keys(doc["training"], fields, "training")
    model, training = doc["model"], doc["training"]
    if (model["architecture"] != "mobilenet_v2"
            or model["pretrained_weights"] != "IMAGENET1K_V2"
            or model["freeze_backbone"] is not True):
        raise ValueError("Use mobilenet_v2, IMAGENET1K_V2 and freeze_backbone: true for this baseline.")
    if doc["preprocessing"]["profile"] != PROFILE:
        raise ValueError(f"Use preprocessing.profile: {PROFILE}.")
    fixed = {"device": "cpu", "optimizer": "adam", "loss": "cross_entropy",
             "class_weighting": "none", "checkpoint_metric": "validation_macro_f1", "checkpoint_mode": "max"}
    for key, expected in fixed.items():
        if training[key] != expected:
            raise ValueError(f"This baseline requires training.{key}: {expected}.")
    if type(training["num_workers"]) is not int or training["num_workers"] != 0:
        raise ValueError("This baseline requires training.num_workers: 0.")
    for key in ("epochs", "batch_size"):
        if type(training[key]) is not int or training[key] < 1:
            raise ValueError(f"training.{key} must be a positive integer.")
    for key in ("learning_rate", "weight_decay"):
        value = training[key]
        if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                or (key == "learning_rate" and value == 0)):
            raise ValueError(f"training.{key} must be finite and {'positive' if key == 'learning_rate' else 'nonnegative'}.")
    if shared.seed >= 2**63:
        raise ValueError("seed must be less than 2**63.")
    if "other_unknown" in shared.class_ids:
        raise ValueError("other_unknown is a public fallback, not a trained class in this baseline.")
    value, root = doc["paths"]["output_dir"], project_root.resolve()
    if (not isinstance(value, str) or not value or value != value.strip()
            or PurePosixPath(value).is_absolute() or ".." in PurePosixPath(value).parts
            or "\\" in value or PureWindowsPath(value).drive):
        raise ValueError("paths.output_dir must be a project-relative path using /.")
    output_dir, models_dir = (root / value).resolve(), (root / "ai/models").resolve()
    if not models_dir.is_relative_to(root) or not output_dir.is_relative_to(models_dir):
        raise ValueError("paths.output_dir must stay inside the project's ignored ai/models/ directory.")
    return TrainSettings(shared, output_dir, training["epochs"], training["batch_size"],
                         float(training["learning_rate"]), float(training["weight_decay"]))


def _signature(path: Path) -> tuple[int, ...]:
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def ensure_unchanged(prepared: PreparedRun) -> None:
    for path, original in prepared.source_bytes.items():
        if path.read_bytes() != original:
            raise ValueError(f"Input changed during the run: {path.name}. Start a new run after reviewing it.")
    for path, original in prepared.image_signatures.items():
        if _signature(path) != original:
            raise ValueError(f"Photograph changed during the run: {path.name}. Start a new run after revalidating it.")


def prepare_run(settings: TrainSettings) -> PreparedRun:
    s = settings.shared
    sources = {s.config: s.config_bytes, s.classes: s.classes.read_bytes(), s.manifest: s.manifest.read_bytes()}
    public_ids = load_class_ids(s.classes)
    if tuple(c for c in public_ids if c in s.class_ids) != s.class_ids:
        raise ValueError("model.class_ids must follow their public classes.json order.")
    rows = load_records(s.manifest)
    signatures = {}
    for _, row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("A manifest row has the wrong number of columns.")
        if row["class_id"] not in s.class_ids:
            raise ValueError(f"Manifest class {row['class_id']!r} is outside the configured model classes.")
        signatures[resolve_image(s.data_dir, row["relative_path"])] = _signature(resolve_image(s.data_dir, row["relative_path"]))
    # Each constructor verifies hashes and global site isolation across ALL rows.
    train = WatershedDataset(s.data_dir, s.manifest, s.classes, split="train", model_class_ids=s.class_ids)
    validation = WatershedDataset(s.data_dir, s.manifest, s.classes, split="validation", model_class_ids=s.class_ids)
    counts = {}
    for split in ("train", "validation", "test"):
        selected = [row for _, row in rows if row["split"] == split]
        counts[split] = {"photos": len(selected), "sites": len({row["site_id"] for row in selected}),
                         "classes": {c: sum(row["class_id"] == c for row in selected) for c in s.class_ids}}
        if not selected:
            raise ValueError(f"The {split} group is empty. Review the saved split before training.")
    fingerprints = {"config_sha256": hashlib.sha256(sources[s.config]).hexdigest(),
                    "classes_sha256": hashlib.sha256(sources[s.classes]).hexdigest(),
                    "manifest_sha256": hashlib.sha256(sources[s.manifest]).hexdigest()}
    prepared = PreparedRun(settings, train, validation, sources, signatures, counts, fingerprints)
    ensure_unchanged(prepared)
    return prepared


def _check_batch(images: torch.Tensor, targets: torch.Tensor, classes: int) -> None:
    if (images.ndim != 4 or tuple(images.shape[1:]) != (3, 224, 224)
            or images.dtype != torch.float32 or images.device.type != "cpu"
            or not torch.isfinite(images).all().item()):
        raise ValueError("Expected finite CPU float32 images with shape (N, 3, 224, 224).")
    if (targets.dtype != torch.int64 or targets.device.type != "cpu" or targets.ndim != 1
            or len(targets) != len(images) or not len(targets)
            or targets.min().item() < 0 or targets.max().item() >= classes):
        raise ValueError("Expected one int64 class index per image in the fixed class order.")


def check_data(prepared: PreparedRun) -> None:
    torch.manual_seed(prepared.settings.shared.seed)
    print("Fixed class order: " + ", ".join(prepared.settings.shared.class_ids))
    for split, dataset in (("train", prepared.train), ("validation", prepared.validation)):
        loaded = 0
        for images, targets in DataLoader(dataset, batch_size=prepared.settings.batch_size, num_workers=0):
            _check_batch(images, targets, len(dataset.class_ids))
            loaded += len(targets)
        print(f"PASS: {split} tensors loaded: {loaded}/{len(dataset)}")
    missing = [c for c, n in prepared.validation.class_counts.items() if not n]
    if missing:
        print("WARNING: validation has no examples for: " + ", ".join(missing))
    print(f"Reserved test photographs: {prepared.counts['test']['photos']} (metadata only; no test predictions)")
    ensure_unchanged(prepared)
    print(LIMITATION)


def metrics_from_confusion(matrix: torch.Tensor, class_ids: tuple[str, ...], loss: float) -> dict:
    """Macro F1 includes every configured class, even a class with zero support."""
    total = int(matrix.sum().item())
    if total == 0 or not math.isfinite(loss):
        raise ValueError("Cannot calculate metrics for an empty group or non-finite loss.")
    per_class = {}
    for i, class_id in enumerate(class_ids):
        tp, support, predicted = int(matrix[i, i]), int(matrix[i].sum()), int(matrix[:, i].sum())
        per_class[class_id] = {"support": support, "precision": tp / predicted if predicted else 0.0,
                               "recall": tp / support if support else 0.0,
                               "f1": 2 * tp / (support + predicted) if support + predicted else 0.0}
    return {"loss": loss, "accuracy": int(matrix.diag().sum()) / total,
            "macro_f1": sum(item["f1"] for item in per_class.values()) / len(class_ids),
            "samples": total, "per_class": per_class, "confusion_matrix": matrix.tolist()}


def run_epoch(model: nn.Module, loader: DataLoader, class_ids: tuple[str, ...], optimizer=None) -> dict:
    training = optimizer is not None
    model.train(training)  # Shared model keeps frozen features and BatchNorm in eval mode.
    matrix = torch.zeros((len(class_ids), len(class_ids)), dtype=torch.int64)
    loss_sum, count = 0.0, 0
    with torch.enable_grad() if training else torch.inference_mode():
        for images, targets in loader:
            _check_batch(images, targets, len(class_ids))
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            if tuple(logits.shape) != (len(targets), len(class_ids)) or not torch.isfinite(logits).all().item():
                raise ValueError("Model returned invalid logits.")
            loss = nn.functional.cross_entropy(logits, targets)  # Raw logits, not softmax probabilities.
            if not torch.isfinite(loss).item():
                raise ValueError("Loss is not finite.")
            if training:
                loss.backward()
                for parameter in model.parameters():
                    if parameter.requires_grad and (parameter.grad is None or not torch.isfinite(parameter.grad).all().item()):
                        raise ValueError("A trainable parameter has missing or non-finite gradients.")
                optimizer.step()
            indices = targets * len(class_ids) + logits.detach().argmax(dim=1)
            matrix += torch.bincount(indices, minlength=len(class_ids) ** 2).reshape(matrix.shape)
            loss_sum += float(loss.detach()) * len(targets)
            count += len(targets)
    if not count:
        raise ValueError("An epoch received no photographs.")
    return metrics_from_confusion(matrix, class_ids, loss_sum / count)


def is_better(candidate: dict, best: dict | None) -> bool:
    return best is None or (candidate["macro_f1"], -candidate["loss"]) > (best["macro_f1"], -best["loss"])


def atomic_write(path: Path, writer) -> None:
    """Replace only this run's file after its complete new bytes reach disk."""
    fd, name = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            writer(stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, value) -> None:
    data = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
    atomic_write(path, lambda stream: stream.write(data))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def train_model(prepared: PreparedRun) -> Path:
    """Called only after preflight; uses train and validation, never a test loader."""
    ensure_unchanged(prepared)
    settings, shared = prepared.settings, prepared.settings.shared
    random.seed(shared.seed)
    torch.manual_seed(shared.seed)
    print("Loading ImageNet MobileNetV2 V2 weights; the first run may download them.", flush=True)
    model = WatershedMobileNetV2(shared.class_ids, pretrained=True, freeze_backbone=True).to("cpu")
    ensure_unchanged(prepared)
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                                 lr=settings.learning_rate, weight_decay=settings.weight_decay)
    generator = torch.Generator().manual_seed(shared.seed)
    train_loader = DataLoader(prepared.train, batch_size=settings.batch_size, shuffle=True,
                              generator=generator, num_workers=0, drop_last=False)
    validation_loader = DataLoader(prepared.validation, batch_size=settings.batch_size, shuffle=False,
                                   num_workers=0, drop_last=False)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("dev-%Y%m%dT%H%M%SZ-"),
                                    dir=settings.output_dir))
    versions = {name: version(name) for name in ("torch", "torchvision", "Pillow", "PyYAML")}
    metadata = {
        "schema_version": "1.0", "purpose": "development", "status": "running", "started_at": _now(),
        "limitation": LIMITATION, "architecture": "mobilenet_v2", "initial_weights": "IMAGENET1K_V2",
        "backbone_frozen": True, "device": "cpu", "seed": shared.seed,
        "class_ids": list(shared.class_ids), "class_to_idx": {c: i for i, c in enumerate(shared.class_ids)},
        "preprocessing": PREPROCESSING, "training_horizontal_flip_probability": 0.5,
        "counts": prepared.counts, "input_fingerprints": prepared.fingerprints,
        "python_version": platform.python_version(), "package_versions": versions,
        "selection": "Maximum validation macro F1; lower validation loss breaks ties; otherwise keep earlier epoch.",
        "zero_division": 0, "confusion_matrix_axes": {"rows": "true", "columns": "predicted"},
        "test_evaluated": False, "confidence_threshold": None, "epochs_requested": settings.epochs,
        "epochs_completed": 0, "best_epoch": None, "best_validation": None,
        "reproducibility": "Seeded CPU run; identical results across software/hardware versions are not guaranteed.",
    }
    history, best = [], None
    print(f"Run directory: {run_dir}", flush=True)
    try:
        atomic_write(run_dir / "config.yaml", lambda stream: stream.write(shared.config_bytes))
        write_json(run_dir / "metadata.json", metadata)
        for epoch in range(1, settings.epochs + 1):
            ensure_unchanged(prepared)
            train_metrics = run_epoch(model, train_loader, shared.class_ids, optimizer)
            validation_metrics = run_epoch(model, validation_loader, shared.class_ids)
            ensure_unchanged(prepared)
            if is_better(validation_metrics, best):
                checkpoint = {
                    "format_version": "1.0", "purpose": "development_checkpoint",
                    "architecture": "mobilenet_v2", "initial_weights": "IMAGENET1K_V2",
                    "backbone_frozen": True, "class_ids": list(shared.class_ids),
                    "preprocessing": PREPROCESSING, "seed": shared.seed, "epoch": epoch,
                    "validation_metrics": validation_metrics, "input_fingerprints": prepared.fingerprints,
                    "package_versions": versions, "confidence_threshold": None, "test_evaluated": False,
                    "model_state_dict": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                }
                atomic_write(run_dir / "best.pt", lambda stream: torch.save(checkpoint, stream))
                best = validation_metrics
                metadata.update(best_epoch=epoch, best_validation=best)
            history.append({"epoch": epoch, "train": train_metrics, "validation": validation_metrics})
            write_json(run_dir / "history.json", history)
            metadata["epochs_completed"] = epoch
            write_json(run_dir / "metadata.json", metadata)
            print(f"Epoch {epoch}/{settings.epochs} | train loss {train_metrics['loss']:.4f} | "
                  f"validation loss {validation_metrics['loss']:.4f} | "
                  f"validation macro F1 {validation_metrics['macro_f1']:.4f}", flush=True)
        ensure_unchanged(prepared)
        metadata.update(status="completed", finished_at=_now())
        write_json(run_dir / "metadata.json", metadata)
    except BaseException as exc:
        metadata.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                        finished_at=_now(), error=f"{type(exc).__name__}: {exc}")
        try:
            write_json(run_dir / "metadata.json", metadata)
        except OSError as save_error:
            print(f"Could not record failure status: {save_error}. Treat this run as incomplete.", file=sys.stderr)
        raise
    print(f"PASS: Development training completed. Best epoch: {metadata['best_epoch']}")
    print(f"Checkpoint: {run_dir / 'best.pt'}")
    print(LIMITATION)
    print("Test evaluation and confidence-threshold selection have not been performed.")
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or train the watershed development classifier.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate inputs and tensors; no model or output files")
    mode.add_argument("--development-run", action="store_true", help="Train the head and save a development checkpoint")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, help="Config path relative to project root; default ai/config/train.yaml")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    config = args.config or Path("ai/config/train.yaml")
    if not config.is_absolute():
        config = root / config
    try:
        print("Mode: " + ("preflight check" if args.check else "development training"), flush=True)
        prepared = prepare_run(read_train_settings(config, root))
        check_data(prepared)
        if args.check:
            print("PASS: Training preflight completed. No model was trained or downloaded; no files were written.")
        else:
            train_model(prepared)
        return 0
    except KeyboardInterrupt:
        print("STOPPED: Run interrupted. Do not mark training as completed.", file=sys.stderr)
        return 130
    except (OSError, ValueError, csv.Error, ImportError, RuntimeError, EOFError, SyntaxError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
