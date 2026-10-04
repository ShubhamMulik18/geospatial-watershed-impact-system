"""Preview site-grouped train/validation/test assignments for watershed photos.

Save as ai/training/split_dataset.py. Run from the project root:
    .venv-ai/bin/python -m ai.training.split_dataset

The default is a read-only preview. --write fills blank split cells, after
making an exact backup beside the private manifest. Already assigned sites
stay in their original split, even when adding photographs or changing seeds.
Do not edit the config, manifest, classes or photographs while this runs.

Requires validate_dataset.py, Pillow and PyYAML==6.0.3; no PyTorch is needed.
Reads only schema_version, seed, the data/manifest/classes paths, split policy
and model.class_ids from train.yaml. Other training settings are not validated
here. Paths are relative to the project root, as documented in train.yaml.

Algorithm: 64 seeded greedy starts with local single-site improvements. It
prioritizes training-class coverage, nonempty hold-outs, then hold-out class
coverage, then proximity to the configured image/class/site ratios. This is
a heuristic, not a promise of optimal stratification. It uses no model scores.
For small collections, class coverage can substantially change the ratios.

Group globally by site_id, including sites represented in multiple classes.
Related crops/capture sequences must already share their original site group.
Exact duplicates are checked; near duplicates, labels and permissions still
need manual review. Coverage alone does not establish training readiness.

Writing requires every configured class in training and nonempty validation
and test sets. Missing validation/test classes are reported, not hidden. Do
not treat tiny development splits as a reliable final accuracy benchmark.

Only split values change. CSV quoting/line endings may be normalized; the
original bytes are backed up. No images are copied or edited. This script does
not train, tune a confidence threshold or create an inference model bundle.
"""

from __future__ import annotations

import argparse
import codecs
import csv
import io
import math
import os
import random
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

if __name__ == "__main__" and not __package__:
    raise SystemExit("From the project root, run: .venv-ai/bin/python -m ai.training.split_dataset")

from ai.training.validate_dataset import COLUMNS, load_class_ids, load_records, resolve_image, validate

SPLITS = ("train", "validation", "test")
ALGORITHM = "site-greedy-v1 (64 seeded starts)"


@dataclass(frozen=True)
class Settings:
    seed: int
    ratios: tuple[float, ...]
    class_ids: tuple[str, ...]
    data_dir: Path
    manifest: Path
    classes: Path
    config: Path
    config_bytes: bytes


@dataclass
class SplitPlan:
    settings: Settings
    original_bytes: bytes
    original_mode: int
    original_records: list[tuple[int, dict]]
    records: list[tuple[int, dict]]
    assignments: dict[str, str]
    images: dict[str, tuple[Path, tuple[int, ...]]]
    classes_bytes: bytes

    @property
    def changed_count(self) -> int:
        return sum(old["split"] != new["split"] for (_, old), (_, new)
                   in zip(self.original_records, self.records))


def _project_path(root: Path, value, name: str) -> Path:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonblank project-relative path.")
    relative = PurePosixPath(value)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in value
            or PureWindowsPath(value).drive):
        raise ValueError(f"{name} must use / and stay inside the project.")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{name} resolves outside the project.")
    return path


def read_settings(config: Path, project_root: Path) -> Settings:
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("Install PyYAML first: .venv-ai/bin/python -m pip install PyYAML==6.0.3") from exc

    class UniqueSafeLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader, node):
        result = {}
        for key, value in loader.construct_pairs(node):
            if not isinstance(key, str) or key in result:
                raise ValueError("YAML keys must be strings without duplicates.")
            result[key] = value
        return result

    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    config, root = config.resolve(), project_root.resolve()
    source = config.read_bytes()
    try:
        document = yaml.load(source.decode("utf-8-sig"), Loader=UniqueSafeLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise ValueError("train.yaml must have schema_version: '1.0'.")
    for section in ("paths", "split", "model"):
        if not isinstance(document.get(section), dict):
            raise ValueError(f"train.yaml needs a {section} mapping.")
    seed = document.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
    policy = document["split"]
    if set(policy) != {"group_by", "train_ratio", "validation_ratio", "test_ratio"}:
        raise ValueError("split must contain group_by and the three named ratios, without extra keys.")
    if policy["group_by"] != "site_id":
        raise ValueError("This implementation requires split.group_by: site_id.")
    ratios = tuple(policy[f"{split}_ratio"] for split in SPLITS)
    if (any(type(r) not in (int, float) or not math.isfinite(r) or not 0 < r < 1 for r in ratios)
            or not math.isclose(sum(ratios), 1.0, rel_tol=0, abs_tol=1e-9)):
        raise ValueError("Split ratios must be finite numbers between 0 and 1 and sum to 1.")
    class_ids = document["model"].get("class_ids")
    if (not isinstance(class_ids, list) or len(class_ids) < 2
            or any(not isinstance(c, str) or not c for c in class_ids)
            or len(set(class_ids)) != len(class_ids)):
        raise ValueError("model.class_ids must list at least two unique class IDs in order.")
    paths = document["paths"]
    data_dir = _project_path(root, paths.get("data_dir"), "paths.data_dir")
    manifest = _project_path(root, paths.get("manifest"), "paths.manifest")
    classes = _project_path(root, paths.get("classes"), "paths.classes")
    # Backups and real source records belong in the existing private directory.
    private_dir = (data_dir / "manifests/private").resolve()
    if not manifest.is_relative_to(private_dir):
        raise ValueError("The actual manifest must be inside data_dir/manifests/private/.")
    return Settings(seed, tuple(float(r) for r in ratios), tuple(class_ids),
                    data_dir, manifest, classes, config, source)


def assign_sites(records: list[tuple[int, dict]], class_ids: tuple[str, ...],
                 ratios: tuple[float, ...], seed: int) -> dict[str, str]:
    """Return one split per site; never change an already assigned site."""
    positions = {name: i for i, name in enumerate(class_ids)}
    groups, locked = {}, {}
    for _, row in records:
        site = row["site_id"]
        groups.setdefault(site, [0] * len(class_ids))[positions[row["class_id"]]] += 1
        if row["split"]:
            if site in locked and locked[site] != row["split"]:
                raise ValueError(f"Site {site!r} already appears in different splits.")
            locked[site] = row["split"]
    free = sorted(set(groups) - set(locked))
    if not free:
        return dict(locked)
    totals = [sum(g[j] for g in groups.values()) for j in range(len(class_ids))]
    site_support = [sum(g[j] > 0 for g in groups.values()) for j in range(len(class_ids))]
    total_images = sum(totals)
    rng = random.Random(seed)
    best, best_score = None, None
    for _ in range(64):
        assignments = dict(locked)
        counts = [[0] * len(class_ids) for _ in SPLITS]
        site_counts = [0] * len(SPLITS)

        def adjust(site, split_index, direction):
            site_counts[split_index] += direction
            for j, count in enumerate(groups[site]):
                counts[split_index][j] += direction * count

        def score():
            missing_train = sum(n == 0 for n in counts[0])
            empty_holdouts = sum(site_counts[s] == 0 for s in (1, 2))
            missing_holdout_classes = sum(n == 0 for s in (1, 2) for n in counts[s])
            distance = sum((sum(counts[s]) / total_images - ratios[s]) ** 2
                           + (site_counts[s] / len(groups) - ratios[s]) ** 2 for s in range(3))
            distance += sum((counts[s][j] / max(total, 1) - ratios[s]) ** 2
                            for j, total in enumerate(totals) for s in range(3)) / len(class_ids)
            return missing_train, empty_holdouts, missing_holdout_classes, distance

        for site, split in locked.items():
            adjust(site, SPLITS.index(split), 1)
        order = list(free)
        rng.shuffle(order)
        # Place groups containing rarer classes first; shuffle equal-priority ties.
        order.sort(key=lambda site: (min(site_support[j] for j, n in enumerate(groups[site]) if n),
                                     -sum(groups[site])))
        for site in order:
            choices = list(range(3))
            rng.shuffle(choices)
            candidates = []
            for s in choices:
                adjust(site, s, 1)
                candidates.append((score(), s))
                adjust(site, s, -1)
            _, chosen = min(candidates, key=lambda candidate: candidate[0])
            assignments[site] = SPLITS[chosen]
            adjust(site, chosen, 1)
        for _pass in range(8):
            improved = False
            rng.shuffle(order)
            for site in order:
                old = SPLITS.index(assignments[site])
                current, chosen = score(), old
                adjust(site, old, -1)
                for s in range(3):
                    adjust(site, s, 1)
                    candidate = score()
                    adjust(site, s, -1)
                    if candidate < current:
                        current, chosen = candidate, s
                adjust(site, chosen, 1)
                assignments[site] = SPLITS[chosen]
                improved |= chosen != old
            if not improved:
                break
        candidate = score()
        if best_score is None or candidate < best_score:
            best, best_score = dict(assignments), candidate
    return best


def _signature(path: Path) -> tuple[int, ...]:
    info = path.stat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def ensure_unchanged(plan: SplitPlan) -> None:
    settings = plan.settings
    if (settings.manifest.read_bytes() != plan.original_bytes
            or settings.config.read_bytes() != settings.config_bytes
            or settings.classes.read_bytes() != plan.classes_bytes):
        raise ValueError("The manifest or configuration changed during this run. Preview again.")
    for relative, (path, signature) in plan.images.items():
        current = resolve_image(settings.data_dir, relative)
        if current != path or _signature(current) != signature:
            raise ValueError(f"Photograph changed during this run: {relative}. Preview again.")


def prepare_plan(config: Path, project_root: Path, image_module) -> SplitPlan:
    settings = read_settings(config, project_root)
    original_bytes = settings.manifest.read_bytes()
    mode = stat.S_IMODE(settings.manifest.stat().st_mode)
    classes_bytes = settings.classes.read_bytes()
    public_ids = load_class_ids(settings.classes)
    if not set(settings.class_ids).issubset(public_ids):
        raise ValueError("Every configured model class must exist in classes.json.")
    if tuple(c for c in public_ids if c in settings.class_ids) != settings.class_ids:
        raise ValueError("Keep model.class_ids in the same relative order as classes.json.")
    original = load_records(settings.manifest)
    images = {}
    for line, row in original:
        if set(row) != set(COLUMNS) or any(v is None for v in row.values()):
            raise ValueError(f"CSV line {line}: expected exactly {len(COLUMNS)} columns.")
        path = resolve_image(settings.data_dir, row["relative_path"])
        images[row["relative_path"]] = (path, _signature(path))
    print("Checking the CURRENT manifest before planning splits:", flush=True)
    if validate(settings.data_dir, original, public_ids, image_module) != 0:
        raise ValueError("Dataset validation failed. Fix its reported issues first.")
    if any(not row["sha256"] for _, row in original):
        raise ValueError("Fill all SHA-256 fields with hash_manifest.py before planning splits.")
    unsupported = {row["class_id"] for _, row in original} - set(settings.class_ids)
    if unsupported:
        raise ValueError(f"Manifest classes outside model.class_ids: {sorted(unsupported)}. No rows were dropped.")
    assignments = assign_sites(original, settings.class_ids, settings.ratios, settings.seed)
    records = [(line, dict(row, split=assignments[row["site_id"]])) for line, row in original]
    plan = SplitPlan(settings, original_bytes, mode, original, records, assignments, images, classes_bytes)
    ensure_unchanged(plan)
    return plan


def split_counts(plan: SplitPlan):
    counts = {split: {c: 0 for c in plan.settings.class_ids} for split in SPLITS}
    for _, row in plan.records:
        counts[row["split"]][row["class_id"]] += 1
    return counts


def print_plan(plan: SplitPlan) -> None:
    counts = split_counts(plan)
    print(f"\nPROPOSED SPLIT — {ALGORITHM}; seed={plan.settings.seed}")
    print(f"Photographs: {len(plan.records)} | Distinct site groups: {len(plan.assignments)}")
    print("Targets: " + ", ".join(f"{s} {r:.0%}" for s, r in zip(SPLITS, plan.settings.ratios)))
    print(f"{'Split':<13} {'Photos':>7} {'Sites':>7} {'Actual':>9}")
    for split in SPLITS:
        n = sum(counts[split].values())
        sites = sum(value == split for value in plan.assignments.values())
        print(f"{split:<13} {n:>7} {sites:>7} {n / len(plan.records):>9.1%}")
    print(f"\n{'Class':<22} {'train':>7} {'validation':>11} {'test':>7}")
    for c in plan.settings.class_ids:
        print(f"{c:<22} {counts['train'][c]:>7} {counts['validation'][c]:>11} {counts['test'][c]:>7}")
    print("\nSite assignments:")
    originally_assigned = {row["site_id"] for _, row in plan.original_records if row["split"]}
    for site, split in sorted(plan.assignments.items()):
        label = "existing; preserved" if site in originally_assigned else "proposed"
        print(f"  {site} -> {split} ({label})")
    print(f"\nBlank split cells that would be filled: {plan.changed_count}")
    print(f"Existing nonblank split cells preserved: {sum(bool(r['split']) for _, r in plan.original_records)}")
    gaps = [(split, c) for split in SPLITS for c in plan.settings.class_ids if not counts[split][c]]
    for split, c in gaps:
        print(f"COVERAGE GAP: {split} has no {c} photographs.")
    if not gaps:
        print("Every configured class is represented in each proposed split.")
    print("Grouping and class coverage take priority over exact percentages.")
    print("Coverage is a software check, not proof of sufficient data or reliable accuracy.")


def write_plan(plan: SplitPlan) -> Path | None:
    """Fill split cells with an exact backup and an atomic CSV replacement."""
    ensure_unchanged(plan)
    counts = split_counts(plan)
    if any(not count for count in counts["train"].values()):
        raise ValueError("Cannot save: at least one configured class has no training photographs.")
    if any(not sum(counts[split].values()) for split in ("validation", "test")):
        raise ValueError("Cannot save: validation and test must both contain photographs.")
    if len(plan.records) != len(plan.original_records):
        raise ValueError("The proposed plan changed the number of records.")
    for (old_line, old), (new_line, new) in zip(plan.original_records, plan.records):
        if (old_line != new_line or set(new) != set(COLUMNS)
                or any(old[k] != new[k] for k in COLUMNS if k != "split")
                or (old["split"] and old["split"] != new["split"])
                or new["split"] != plan.assignments[old["site_id"]]):
            raise ValueError("Only blank split cells may change, following the site plan.")
    if not plan.changed_count:
        return None
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(row for _, row in plan.records)
    encoding = "utf-8-sig" if plan.original_bytes.startswith(codecs.BOM_UTF8) else "utf-8"
    payload = stream.getvalue().encode(encoding)
    manifest = plan.settings.manifest
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = manifest.with_name(f"{manifest.stem}.backup-{stamp}{manifest.suffix}")
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(plan.original_bytes)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        backup.unlink(missing_ok=True)
        raise
    print(f"Backup: {backup}", flush=True)
    temp_path = None
    try:
        fd, name = tempfile.mkstemp(prefix=f".{manifest.name}.", suffix=".tmp", dir=manifest.parent)
        temp_path = Path(name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, plan.original_mode)
        ensure_unchanged(plan)
        os.replace(temp_path, manifest)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return backup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, help="Defaults to PROJECT_ROOT/ai/config/train.yaml")
    parser.add_argument("--write", action="store_true", help="Back up the private CSV and fill blank split cells")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    config = args.config or root / "ai/config/train.yaml"
    print(f"Mode: {'write' if args.write else 'preview (read-only)'}", flush=True)
    try:
        from PIL import Image
        plan = prepare_plan(config, root, Image)
        print_plan(plan)
        if args.write:
            backup = write_plan(plan)
            if backup is None:
                print("\nPASS: All split cells were already assigned; no changes or backup needed.")
            else:
                print(f"\nPASS: Filled {plan.changed_count} blank split cells; existing assignments preserved.")
                print("Run the dataset validator again before using this manifest.")
        else:
            ensure_unchanged(plan)
            print("\nPASS: Split preview completed. The CSV and photographs were not changed.")
            print("The proposed assignments have NOT been saved. Review them before any --write run.")
        print("This is not a training-readiness or accuracy result. No model was trained.")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted. Check the current manifest before retrying; any printed backup is retained.", file=sys.stderr)
        return 130
    except (OSError, UnicodeError, ValueError, csv.Error, ImportError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print("Check the current manifest before retrying; any printed backup is retained.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
