"""Fill missing SHA-256 values in the watershed photograph manifest.

Save as ai/training/hash_manifest.py. Run from the project root:
    .venv-ai/bin/python -m ai.training.hash_manifest          # preview only
    .venv-ai/bin/python -m ai.training.hash_manifest --write  # backup, then save

Requires the existing validate_dataset.py and Pillow. No model is needed.
Only empty sha256 cells are filled. Labels, site IDs, paths, sources, dates,
splits, row order and source photographs are preserved. Existing hashes must
still match their files. CSV quoting and line endings may be normalized.
Backups stay beside the manifest, inside its existing private directory.
Passing this check does not establish training readiness or model accuracy.
"""

from __future__ import annotations

import argparse
import codecs
import csv
import io
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__" and not __package__:
    raise SystemExit(
        "Run from the project root: "
        ".venv-ai/bin/python -m ai.training.hash_manifest"
    )

from ai.training.validate_dataset import (
    COLUMNS,
    fingerprint,
    load_class_ids,
    load_records,
    resolve_image,
    validate,
)


@dataclass
class HashPlan:
    manifest: Path
    data_dir: Path
    original_bytes: bytes
    original_mode: int
    records: list[tuple[int, dict]]
    missing_count: int
    images: dict[str, tuple[Path, tuple[int, ...]]]


def file_signature(path: Path) -> tuple[int, ...]:
    """Detect ordinary file changes while this command is running."""
    info = path.stat()
    return (
        info.st_dev, info.st_ino, info.st_size,
        info.st_mtime_ns, info.st_ctime_ns,
    )


def ensure_unchanged(plan: HashPlan) -> None:
    """Do not save a plan if the CSV or its image files changed meanwhile."""
    if plan.manifest.read_bytes() != plan.original_bytes:
        raise ValueError("The manifest changed during this run. Run the command again.")
    for relative_path, (original_path, original_signature) in plan.images.items():
        current_path = resolve_image(plan.data_dir, relative_path)
        if (current_path != original_path
                or file_signature(current_path) != original_signature):
            raise ValueError(
                f"Image changed during this run: {relative_path}. Run the command again."
            )


def prepare_plan(
    data_dir: Path, manifest: Path, classes: Path, image_module,
) -> HashPlan:
    data_dir, manifest = data_dir.resolve(), manifest.resolve()
    original_bytes = manifest.read_bytes()
    original_mode = stat.S_IMODE(manifest.stat().st_mode)
    class_ids = load_class_ids(classes)
    original_records = load_records(manifest)
    records, images = [], {}
    missing_count = 0

    print(f"Manifest: {manifest}", flush=True)
    print(f"Records: {len(original_records)}", flush=True)
    for line, original in original_records:
        if set(original) != set(COLUMNS) or any(v is None for v in original.values()):
            raise ValueError(f"CSV line {line}: expected exactly {len(COLUMNS)} columns.")
        row = dict(original)
        relative_path = row["relative_path"]
        image_path = resolve_image(data_dir, relative_path)
        images.setdefault(relative_path, (image_path, file_signature(image_path)))
        if row["sha256"] == "":
            row["sha256"] = fingerprint(image_path)
            missing_count += 1
            print(f"HASHED IN MEMORY: {row['image_id']}", flush=True)
        records.append((line, row))

    # The shared validator verifies new AND existing hashes against the images.
    # It also checks labels, duplicates, image decoding and site/split consistency.
    print("\nChecking proposed records in memory; the CSV has not been saved.", flush=True)
    if validate(data_dir, records, class_ids, image_module) != 0:
        raise ValueError("Dataset checks failed. Fix the reported issues before saving hashes.")

    plan = HashPlan(
        manifest, data_dir, original_bytes, original_mode,
        records, missing_count, images,
    )
    ensure_unchanged(plan)
    return plan


def csv_bytes(plan: HashPlan) -> bytes:
    """Keep every existing field value; serialize the proposed hash updates."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(row for _, row in plan.records)
    encoding = "utf-8-sig" if plan.original_bytes.startswith(codecs.BOM_UTF8) else "utf-8"
    return stream.getvalue().encode(encoding)


def write_plan(plan: HashPlan) -> Path | None:
    """Save an exact backup, then atomically replace the CSV on the same disk."""
    ensure_unchanged(plan)
    if plan.missing_count == 0:
        return None

    payload = csv_bytes(plan)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = plan.manifest.with_name(
        f"{plan.manifest.stem}.backup-{stamp}{plan.manifest.suffix}"
    )
    # Exclusive creation prevents an existing backup from being overwritten.
    backup_fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(backup_fd, "wb") as handle:
            handle.write(plan.original_bytes)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        backup.unlink(missing_ok=True)
        raise
    print(f"Backup: {backup}", flush=True)

    temp_path = None
    try:
        fd, name = tempfile.mkstemp(
            prefix=f".{plan.manifest.name}.", suffix=".tmp", dir=plan.manifest.parent,
        )
        temp_path = Path(name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, plan.original_mode)
        ensure_unchanged(plan)
        os.replace(temp_path, plan.manifest)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return backup


def main(argv: list[str] | None = None) -> int:
    ai_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--data-dir", type=Path, default=ai_dir / "data")
    parser.add_argument(
        "--manifest", type=Path, help="Defaults to DATA_DIR/manifests/private/manifest.csv",
    )
    parser.add_argument("--classes", type=Path, default=ai_dir / "config/classes.json")
    parser.add_argument("--write", action="store_true", help="Create a backup and fill missing hashes.")
    args = parser.parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow is missing. Use your .venv-ai Python environment.", file=sys.stderr)
        return 2

    data_dir = args.data_dir.resolve()
    manifest = args.manifest or data_dir / "manifests/private/manifest.csv"
    print(f"Mode: {'write' if args.write else 'preview'}", flush=True)
    try:
        plan = prepare_plan(data_dir, manifest, args.classes, Image)
        if plan.missing_count == 0:
            print(f"\nPASS: All {len(plan.records)} records already have verified SHA-256 values.")
            print("No files were changed; no backup was needed.")
        elif args.write:
            write_plan(plan)
            print(f"\nPASS: Filled {plan.missing_count} missing SHA-256 values.")
            print("Other CSV values and source photographs were preserved.")
            print("Run validate_dataset.py and the dataset collection check again.")
        else:
            print(
                f"\nPASS: Preview complete; {plan.missing_count} missing SHA-256 values "
                "would be filled."
            )
            print("No files were changed. Run again with --write to save.")
        print("No split assignments were made. This is not a training or accuracy result.")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted. Rerun the command to check the current manifest.", file=sys.stderr)
        return 130
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print("Check the current manifest before retrying. Any backup already printed is retained.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
