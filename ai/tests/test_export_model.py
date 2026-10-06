"""Exercise export and CPU loading using a real trainer-produced test checkpoint.

Run from the project root:
    .venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_export_model.py' -v

The fixture uses random model weights and synthetic tensors for one training
epoch. All generated files are temporary. No downloads, field photographs,
private manifests or user's trained checkpoint are used. Test scores are not
evidence of watershed accuracy.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import torch
from torch.utils.data import TensorDataset

from ai.inference import model_loader, preprocess
from ai.inference.model import WatershedMobileNetV2
from ai.training import export_model, train
from ai.training.split_dataset import Settings


class ExportModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, cls.old_threads)
        cls.fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture.cleanup)
        root = Path(cls.fixture.name)
        cls.fixture_classes = root / "classes.json"
        cls.fixture_classes.write_bytes((Path(__file__).resolve().parents[1] / "config/classes.json").read_bytes())
        labels = model_loader.read_public_classes(cls.fixture_classes.read_bytes())
        cls.class_ids = tuple(c for c in labels if c != "other_unknown")
        shared = Settings(42, (0.7, 0.15, 0.15), cls.class_ids, root / "data", root / "manifest.csv",
                          cls.fixture_classes, root / "train.yaml", b"synthetic_test_fixture: true\n")
        settings = train.TrainSettings(shared, root / "runs", 1, 4, 0.001, 0.0001)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(123)
            data = TensorDataset(torch.randn(4, 3, 224, 224), torch.arange(4))
        counts = {s: {"photos": 4, "sites": 4, "classes": dict.fromkeys(cls.class_ids, 1)}
                  for s in ("train", "validation", "test")}
        fingerprints = {"classes_sha256": model_loader.sha256_bytes(cls.fixture_classes.read_bytes()),
                        "config_sha256": "1" * 64, "manifest_sha256": "2" * 64}
        prepared = train.PreparedRun(settings, data, data, {cls.fixture_classes: cls.fixture_classes.read_bytes()},
                                     {}, counts, fingerprints)

        def random_initialization(class_ids, *, pretrained, freeze_backbone):
            if pretrained is not True:
                raise AssertionError("The trainer should still request pretrained initialization.")
            return WatershedMobileNetV2(class_ids, pretrained=False, freeze_backbone=freeze_backbone)

        # Use the actual trainer's serialization format. Replace only its download
        # with random initialization; the checkpoint has undergone a real optimizer step.
        with patch.object(train, "WatershedMobileNetV2", side_effect=random_initialization), \
                patch("torchvision.models._api.load_state_dict_from_url", side_effect=AssertionError("No downloads")), \
                contextlib.redirect_stdout(io.StringIO()):
            cls.fixture_run = train.train_model(prepared)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.classes = self.root / "ai/config/classes.json"
        self.classes.parent.mkdir(parents=True)
        self.classes.write_bytes(self.fixture_classes.read_bytes())
        self.run = self.root / "ai/models/training_runs/synthetic"
        shutil.copytree(self.fixture_run, self.run)
        self.checkpoint = self.run / "best.pt"
        self.destination = self.root / "ai/models/bundles/dev-unit-test-v1"
        self.args = ["--project-root", str(self.root), "--checkpoint", str(self.checkpoint),
                     "--model-version", "dev-unit-test-v1"]
        self.download_blocker = patch("torchvision.models._api.load_state_dict_from_url",
                                      side_effect=AssertionError("Export/loading must not download weights"))
        self.download_blocker.start()
        self.addCleanup(self.download_blocker.stop)

    def prepare(self):
        return export_model.prepare_bundle(self.checkpoint, self.classes, "dev-unit-test-v1")

    def export(self):
        files, sources, logits = self.prepare()
        return export_model.write_bundle(self.destination, files, sources, logits)

    def mutate_json(self, path, change):
        document = json.loads(path.read_text(encoding="utf-8"))
        change(document)
        path.write_bytes(model_loader.json_bytes(document))

    def test_preflight_is_read_only_and_accepts_the_actual_trainer_format(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(export_model.main([*self.args, "--check"]), 0)
        self.assertIn("PASS: Export preflight", output.getvalue())
        self.assertFalse(self.destination.parent.exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_export_round_trip_preserves_logits_and_loads_without_training_files(self):
        original = model_loader.restore_model(
            torch.load(self.checkpoint, map_location="cpu", weights_only=True)["model_state_dict"], self.class_ids)
        bundle = self.export()
        self.assertEqual({p.name for p in bundle.iterdir()}, {"model.pt", "classes.json", "metadata.json", "MODEL_CARD.md"})
        metadata = json.loads((bundle / "metadata.json").read_text())
        self.assertEqual(metadata["training"]["epoch"], 1)
        self.assertIsNone(metadata["decision_policy"]["threshold"])
        self.assertTrue(metadata["decision_policy"]["always_requires_verification"])
        self.assertNotIn(str(self.root), (bundle / "metadata.json").read_text())
        moved = Path(shutil.move(str(bundle), self.root / "portable_bundle"))
        shutil.rmtree(self.run)
        self.classes.unlink()
        loaded = model_loader.load_model(moved)
        self.assertEqual(loaded.class_ids, self.class_ids)
        self.assertIsNone(loaded.threshold)
        self.assertTrue(loaded.always_requires_verification)
        self.assertFalse(any(module.training for module in loaded.model.modules()))
        self.assertFalse(any(p.requires_grad for p in loaded.model.parameters()))
        image_path = self.root / "synthetic.png"
        Image.new("RGBA", (320, 250), (40, 110, 170, 160)).save(image_path)
        tensor = preprocess.preprocess_image(image_path).unsqueeze(0)
        with torch.inference_mode():
            self.assertTrue(torch.equal(original(tensor), loaded.model(tensor)))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(model_loader.main(["--bundle", str(moved), "--check"]), 0)

    def test_preprocessing_spec_matches_trainer_and_actual_transform(self):
        self.assertEqual(model_loader.PREPROCESSING, train.PREPROCESSING)
        transform = preprocess._evaluation_transform()
        self.assertEqual(transform.resize_size, [232])
        self.assertEqual(transform.crop_size, [224])
        self.assertEqual(transform.mean, model_loader.PREPROCESSING["mean"])
        self.assertEqual(transform.std, model_loader.PREPROCESSING["std"])
        self.assertTrue(transform.antialias)
        self.assertEqual(transform.interpolation.value, "bilinear")

    def test_changed_class_file_is_rejected(self):
        self.mutate_json(self.classes, lambda d: d["classes"][0].update(label="Changed Label"))
        with self.assertRaisesRegex(ValueError, "differs from the file used for training"):
            self.prepare()

    def test_reordered_classes_and_fabricated_threshold_are_rejected(self):
        original = self.checkpoint.read_bytes()
        for change in (lambda c: c["class_ids"].reverse(), lambda c: c.update(confidence_threshold=0.7),
                       lambda c: c.update(test_evaluated=True), lambda c: c.update(preprocessing={"profile": "wrong"})):
            checkpoint = model_loader.load_torch_bytes(original, "fixture")
            change(checkpoint)
            torch.save(checkpoint, self.checkpoint)
            with self.assertRaises(ValueError):
                self.prepare()

    def test_incomplete_or_mismatched_run_metadata_is_rejected(self):
        path = self.run / "metadata.json"
        original = path.read_bytes()
        for change in (lambda d: d.update(status="running"), lambda d: d.update(best_epoch=99),
                       lambda d: d.update(best_validation={}), lambda d: d.update(epochs_completed=0)):
            path.write_bytes(original)
            self.mutate_json(path, change)
            with self.assertRaises(ValueError):
                self.prepare()

    def test_missing_misshaped_wrong_dtype_and_nonfinite_weights_are_rejected(self):
        original = self.checkpoint.read_bytes()
        key = "network.classifier.1.weight"
        changes = (
            lambda s: s.pop(key), lambda s: s.update({key: torch.zeros(3, 1280)}),
            lambda s: s.update({key: s[key].double()}), lambda s: s[key].fill_(float("nan")),
        )
        for change in changes:
            checkpoint = model_loader.load_torch_bytes(original, "fixture")
            change(checkpoint["model_state_dict"])
            torch.save(checkpoint, self.checkpoint)
            with self.assertRaises(ValueError):
                self.prepare()

    def test_existing_bundle_is_never_overwritten(self):
        self.export()
        before = {p.name: p.read_bytes() for p in self.destination.iterdir()}
        files, sources, logits = self.prepare()
        with self.assertRaises(FileExistsError):
            export_model.write_bundle(self.destination, files, sources, logits)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(export_model.main([*self.args, "--write"]), 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.destination.iterdir()})

    def test_modified_weights_or_labels_fail_checksum_before_loading(self):
        self.export()
        for name in ("model.pt", "classes.json"):
            path = self.destination / name
            original = path.read_bytes()
            path.write_bytes(original + b"modified")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                model_loader.load_model(self.destination)
            path.write_bytes(original)

    def test_loader_rejects_changed_policy_preprocessing_class_order_and_filenames(self):
        self.export()
        path = self.destination / "metadata.json"
        original = path.read_bytes()
        changes = (
            lambda d: d["decision_policy"].update(always_requires_verification=False),
            lambda d: d["decision_policy"].update(threshold=0.7),
            lambda d: d["preprocessing"].update(center_crop=[128, 128]),
            lambda d: d["class_ids"].reverse(), lambda d: d.update(weights_file="../best.pt"),
        )
        for change in changes:
            path.write_bytes(original)
            self.mutate_json(path, change)
            with self.assertRaises(ValueError):
                model_loader.load_model(self.destination)

    def test_failed_export_cleans_only_its_new_directory(self):
        files, sources, logits = self.prepare()
        with patch.object(export_model, "load_model", side_effect=ValueError("Simulated reload failure")):
            with self.assertRaisesRegex(ValueError, "Simulated reload failure"):
                export_model.write_bundle(self.destination, files, sources, logits)
        self.assertFalse(self.destination.exists())
        self.assertEqual(sources[self.checkpoint.resolve()], self.checkpoint.read_bytes())

    def test_inputs_changed_after_check_are_rejected_before_writing(self):
        files, sources, logits = self.prepare()
        self.classes.write_bytes(self.classes.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Export input changed"):
            export_model.write_bundle(self.destination, files, sources, logits)
        self.assertFalse(self.destination.exists())

    def test_output_outside_models_and_invalid_versions_are_rejected(self):
        for value in ("release-v1", "dev-../../outside", "", "dev-" + "x" * 128):
            with self.assertRaises(ValueError):
                model_loader.validate_model_version(value)
        with contextlib.redirect_stderr(io.StringIO()):
            result = export_model.main([*self.args, "--output-dir", "ai/data", "--write"])
        self.assertEqual(result, 1)
        self.assertFalse((self.root / "ai/data").exists())

    def test_loader_reports_missing_files_and_unsupported_device(self):
        with self.assertRaises(OSError):
            model_loader.load_model(self.destination)
        with self.assertRaisesRegex(ValueError, "cpu"):
            model_loader.load_model(self.destination, device="mps")

    def test_invalid_serialization_and_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            model_loader.load_torch_bytes(b"not a torch checkpoint", "invalid fixture")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            model_loader.read_json_bytes(b'{"a": 1, "a": 2}', "fixture")
        with self.assertRaises(ValueError):
            model_loader.read_json_bytes(b'{"metric": NaN}', "fixture")


if __name__ == "__main__":
    unittest.main()
