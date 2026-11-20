"""Test one-photo inference with a synthetic bundle and generated test images.

From the project root:
    .venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_predictor.py' -v

No field photos, private manifests, trained user checkpoint, downloads or training
are used. Fixed logits are software fixtures, not measured watershed predictions.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import MappingProxyType
import unittest
from unittest.mock import patch

from PIL import Image
import torch
from torch import nn

from ai.inference import model_loader, predictor, preprocess
from ai.inference.model import WatershedMobileNetV2


class FixedLogits(nn.Module):
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.saw_inference_mode = False
        self.input_shape = None

    def forward(self, images):
        self.saw_inference_mode = torch.is_inference_mode_enabled()
        self.input_shape = tuple(images.shape)
        return self.value


class PredictorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, cls.old_threads)
        cls.temp_bundle = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp_bundle.cleanup)
        cls.bundle = Path(cls.temp_bundle.name)
        classes_data = (Path(__file__).resolve().parents[1] / "config/classes.json").read_bytes()
        cls.labels = model_loader.read_public_classes(classes_data)
        cls.class_ids = tuple(c for c in cls.labels if c != "other_unknown")
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(123)
            model = WatershedMobileNetV2(cls.class_ids, pretrained=False)
        # Preserve the real architecture, while making its classification-head
        # output predictable for a test. This is not a learned watershed model.
        with torch.no_grad():
            model.network.classifier[-1].weight.zero_()
            model.network.classifier[-1].bias.copy_(torch.tensor([0.0, 1.0, 0.0, 0.0]))
        torch.save(model.state_dict(), cls.bundle / "model.pt")
        (cls.bundle / "classes.json").write_bytes(classes_data)
        metadata = {
            "schema_version": "1.0", "purpose": "development_inference",
            "model_version": "dev-predictor-test", "architecture": "mobilenet_v2",
            "weights_file": "model.pt", "model_hash": model_loader.sha256_bytes((cls.bundle / "model.pt").read_bytes()),
            "classes_file": "classes.json", "classes_sha256": model_loader.sha256_bytes(classes_data),
            "class_ids": list(cls.class_ids), "preprocessing": model_loader.PREPROCESSING,
            "decision_policy": model_loader.DEVELOPMENT_POLICY,
            "training": {"synthetic_fixture": True}, "export": {"synthetic_fixture": True},
            "test_evaluated": False, "limitations": ["Synthetic software-test bundle, not a trained model."],
        }
        (cls.bundle / "metadata.json").write_bytes(model_loader.json_bytes(metadata))
        (cls.bundle / "MODEL_CARD.md").write_text("Synthetic software-test bundle.\n", encoding="utf-8")

    def setUp(self):
        self.temp_images = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_images.cleanup)
        self.root = Path(self.temp_images.name)
        self.image = self.root / "synthetic.png"
        Image.new("RGB", (320, 250), (50, 110, 170)).save(self.image)
        download = patch("torchvision.models._api.load_state_dict_from_url",
                         side_effect=AssertionError("Prediction must not download weights"))
        download.start()
        self.addCleanup(download.stop)

    def fixed_predictor(self, logits, *, threshold=None):
        model = FixedLogits(logits).eval()
        loaded = model_loader.LoadedModel(model, self.class_ids, MappingProxyType(self.labels),
                                         "dev-fixed-test", "a" * 64, threshold, True)
        with patch.object(predictor, "load_model", return_value=loaded):
            instance = predictor.load_predictor(self.bundle)
        return instance, model

    def test_real_bundle_prediction_matches_shared_preprocessing_and_softmax(self):
        instance = predictor.load_predictor(self.bundle)
        result = instance.predict(image_path=self.image)
        loaded = model_loader.load_model(self.bundle)
        with torch.inference_mode():
            expected = torch.softmax(loaded.model(preprocess.preprocess_image(self.image).unsqueeze(0)), dim=1)[0]
        self.assertEqual(result.class_id, "farm_pond")
        self.assertEqual(result.predicted_class, self.labels["farm_pond"])
        self.assertAlmostEqual(result.confidence, expected[1].item(), places=7)
        self.assertEqual(result.model_hash, loaded.model_hash)
        self.assertEqual(result.model_version, "dev-predictor-test")
        self.assertIsNone(result.threshold)
        self.assertTrue(result.requires_verification)

    def test_model_is_loaded_once_and_reused_for_two_photographs(self):
        second = self.root / "second.png"
        Image.new("L", (300, 260), 90).save(second)
        with patch.object(predictor, "load_model", wraps=model_loader.load_model) as load:
            instance = predictor.load_predictor(self.bundle, device="cpu")
            first_result = instance.predict(self.image)
            second_result = instance.predict(second)
        load.assert_called_once_with(self.bundle, device="cpu")
        self.assertEqual(first_result.model_hash, second_result.model_hash)

    def test_predictions_preserve_files_parameters_buffers_and_repeatability(self):
        instance = predictor.load_predictor(self.bundle)
        before_files = {p: p.read_bytes() for base in (self.root, self.bundle) for p in base.rglob("*") if p.is_file()}
        state = {k: v.clone() for k, v in instance._loaded.model.state_dict().items()}
        first = instance.predict(self.image)
        second = instance.predict(self.image)
        self.assertEqual(first.to_dict(), second.to_dict())
        for name, value in instance._loaded.model.state_dict().items():
            self.assertTrue(torch.equal(value, state[name]), name)
        self.assertFalse(any(m.training for m in instance._loaded.model.modules()))
        self.assertTrue(all(p.grad is None for p in instance._loaded.model.parameters()))
        self.assertEqual(before_files, {p: p.read_bytes() for base in (self.root, self.bundle)
                                       for p in base.rglob("*") if p.is_file()})

    def test_high_and_low_scores_both_require_review_with_unselected_threshold(self):
        for logits in (torch.tensor([[0.0, 100.0, 0.0, 0.0]]), torch.zeros(1, 4)):
            with self.subTest(logits=logits):
                instance, _ = self.fixed_predictor(logits)
                result = instance.predict(self.image)
                self.assertTrue(result.requires_verification)
                self.assertIsNone(result.threshold)
                self.assertEqual(result.class_id, result.top_candidate_class_id)
                self.assertNotEqual(result.class_id, "other_unknown")

    def test_tied_scores_follow_bundle_order_and_run_without_gradients(self):
        instance, model = self.fixed_predictor(torch.tensor([[0.0, 2.0, 0.0, 2.0]]))
        result = instance.predict(self.image)
        self.assertEqual(result.class_id, "farm_pond")  # Index 1 precedes contour_trench at index 3.
        self.assertTrue(model.saw_inference_mode)
        self.assertEqual(model.input_shape, (1, 3, 224, 224))

    def test_numeric_threshold_fallback_retains_candidate_and_original_score(self):
        # Policy-unit fixture only. The real development bundle loader rejects
        # numeric cutoffs until a future validated bundle format supports them.
        instance, _ = self.fixed_predictor(torch.zeros(1, 4), threshold=0.8)
        result = instance.predict(self.image)
        self.assertEqual(result.class_id, "other_unknown")
        self.assertEqual(result.predicted_class, self.labels["other_unknown"])
        self.assertEqual(result.top_candidate_class_id, "check_dam")
        self.assertEqual(result.confidence, 0.25)
        self.assertTrue(result.requires_verification)
        boundary, _ = self.fixed_predictor(torch.zeros(1, 4), threshold=0.25)
        self.assertEqual(boundary.predict(self.image).class_id, "check_dam")

    def test_missing_corrupt_directory_and_multiframe_images_raise_errors(self):
        corrupt = self.root / "corrupt.jpg"
        corrupt.write_bytes(b"not a photograph")
        animation = self.root / "multi.gif"
        with Image.new("RGB", (32, 32), "red") as a, Image.new("RGB", (32, 32), "blue") as b:
            a.save(animation, save_all=True, append_images=[b], duration=100, loop=0)
        instance = predictor.load_predictor(self.bundle)
        for path in (self.root / "missing.jpg", corrupt, self.root, animation):
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                instance.predict(path)

    def test_rgb_conversion_accepts_grayscale_and_transparent_single_images(self):
        instance = predictor.load_predictor(self.bundle)
        for mode, color in (("L", 100), ("RGBA", (40, 100, 180, 80))):
            path = self.root / f"{mode}.png"
            Image.new(mode, (270, 250), color).save(path)
            result = instance.predict(path)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)

    def test_invalid_preprocessing_output_is_rejected(self):
        instance, _ = self.fixed_predictor(torch.zeros(1, 4))
        for value in (torch.zeros(3, 128, 128), torch.zeros(3, 224, 224, dtype=torch.float64),
                      torch.full((3, 224, 224), float("nan")), None):
            with patch.object(predictor, "preprocess_image", return_value=value):
                with self.assertRaisesRegex(RuntimeError, "Preprocessing must return"):
                    instance.predict(self.image)

    def test_invalid_model_outputs_raise_errors_instead_of_predictions(self):
        values = (torch.zeros(1, 5), torch.zeros(2, 4), torch.zeros(1, 4, dtype=torch.float64),
                  torch.full((1, 4), float("nan")), torch.full((1, 4), float("inf")), None)
        for value in values:
            instance, _ = self.fixed_predictor(value)
            with self.assertRaisesRegex(RuntimeError, "Model must return"):
                instance.predict(self.image)

    def test_cli_prints_json_and_keeps_review_reminder_separate(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()) as error:
            status = predictor.main(["--bundle", str(self.bundle), "--image", str(self.image)])
        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["class_id"], "farm_pond")
        self.assertTrue(payload["requires_verification"])
        self.assertIsNone(payload["threshold"])
        self.assertIn("human verification", error.getvalue())

    def test_cli_failure_has_no_success_payload(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()) as error:
            status = predictor.main(["--bundle", str(self.bundle), "--image", str(self.root / "missing.jpg")])
        self.assertEqual(status, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("FAIL:", error.getvalue())

    def test_missing_bundle_and_unsupported_device_fail_at_startup(self):
        with self.assertRaises(OSError):
            predictor.load_predictor(self.root / "missing_bundle")
        with self.assertRaisesRegex(ValueError, "cpu"):
            predictor.load_predictor(self.bundle, device="mps")

    def test_public_projection_preserves_review_flag_and_excludes_internal_metadata(self):
        result = predictor.load_predictor(self.bundle).predict(self.image)
        payload = result.to_public_fields()
        self.assertEqual(set(payload), {"class_id", "predicted_class", "confidence", "requires_verification", "model_version"})
        self.assertTrue(payload["requires_verification"])
        self.assertEqual(payload["confidence"], result.confidence)


if __name__ == "__main__":
    unittest.main()
