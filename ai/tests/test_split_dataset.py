"""Tests for split preparation, using synthetic temporary images only.

Save as ai/tests/test_split_dataset.py. Run from the project root:
    .venv-ai/bin/python -m unittest discover -s ai/tests -p test_split_dataset.py -v

Requires Pillow, PyYAML and the existing validator, dataset and preprocessing
modules. No real manifest, dataset or model is used. Test images are fixtures,
not training photographs.
"""

from __future__ import annotations

import codecs
import contextlib
import csv
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from ai.training.split_dataset import (
    SPLITS, assign_sites, main, prepare_plan, read_settings, split_counts, write_plan,
)
from ai.training.validate_dataset import COLUMNS, load_records

CLASSES = ("check_dam", "farm_pond", "percolation_tank", "contour_trench")
CONFIG = """schema_version: '1.0'
seed: 42
paths:
  data_dir: ai/data
  manifest: ai/data/manifests/private/manifest.csv
  classes: ai/config/classes.json
split:
  group_by: site_id
  train_ratio: 0.70
  validation_ratio: 0.15
  test_ratio: 0.15
model:
  class_ids: [check_dam, farm_pond, percolation_tank, contour_trench]
"""


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "ai/data"
        self.private = self.data / "manifests/private"
        self.private.mkdir(parents=True)
        config_dir = self.root / "ai/config"
        config_dir.mkdir(parents=True)
        self.config = config_dir / "train.yaml"
        self.config.write_text(CONFIG, encoding="utf-8")
        self.classes = config_dir / "classes.json"
        self.classes.write_text(json.dumps({
            "schema_version": "1.0",
            "classes": [{"class_id": c, "label": c} for c in (*CLASSES, "other_unknown")],
        }), encoding="utf-8")
        self.manifest = self.private / "manifest.csv"
        self.rows = []
        # Same class counts and group relationships as a 15-photo development
        # collection, but all image bytes and identifiers are synthetic.
        for class_id, sites in zip(CLASSES, (
            ("dam0", "dam1", "dam2", "dam3"),
            ("pond0", "pond1", "shared", "pond3"),
            ("tank0", "tank1", "tank2"),
            ("trench0", "shared", "trench0", "trench3"),
        )):
            for site in sites:
                self.add_photo(class_id, site)
        self.save_rows()

    def add_photo(self, class_id, site, split=""):
        index = len(self.rows)
        relative = f"raw/{class_id}/fixture_{index}.png"
        path = self.data / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (24 + index, 24), (index, 30, 80)).save(path)
        self.rows.append(dict(zip(COLUMNS, (
            f"fixture_{index}", relative, class_id, site,
            "synthetic unit-test fixture", "generated only for tests, not field data",
            "", "Test region, भारत", hashlib.sha256(path.read_bytes()).hexdigest(), split,
        ))))

    def save_rows(self, bom=False):
        with self.manifest.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\r\n")
            writer.writeheader()
            writer.writerows(self.rows)

    def plan(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return prepare_plan(self.config, self.root, Image)

    def save_plan(self, plan):
        with contextlib.redirect_stdout(io.StringIO()):
            return write_plan(plan)

    def photo_bytes(self):
        return {row["relative_path"]: (self.data / row["relative_path"]).read_bytes() for row in self.rows}

    def test_cli_preview_is_read_only(self):
        original, photos = self.manifest.read_bytes(), self.photo_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = main(["--project-root", str(self.root)])
        self.assertEqual(result, 0, output.getvalue())
        self.assertIn("PROPOSED SPLIT", output.getvalue())
        self.assertIn("NOT been saved", output.getvalue())
        self.assertEqual(self.manifest.read_bytes(), original)
        self.assertEqual(self.photo_bytes(), photos)
        self.assertEqual(list(self.private.iterdir()), [self.manifest])

    def test_global_groups_and_class_coverage(self):
        plan = self.plan()
        self.assertEqual(len(plan.records), 15)
        self.assertEqual(len(plan.assignments), 13)
        for site in plan.assignments:
            splits = {row["split"] for _, row in plan.records if row["site_id"] == site}
            self.assertEqual(len(splits), 1)
        shared = [row for _, row in plan.records if row["site_id"] == "shared"]
        self.assertEqual({row["class_id"] for row in shared}, {"farm_pond", "contour_trench"})
        self.assertEqual(shared[0]["split"], shared[1]["split"])
        self.assertTrue(all(n > 0 for values in split_counts(plan).values() for n in values.values()))

    def test_repeatable_and_independent_of_csv_row_order(self):
        plan = self.plan()
        actual = assign_sites(list(reversed(plan.original_records)), CLASSES, (0.7, 0.15, 0.15), 42)
        self.assertEqual(actual, plan.assignments)

    def test_existing_site_assignments_and_new_related_rows_are_preserved(self):
        self.rows[0]["split"] = "test"
        next(row for row in self.rows if row["site_id"] == "shared")["split"] = "validation"
        self.save_rows()
        plan = self.plan()
        self.assertEqual(plan.assignments["dam0"], "test")
        self.assertEqual(plan.assignments["shared"], "validation")
        self.assertTrue(all(row["split"] == "validation" for _, row in plan.records
                            if row["site_id"] == "shared"))
        self.assertEqual(plan.changed_count, 13)

    def test_conflicting_existing_site_splits_are_rejected(self):
        rows = [row for row in self.rows if row["site_id"] == "shared"]
        rows[0]["split"], rows[1]["split"] = "train", "test"
        self.save_rows()
        with self.assertRaisesRegex(ValueError, "validation failed"):
            self.plan()

    def test_blank_and_mismatched_hashes_are_rejected(self):
        for value, message in (("", "Fill all SHA-256"), ("0" * 64, "validation failed")):
            with self.subTest(value=value):
                self.rows[0]["sha256"] = value
                self.save_rows()
                with self.assertRaisesRegex(ValueError, message):
                    self.plan()

    def test_exact_duplicate_bytes_are_rejected(self):
        first, second = self.rows[:2]
        shutil.copyfile(self.data / first["relative_path"], self.data / second["relative_path"])
        second["sha256"] = first["sha256"]
        self.save_rows()
        with self.assertRaisesRegex(ValueError, "validation failed"):
            self.plan()

    def test_unsupported_manifest_classes_are_not_silently_dropped(self):
        self.rows[0]["class_id"] = "other_unknown"
        self.save_rows()
        with self.assertRaisesRegex(ValueError, "outside model.class_ids"):
            self.plan()

    def test_yaml_duplicate_keys_and_invalid_ratios_are_rejected(self):
        for text in (
            CONFIG + "seed: 99\n",
            CONFIG.replace("train_ratio: 0.70", "train_ratio: .nan"),
            CONFIG.replace("train_ratio: 0.70", "train_ratio: true"),
            CONFIG.replace("train_ratio: 0.70", "train_ratio: 0.60"),
            CONFIG.replace("group_by: site_id", "group_by: image_id"),
        ):
            with self.subTest(config=text):
                self.config.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_settings(self.config, self.root)

    def test_manifest_must_stay_in_private_directory(self):
        for value in ("../manifest.csv", "ai/data/manifests/public.csv"):
            with self.subTest(path=value):
                self.config.write_text(CONFIG.replace("ai/data/manifests/private/manifest.csv", value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_settings(self.config, self.root)

    def test_write_preserves_fields_photos_bom_and_exact_backup_then_is_idempotent(self):
        self.save_rows(bom=True)
        original, photos = self.manifest.read_bytes(), self.photo_bytes()
        plan = self.plan()
        backup = self.save_plan(plan)
        self.assertEqual(backup.read_bytes(), original)
        self.assertTrue(self.manifest.read_bytes().startswith(codecs.BOM_UTF8))
        written = [row for _, row in load_records(self.manifest)]
        for old, new in zip(self.rows, written):
            self.assertEqual({k: v for k, v in old.items() if k != "split"},
                             {k: v for k, v in new.items() if k != "split"})
            self.assertIn(new["split"], SPLITS)
        self.assertEqual(self.photo_bytes(), photos)
        final = self.manifest.read_bytes()
        self.assertIsNone(self.save_plan(self.plan()))
        self.assertEqual(self.manifest.read_bytes(), final)
        self.assertEqual(len(list(self.private.glob("manifest.backup-*.csv"))), 1)

    def test_saved_splits_work_with_existing_dataset_loader(self):
        from ai.training.dataset import WatershedDataset
        self.save_plan(self.plan())
        datasets = {split: WatershedDataset(
            self.data, self.manifest, self.classes, split=split, model_class_ids=CLASSES,
        ) for split in SPLITS}
        self.assertEqual(sum(len(dataset) for dataset in datasets.values()), 15)
        site_sets = {split: {row.site_id for row in dataset.records}
                     for split, dataset in datasets.items()}
        for split, dataset in datasets.items():
            self.assertEqual(dataset.class_ids, CLASSES)
            self.assertEqual(dataset.blank_hash_count, 0)
            self.assertEqual(dataset.unassigned_count, 0)
            for other in SPLITS:
                if split != other:
                    self.assertTrue(site_sets[split].isdisjoint(site_sets[other]))

    def test_changed_inputs_prevent_writing(self):
        targets = (self.manifest, self.config, self.classes, self.data / self.rows[0]["relative_path"])
        for target in targets:
            with self.subTest(path=target):
                plan = self.plan()
                original = target.read_bytes()
                target.write_bytes(original + b"\n")
                try:
                    with self.assertRaisesRegex(ValueError, "changed during this run"):
                        self.save_plan(plan)
                    self.assertEqual(len(list(self.private.glob("manifest.backup-*.csv"))), 0)
                finally:
                    target.write_bytes(original)

    def test_non_split_changes_in_a_plan_are_rejected(self):
        plan = self.plan()
        plan.records[0][1]["region"] = "changed unexpectedly"
        with self.assertRaisesRegex(ValueError, "Only blank split cells"):
            self.save_plan(plan)
        self.assertEqual(self.manifest.read_bytes(), plan.original_bytes)

    def test_failed_atomic_replace_keeps_original_and_backup(self):
        plan = self.plan()
        with patch("ai.training.split_dataset.os.replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                self.save_plan(plan)
        self.assertEqual(self.manifest.read_bytes(), plan.original_bytes)
        backups = list(self.private.glob("manifest.backup-*.csv"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), plan.original_bytes)
        self.assertEqual(list(self.private.glob(".*.tmp")), [])

    def test_missing_training_class_prevents_write(self):
        self.rows = [row for row in self.rows if row["class_id"] != "percolation_tank"]
        self.save_rows()
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "no training photographs"):
            self.save_plan(plan)
        self.assertEqual(self.manifest.read_bytes(), plan.original_bytes)

    def test_too_few_groups_cannot_be_written_as_three_nonempty_splits(self):
        for index, row in enumerate(self.rows):
            row["site_id"] = f"group{index % 2}"
        self.save_rows()
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "validation and test"):
            self.save_plan(plan)
        self.assertEqual(self.manifest.read_bytes(), plan.original_bytes)
        self.assertEqual(list(self.private.iterdir()), [self.manifest])


if __name__ == "__main__":
    unittest.main()
