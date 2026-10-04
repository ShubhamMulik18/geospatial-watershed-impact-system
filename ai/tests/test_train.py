"""Software tests for ai/training/train.py; no network or field photos needed.

Save as ai/tests/test_train.py. Run from the project root:
    .venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_train.py' -v

All images, CSVs and checkpoints are temporary synthetic test fixtures.
Training integration tests replace ONLY the pretrained-weight download with
random initialization. They still exercise the real shared MobileNetV2,
preprocessing, dataset, optimizer, validation and checkpoint serialization.
These tests provide no evidence of watershed classification accuracy.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
import yaml
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ai.inference.model import WatershedMobileNetV2
from ai.training import dataset as dataset_module
from ai.training import train
from ai.training.validate_dataset import COLUMNS

CLASS_IDS = ("check_dam", "farm_pond", "percolation_tank", "contour_trench")


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "ai/data"
        self.config = self.root / "ai/config/train.yaml"
        self.config.parent.mkdir(parents=True)
        self.manifest = self.data / "manifests/private/manifest.csv"
        self.manifest.parent.mkdir(parents=True)
        self.classes = self.config.with_name("classes.json")
        self.classes.write_text(json.dumps({"schema_version": "1.0", "classes": [
            {"class_id": c, "label": c.replace("_", " ")} for c in (*CLASS_IDS, "other_unknown")
        ]}), encoding="utf-8")
        self.document = {
            "schema_version": "1.0", "seed": 42,
            "paths": {"data_dir": "ai/data", "manifest": "ai/data/manifests/private/manifest.csv",
                      "classes": "ai/config/classes.json", "output_dir": "ai/models/training_runs"},
            "split": {"group_by": "site_id", "train_ratio": 0.70, "validation_ratio": 0.15, "test_ratio": 0.15},
            "model": {"architecture": "mobilenet_v2", "pretrained_weights": "IMAGENET1K_V2",
                      "freeze_backbone": True, "class_ids": list(CLASS_IDS)},
            "preprocessing": {"profile": "mobilenet_v2_imagenet1k_v2"},
            "training": {"epochs": 2, "batch_size": 3, "device": "cpu", "num_workers": 0,
                         "optimizer": "adam", "learning_rate": 0.001, "weight_decay": 0.0001,
                         "loss": "cross_entropy", "class_weighting": "none",
                         "checkpoint_metric": "validation_macro_f1", "checkpoint_mode": "max"},
        }
        self.write_config()
        self.rows = []
        for class_id in CLASS_IDS:
            for split in ("train", "validation", "test"):
                index = len(self.rows) + 1
                image_id = f"{class_id}_{split}"
                relative = f"raw/{class_id}/{image_id}.png"
                path = self.data / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (28 + index, 40), ((37 * index) % 256, (83 * index) % 256,
                                                   (149 * index) % 256)).save(path)
                self.rows.append(dict(zip(COLUMNS, [image_id, relative, class_id, f"site_{index}",
                    "Synthetic software-test image", "Generated test fixture", "", "",
                    hashlib.sha256(path.read_bytes()).hexdigest(), split])))
        self.write_manifest()

    def write_config(self):
        self.config.write_text(yaml.safe_dump(self.document, sort_keys=False), encoding="utf-8")

    def write_manifest(self):
        with self.manifest.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(self.rows)

    def prepared(self):
        return train.prepare_run(train.read_train_settings(self.config, self.root))

    @staticmethod
    def without_download(class_ids, *, pretrained, freeze_backbone):
        if pretrained is not True or freeze_backbone is not True:
            raise AssertionError("The real training path must request pretrained, frozen weights.")
        return WatershedMobileNetV2(class_ids, pretrained=False, freeze_backbone=True)

    def test_preflight_is_read_only_and_does_not_construct_a_model(self):
        originals = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        output = io.StringIO()
        with patch.object(train, "WatershedMobileNetV2") as model, contextlib.redirect_stdout(output):
            result = train.main(["--project-root", str(self.root), "--check"])
        self.assertEqual(result, 0)
        model.assert_not_called()
        self.assertIn("PASS: Training preflight completed", output.getvalue())
        self.assertFalse((self.root / "ai/models").exists())
        self.assertEqual(originals, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_unsupported_and_misspelled_settings_are_rejected(self):
        cases = [
            ("training", "device", "mps"), ("training", "epochs", True),
            ("training", "learning_rate", float("nan")), ("training", "weight_decay", -0.1),
            ("training", "optimizer", "sgd"), ("training", "num_workers", False),
            ("training", "checkpoint_mode", "min"), ("training", "epoch", 2),
            ("model", "freeze_backbone", False), ("model", "pretrained_weights", "IMAGENET1K_V1"),
            ("model", "class_ids", [*CLASS_IDS, "other_unknown"]),
            ("preprocessing", "profile", "different_profile"),
            ("paths", "output_dir", "ai/data/raw/run"), ("paths", "output_dir", "../outside"),
        ]
        original = json.loads(json.dumps(self.document))
        for section, key, value in cases:
            with self.subTest(section=section, key=key, value=value):
                self.document = json.loads(json.dumps(original))
                self.document[section][key] = value
                self.write_config()
                with self.assertRaises(ValueError):
                    train.read_train_settings(self.config, self.root)

    def test_bad_hash_blank_split_site_leakage_and_missing_class_are_rejected(self):
        originals = [row.copy() for row in self.rows]
        for fault in ("hash", "split", "site", "class", "training_class", "test_empty"):
            with self.subTest(fault=fault):
                self.rows = [row.copy() for row in originals]
                if fault == "hash":
                    self.rows[0]["sha256"] = "a" * 64
                elif fault == "split":
                    self.rows[0]["split"] = ""
                elif fault == "site":
                    self.rows[1]["site_id"] = self.rows[0]["site_id"]
                elif fault == "class":
                    self.rows[2]["class_id"] = "other_unknown"
                elif fault == "training_class":
                    self.rows[0]["split"] = "validation"
                else:
                    for row in self.rows:
                        if row["split"] == "test":
                            row["split"] = "validation"
                self.write_manifest()
                with self.assertRaises(ValueError):
                    self.prepared()

    def test_class_order_cannot_silently_change(self):
        self.document["model"]["class_ids"].reverse()
        self.write_config()
        with self.assertRaisesRegex(ValueError, "public classes.json order"):
            self.prepared()

    def test_metrics_use_fixed_classes_and_true_rows(self):
        matrix = torch.tensor([[2, 1, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]])
        result = train.metrics_from_confusion(matrix, CLASS_IDS, 0.8)
        self.assertAlmostEqual(result["accuracy"], 3 / 5)
        self.assertAlmostEqual(result["macro_f1"], 1 / 3)
        self.assertEqual(result["per_class"]["farm_pond"], {"support": 1, "precision": 0.5, "recall": 1.0, "f1": 2 / 3})
        self.assertEqual(result["per_class"]["contour_trench"]["f1"], 0.0)
        self.assertEqual(result["per_class"]["contour_trench"]["support"], 0)
        self.assertEqual(result["confusion_matrix"], matrix.tolist())

    def test_loss_is_weighted_by_samples_in_an_incomplete_last_batch(self):
        class FixedModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.register_buffer("scores", torch.tensor([[3.0, 0.0], [0.0, 2.0], [0.1, 0.3]]))

            def forward(self, images):
                return self.scores[images[:, 0, 0, 0].long()]

        images, targets = torch.zeros(3, 3, 224, 224), torch.tensor([0, 1, 0])
        images[:, 0, 0, 0] = torch.arange(3)
        model = FixedModel()
        result = train.run_epoch(model, DataLoader(TensorDataset(images, targets), batch_size=2), CLASS_IDS[:2])
        self.assertEqual(result["samples"], 3)
        self.assertAlmostEqual(result["loss"], float(nn.functional.cross_entropy(model.scores, targets)), places=6)

    def test_training_updates_head_but_not_backbone_or_batchnorm(self):
        torch.manual_seed(42)
        model = WatershedMobileNetV2(CLASS_IDS, pretrained=False, freeze_backbone=True)
        before_features = {k: v.clone() for k, v in model.network.features.state_dict().items()}
        before_head = model.network.classifier[-1].bias.detach().clone()
        loader = DataLoader(TensorDataset(torch.randn(2, 3, 224, 224), torch.tensor([0, 0])), batch_size=2)
        optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=0.001)
        train.run_epoch(model, loader, CLASS_IDS, optimizer)
        self.assertFalse(torch.equal(before_head, model.network.classifier[-1].bias))
        for key, value in model.network.features.state_dict().items():
            self.assertTrue(torch.equal(value, before_features[key]), key)
        self.assertFalse(any(p.grad is not None for p in model.network.features.parameters()))
        before_validation = {k: v.clone() for k, v in model.state_dict().items()}
        train.run_epoch(model, loader, CLASS_IDS)
        for key, value in model.state_dict().items():
            self.assertTrue(torch.equal(value, before_validation[key]), key)
        self.assertFalse(any(module.training for module in model.modules()))

    def test_checkpoint_selection_prefers_macro_f1_then_lower_loss(self):
        best = {"macro_f1": 0.5, "loss": 1.0}
        self.assertTrue(train.is_better(best, None))
        self.assertTrue(train.is_better({"macro_f1": 0.6, "loss": 2.0}, best))
        self.assertTrue(train.is_better({"macro_f1": 0.5, "loss": 0.9}, best))
        self.assertFalse(train.is_better({"macro_f1": 0.4, "loss": 0.1}, best))
        self.assertFalse(train.is_better(best.copy(), best))

    def test_two_epochs_checkpoint_reload_and_no_test_tensor_loading(self):
        prepared = self.prepared()
        originals = {p: p.read_bytes() for p in prepared.source_bytes}
        visited = []
        real_preprocess = dataset_module.preprocess_image

        def observe(path):
            visited.append(path.name)
            if "_test." in path.name:
                raise AssertionError("Test image passed to preprocessing during training.")
            return real_preprocess(path)

        with patch.object(train, "WatershedMobileNetV2", side_effect=self.without_download) as model_factory, \
                patch.object(dataset_module, "preprocess_image", side_effect=observe), \
                contextlib.redirect_stdout(io.StringIO()):
            train.check_data(prepared)
            run_dir = train.train_model(prepared)
        model_factory.assert_called_once_with(CLASS_IDS, pretrained=True, freeze_backbone=True)
        self.assertTrue(visited)
        self.assertTrue(any("_train." in name for name in visited))
        self.assertTrue(any("_validation." in name for name in visited))
        self.assertFalse(any("_test." in name for name in visited))
        metadata = json.loads((run_dir / "metadata.json").read_text())
        history = json.loads((run_dir / "history.json").read_text())
        self.assertEqual(metadata["status"], "completed")
        self.assertEqual(metadata["epochs_completed"], 2)
        self.assertFalse(metadata["test_evaluated"])
        self.assertIsNone(metadata["confidence_threshold"])
        selected = max(history, key=lambda row: (row["validation"]["macro_f1"], -row["validation"]["loss"]))
        self.assertEqual(metadata["best_epoch"], selected["epoch"])
        checkpoint = torch.load(run_dir / "best.pt", map_location="cpu", weights_only=True)
        self.assertEqual(checkpoint["class_ids"], list(CLASS_IDS))
        self.assertEqual(checkpoint["epoch"], selected["epoch"])
        self.assertEqual(checkpoint["preprocessing"]["profile"], train.PROFILE)
        restored = WatershedMobileNetV2(checkpoint["class_ids"], pretrained=False, freeze_backbone=True)
        restored.load_state_dict(checkpoint["model_state_dict"], strict=True)
        metrics = train.run_epoch(restored, DataLoader(prepared.validation, batch_size=3), CLASS_IDS)
        self.assertEqual(metrics, selected["validation"])
        self.assertEqual(originals, {p: p.read_bytes() for p in originals})
        self.assertEqual((run_dir / "config.yaml").read_bytes(), originals[self.config])
        self.assertTrue(run_dir.is_relative_to(self.root / "ai/models/training_runs"))

    def test_changed_inputs_abort_the_run(self):
        paths = [self.config, self.classes, self.manifest, self.data / self.rows[0]["relative_path"]]
        for path in paths:
            with self.subTest(path=path.name):
                prepared = self.prepared()
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with self.assertRaisesRegex(ValueError, "changed during the run"):
                    train.ensure_unchanged(prepared)
                path.write_bytes(original)

    def test_failed_atomic_save_preserves_previous_checkpoint(self):
        target = self.root / "best.pt"
        target.write_bytes(b"previous complete checkpoint")

        def fail(stream):
            stream.write(b"partial new bytes")
            raise OSError("simulated full disk")

        with self.assertRaises(OSError):
            train.atomic_write(target, fail)
        self.assertEqual(target.read_bytes(), b"previous complete checkpoint")
        self.assertEqual(list(self.root.glob(".best.pt-*.tmp")), [])
        with patch.object(train.os, "replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaises(OSError):
                train.atomic_write(target, lambda stream: stream.write(b"new checkpoint"))
        self.assertEqual(target.read_bytes(), b"previous complete checkpoint")
        self.assertEqual(list(self.root.glob(".best.pt-*.tmp")), [])

    def test_failed_and_interrupted_runs_are_not_marked_completed(self):
        for error, status in ((RuntimeError("simulated training failure"), "failed"), (KeyboardInterrupt(), "interrupted")):
            with self.subTest(status=status), \
                    patch.object(train, "WatershedMobileNetV2", side_effect=self.without_download), \
                    patch.object(train, "run_epoch", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(type(error)):
                    train.train_model(self.prepared())
        runs = list((self.root / "ai/models/training_runs").iterdir())
        self.assertEqual(len(runs), 2)  # A fresh run never overwrites its predecessor.
        statuses = {json.loads((p / "metadata.json").read_text())["status"] for p in runs}
        self.assertEqual(statuses, {"failed", "interrupted"})
        self.assertFalse(any((p / "best.pt").exists() for p in runs))


if __name__ == "__main__":
    unittest.main()
