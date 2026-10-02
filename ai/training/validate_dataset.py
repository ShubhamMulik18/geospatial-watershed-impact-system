"""Check a watershed photograph manifest without changing any files.

Place this file in ai/training/validate_dataset.py, then run from the project:
    .venv-ai/bin/python ai/training/validate_dataset.py

Requires Python 3.10+ and Pillow. No trained model is needed.
Empty capture_date, region, sha256 and split fields are allowed during collection.
Hashes are calculated in memory for checking; this script does not fill the CSV.
Passing these checks does not verify label evidence or readiness for training.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath


COLUMNS = [
    "image_id", "relative_path", "class_id", "site_id", "source",
    "licence_or_permission", "capture_date", "region", "sha256", "split",
]
REQUIRED_VALUES = COLUMNS[:6]
ALLOWED_SPLITS = {"", "train", "validation", "test"}


def load_class_ids(path: Path) -> list[str]:
    """Use the team's class configuration as the source of allowed labels."""
    with path.open(encoding="utf-8-sig") as handle:
        catalog = json.load(handle)
    if not isinstance(catalog, dict) or catalog.get("schema_version") != "1.0":
        raise ValueError("classes.json must be an object with schema_version '1.0'.")
    entries = catalog.get("classes")
    if not isinstance(entries, list) or not entries:
        raise ValueError("classes.json must contain a non-empty classes list.")
    class_ids = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every class entry must have class_id and label fields.")
        class_id, label = entry.get("class_id"), entry.get("label")
        if not isinstance(class_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", class_id):
            raise ValueError(f"Invalid class ID in classes.json: {class_id!r}")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Missing display label for {class_id}.")
        if class_id in class_ids:
            raise ValueError(f"Repeated class ID in classes.json: {class_id}")
        class_ids.append(class_id)
    if "other_unknown" not in class_ids:
        raise ValueError("Keep other_unknown in the public class configuration.")
    return class_ids


def load_records(path: Path) -> list[tuple[int, dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != COLUMNS:
            raise ValueError("CSV header must be exactly: " + ",".join(COLUMNS))
        records = []
        for row in reader:
            records.append((reader.line_num, row))
    if not records:
        raise ValueError("The manifest has no photograph records.")
    return records


def resolve_image(data_dir: Path, relative_path: str) -> Path:
    """Require a portable path relative to ai/data, contained within that folder."""
    relative = PurePosixPath(relative_path)
    if (relative.is_absolute() or ".." in relative.parts
            or "\\" in relative_path or PureWindowsPath(relative_path).drive):
        raise ValueError("relative_path must use / and stay inside ai/data.")
    image_path = (data_dir / relative).resolve()
    if not image_path.is_relative_to(data_dir):
        raise ValueError("relative_path resolves outside ai/data, including through a link.")
    if not image_path.is_file():
        raise ValueError(f"Image file not found: {relative_path}")
    return image_path


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_image(path: Path, image_module) -> tuple[int, int]:
    """Check the file structure, then reopen and decode the actual pixels."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", image_module.DecompressionBombWarning)
        with image_module.open(path) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("Use a single photograph, not a multi-frame image.")
            image.verify()
        with image_module.open(path) as image:
            image.load()
            return image.size


def validate(data_dir: Path, records: list, class_ids: list[str], image_module) -> int:
    errors = []
    counts = Counter()
    sites = defaultdict(set)
    site_splits = defaultdict(set)
    seen_ids, seen_paths, seen_hashes = {}, {}, {}
    readable_images = unassigned = empty_hashes = 0

    for line, original in records:
        if None in original or any(value is None for value in original.values()):
            errors.append(f"CSV line {line}: expected exactly {len(COLUMNS)} columns.")
            continue
        row = {key: value.strip() for key, value in original.items()}
        prefix = f"CSV line {line} ({row['image_id'] or 'missing image_id'})"
        missing = [field for field in REQUIRED_VALUES if not row[field]]
        if missing:
            errors.append(f"{prefix}: missing required values: {', '.join(missing)}.")
            continue
        for key in ("image_id", "relative_path", "class_id", "site_id", "sha256", "split"):
            if row[key] != original[key]:
                errors.append(f"{prefix}: remove surrounding spaces from {key}.")

        image_id, class_id, site_id = row["image_id"], row["class_id"], row["site_id"]
        if image_id in seen_ids:
            errors.append(f"{prefix}: image_id already used on line {seen_ids[image_id]}.")
        else:
            seen_ids[image_id] = line
        if class_id not in class_ids:
            errors.append(f"{prefix}: class_id {class_id!r} is not in classes.json.")
        else:
            counts[class_id] += 1
            sites[class_id].add(site_id)

        captured = row["capture_date"]
        if captured:
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", captured):
                    raise ValueError
                date.fromisoformat(captured)
            except ValueError:
                errors.append(f"{prefix}: capture_date must be a real YYYY-MM-DD date or blank.")

        split = row["split"]
        if split not in ALLOWED_SPLITS:
            errors.append(f"{prefix}: split must be train, validation, test, or blank.")
        elif split:
            site_splits[site_id].add(split)
        else:
            unassigned += 1

        recorded_hash = row["sha256"]
        hash_is_valid = not recorded_hash or bool(re.fullmatch(r"[0-9a-fA-F]{64}", recorded_hash))
        if not hash_is_valid:
            errors.append(f"{prefix}: sha256 must contain 64 hexadecimal characters or be blank.")
        if not recorded_hash:
            empty_hashes += 1

        try:
            image_path = resolve_image(data_dir, row["relative_path"])
            if image_path in seen_paths:
                errors.append(f"{prefix}: same image path as {seen_paths[image_path]}.")
            else:
                seen_paths[image_path] = image_id

            digest = fingerprint(image_path)
            if recorded_hash and hash_is_valid and recorded_hash.lower() != digest:
                errors.append(f"{prefix}: recorded sha256 does not match the file.")
            if digest in seen_hashes:
                errors.append(f"{prefix}: exact duplicate of {seen_hashes[digest]} (same SHA-256).")
            else:
                seen_hashes[digest] = image_id

            width, height = check_image(image_path, image_module)
            readable_images += 1
            print(f"READABLE: {image_id} | {width} x {height} pixels")
        except (OSError, ValueError, SyntaxError, EOFError, RuntimeError,
                image_module.DecompressionBombError, image_module.DecompressionBombWarning) as exc:
            errors.append(f"{prefix}: {exc}")

    for site_id, splits in sorted(site_splits.items()):
        if len(splits) > 1:
            errors.append(f"Site {site_id!r} appears in multiple splits: {', '.join(sorted(splits))}.")

    print("\nManifest counts (including rows that may have errors):")
    for class_id in class_ids:
        print(f"  {class_id}: {counts[class_id]} image(s), {len(sites[class_id])} distinct site(s)")
    print(f"\nReadable images: {readable_images}/{len(records)}")
    print(f"Unassigned splits: {unassigned}")
    print(f"Blank sha256 fields: {empty_hashes} (allowed during collection)")

    if errors:
        print(f"\nFAIL: {len(errors)} issue(s) need attention:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"\nPASS: {len(records)} records passed the dataset checks.")
    print("Collection check only; this is not a training-readiness or accuracy result.")
    print("Review label evidence, permissions and near/edited duplicates manually.")
    print("No files were changed. Blank hashes and splits were left blank.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ai_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=ai_dir / "data")
    parser.add_argument("--manifest", type=Path, help="Defaults to DATA_DIR/manifests/private/manifest.csv")
    parser.add_argument("--classes", type=Path, default=ai_dir / "config/classes.json")
    args = parser.parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow is missing from this Python environment.", file=sys.stderr)
        print("From your project, run: .venv-ai/bin/python -m pip install Pillow", file=sys.stderr)
        return 2

    data_dir = args.data_dir.resolve()
    manifest = args.manifest or data_dir / "manifests/private/manifest.csv"
    try:
        class_ids = load_class_ids(args.classes)
        records = load_records(manifest)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return validate(data_dir, records, class_ids, Image)


if __name__ == "__main__":
    raise SystemExit(main())
