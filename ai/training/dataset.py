"""Load watershed photographs and their verified CSV labels.

Save as ai/training/dataset.py. Run FROM THE PROJECT ROOT:
    .venv-ai/bin/python -m ai.training.dataset --check-collection

Requires the existing ai/training/validate_dataset.py and
ai/inference/preprocess.py. Run the dataset validator before this loading check.

WatershedDataset is a map-style dataset: __len__ reports its size and
__getitem__ returns (CPU float32 image tensor, integer class index). PyTorch's
DataLoader can batch these into (N, 3, 224, 224) images and int64 labels.
PyTorch is imported only when tensors are requested, not to inspect metadata.

Class order comes from classes.json, excluding other_unknown by default.
An explicit model_class_ids sequence can select another ordered subset later.
Never infer the mapping separately from the classes present in each split.
Export this exact class_ids order with the future model bundle.

split='collection' is ONLY for a loading check; it may include unassigned rows.
Real train/validation/test datasets require assigned splits and recorded hashes.
The same site cannot occur across splits, and exact duplicate files are rejected.
Files are hashed once during construction. Keep the dataset files unchanged
during a run. Near duplicates and label/permission evidence need human review.

Training uses the shared preprocessing, then a 50% horizontal flip. This is a
conservative initial augmentation choice, not a tuned training recipe.
Validation/test/collection use preprocess_image unchanged. Set the PyTorch RNG
seed in the future training script. No augmentation creates new physical sites.

This file never edits the manifest, assigns splits, saves images, downloads
weights or trains a model. It uses Python module imports, without sys.path edits.

References:
https://docs.pytorch.org/docs/2.14/data.html
https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

if __name__ == "__main__" and not __package__:
    raise SystemExit(
        "From the project root, run: "
        ".venv-ai/bin/python -m ai.training.dataset --check-collection"
    )

from ai.inference.preprocess import preprocess_image
from ai.training.validate_dataset import (
    ALLOWED_SPLITS, COLUMNS, REQUIRED_VALUES,
    fingerprint, load_class_ids, load_records, resolve_image,
)

if TYPE_CHECKING:
    from torch import Tensor


@dataclass(frozen=True)
class PhotoRecord:
    image_id: str
    path: Path
    class_id: str
    site_id: str
    split: str
    recorded_sha256: str


def _read_photos(data_dir: Path, manifest: Path, public_ids: Sequence[str]):
    """Reuse the validator's CSV/path rules and guard against split leakage."""
    photos = []
    seen_ids, seen_paths, seen_hashes = set(), set(), {}
    site_splits = defaultdict(set)
    for line, row in load_records(manifest):
        prefix = f"CSV line {line}"
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{prefix}: expected exactly {len(COLUMNS)} columns.")
        missing = [key for key in REQUIRED_VALUES if not row[key].strip()]
        if missing:
            raise ValueError(f"{prefix}: missing required values: {', '.join(missing)}.")
        for key in ("image_id", "relative_path", "class_id", "site_id", "sha256", "split"):
            if row[key] != row[key].strip():
                raise ValueError(f"{prefix}: remove surrounding spaces from {key}.")
        if row["class_id"] not in public_ids:
            raise ValueError(f"{prefix}: class_id {row['class_id']!r} is not in classes.json.")
        if row["split"] not in ALLOWED_SPLITS:
            raise ValueError(f"{prefix}: split must be train, validation, test, or blank.")
        recorded_hash = row["sha256"].lower()
        if recorded_hash and not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
            raise ValueError(f"{prefix}: sha256 must have 64 hexadecimal characters or be blank.")
        path = resolve_image(data_dir, row["relative_path"])
        if row["image_id"] in seen_ids or path in seen_paths:
            raise ValueError(f"{prefix}: repeated image_id or image path.")
        seen_ids.add(row["image_id"])
        seen_paths.add(path)
        digest = fingerprint(path)
        if recorded_hash and recorded_hash != digest:
            raise ValueError(f"{prefix}: recorded sha256 does not match the file.")
        if digest in seen_hashes:
            raise ValueError(f"{prefix}: exact duplicate of {seen_hashes[digest]}.")
        seen_hashes[digest] = row["image_id"]
        if row["split"]:
            site_splits[row["site_id"]].add(row["split"])
        photos.append(PhotoRecord(
            row["image_id"], path, row["class_id"], row["site_id"],
            row["split"], recorded_hash,
        ))
    for site_id, splits in site_splits.items():
        if len(splits) > 1:
            raise ValueError(f"Site {site_id!r} appears in multiple splits: {sorted(splits)}.")
    return tuple(photos)


def _training_flip(tensor: Tensor) -> Tensor:
    """Flip only the width dimension; use PyTorch's seeded random generator."""
    import torch

    return tensor.flip(dims=(-1,)) if torch.rand(()).item() < 0.5 else tensor


class WatershedDataset:
    """Map-style Dataset protocol, usable directly by torch.utils.data.DataLoader.

    Example, AFTER creating and validating the grouped split:
        train = WatershedDataset(data_dir, manifest, classes, split="train")
        validation = WatershedDataset(
            data_dir, manifest, classes, split="validation",
            model_class_ids=train.class_ids,
        )

    __getitem__ returns (image_tensor, target_index). Metadata is in records.
    A class absent from validation/test keeps its index and gets a zero count.
    Missing training classes or selected rows outside model_class_ids are errors.
    """

    def __init__(
        self, data_dir: str | Path, manifest: str | Path, classes: str | Path,
        *, split: str, model_class_ids: Sequence[str] | None = None,
    ):
        if split not in {"collection", "train", "validation", "test"}:
            raise ValueError("Choose collection, train, validation or test explicitly.")
        public_ids = load_class_ids(Path(classes))
        if model_class_ids is not None and (
            isinstance(model_class_ids, (str, bytes)) or not isinstance(model_class_ids, Sequence)
        ):
            raise ValueError("model_class_ids must be an ordered list or tuple of class IDs.")
        class_ids = tuple(model_class_ids) if model_class_ids is not None else tuple(
            class_id for class_id in public_ids if class_id != "other_unknown"
        )
        if (not class_ids or any(not isinstance(item, str) for item in class_ids)
                or len(set(class_ids)) != len(class_ids)
                or not set(class_ids).issubset(public_ids)):
            raise ValueError("model_class_ids must contain unique IDs from classes.json.")
        self.class_ids = class_ids
        self.class_to_idx = {class_id: index for index, class_id in enumerate(class_ids)}
        self.split = split
        photos = _read_photos(Path(data_dir).resolve(), Path(manifest), public_ids)
        self.manifest_count = len(photos)
        self.unassigned_count = sum(not photo.split for photo in photos)
        self.blank_hash_count = sum(not photo.recorded_sha256 for photo in photos)
        if split != "collection":
            if self.unassigned_count:
                raise ValueError(
                    "Splits are still unassigned. Use --check-collection now; "
                    "prepare site-grouped splits before training or evaluation."
                )
            if self.blank_hash_count:
                raise ValueError("Record verified SHA-256 hashes before training or evaluation.")
        self.records = tuple(photo for photo in photos if split == "collection" or photo.split == split)
        if not self.records:
            raise ValueError(f"No photographs are assigned to {split!r}.")
        unsupported = {photo.class_id for photo in self.records} - set(class_ids)
        if unsupported:
            raise ValueError(
                f"Selected photos have classes outside the model class order: {sorted(unsupported)}. "
                "Choose model_class_ids explicitly; do not silently relabel or drop these photos."
            )
        counts = Counter(photo.class_id for photo in self.records)
        self.class_counts = {class_id: counts[class_id] for class_id in class_ids}
        if split == "train":
            missing = [class_id for class_id, count in self.class_counts.items() if not count]
            if missing:
                raise ValueError(f"Training split has no examples for: {', '.join(missing)}.")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[Tensor, int]:
        photo = self.records[index]
        tensor = preprocess_image(photo.path)
        if self.split == "train":
            tensor = _training_flip(tensor)
        return tensor, self.class_to_idx[photo.class_id]


def main(argv: list[str] | None = None) -> int:
    ai_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Check watershed image-and-label loading.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-collection", action="store_true", help="Allow blank splits/hashes")
    mode.add_argument("--split", choices=("train", "validation", "test"))
    parser.add_argument("--data-dir", type=Path, default=ai_dir / "data")
    parser.add_argument("--manifest", type=Path, help="Defaults to DATA_DIR/manifests/private/manifest.csv")
    parser.add_argument("--classes", type=Path, default=ai_dir / "config/classes.json")
    parser.add_argument("--model-class-ids", nargs="+", help="Explicit ordered subset of public class IDs")
    args = parser.parse_args(argv)
    split = "collection" if args.check_collection else args.split
    manifest = args.manifest or args.data_dir / "manifests/private/manifest.csv"
    try:
        dataset = WatershedDataset(
            args.data_dir, manifest, args.classes, split=split,
            model_class_ids=args.model_class_ids,
        )
        import torch
        from torch.utils.data import DataLoader

        torch.manual_seed(42)  # Repeatable CLI check; the training script owns its own seed.
        print(f"Mode: {split}")
        print(f"Selected photographs: {len(dataset)}/{dataset.manifest_count}")
        print(f"Unassigned splits in manifest: {dataset.unassigned_count}")
        print(f"Blank SHA-256 fields: {dataset.blank_hash_count}")
        print("\nFixed class mapping:")
        for class_id, index in dataset.class_to_idx.items():
            print(f"  {index}: {class_id} | {dataset.class_counts[class_id]} image(s)")
        loader = DataLoader(dataset, batch_size=4, shuffle=False, num_workers=0)
        loaded = 0
        print()
        for images, targets in loader:
            if (images.shape[1:] != (3, 224, 224) or images.dtype != torch.float32
                    or images.device.type != "cpu" or not torch.isfinite(images).all().item()):
                raise ValueError("Expected finite CPU float32 images with shape (N, 3, 224, 224).")
            if targets.dtype != torch.int64:
                raise ValueError("Expected int64 batch labels.")
            if loaded == 0:
                print(f"First batch: images={tuple(images.shape)}, labels={tuple(targets.shape)}")
            for target in targets.tolist():
                photo = dataset.records[loaded]
                if target != dataset.class_to_idx[photo.class_id]:
                    raise ValueError(f"Label mismatch for {photo.image_id}.")
                print(f"LOADED: {photo.image_id} | {photo.class_id} | label={target}")
                loaded += 1
        print(f"\nPASS: Loaded {loaded}/{len(dataset)} photographs with labels from the manifest.")
        print("Loading check only; this is not a training-readiness or accuracy result.")
        print("No manifest, split assignments or source photographs were changed.")
        return 0
    except (OSError, UnicodeError, ValueError, csv.Error, ImportError, RuntimeError,
            SyntaxError, EOFError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
