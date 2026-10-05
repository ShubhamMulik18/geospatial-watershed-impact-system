"""Check the AI/backend result contract without a model or photographs.

From the project root:
    .venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_contracts.py' -v

All scores and hashes below are synthetic software-test fixtures, not measurements.
Only the Python standard library is needed.
"""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest

from ai.inference.contracts import PredictionResult


class PredictionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = Path(__file__).resolve().parents[1] / "config/classes.json"
        document = json.loads(config.read_text(encoding="utf-8"))
        cls.labels = {item["class_id"]: item["label"] for item in document["classes"]}

    def result(self, **changes):
        values = {
            "class_id": "check_dam",
            "predicted_class": self.labels["check_dam"],
            "confidence": 0.6,
            "requires_verification": True,
            "top_candidate_class_id": "check_dam",
            "threshold": None,
            "model_version": "dev-contract-test",
            "model_hash": "a" * 64,
        }
        values.update(changes)
        return PredictionResult(**values)

    def test_current_classes_use_the_configured_display_labels(self):
        self.assertNotIn("plantation", self.labels)
        for class_id in ("check_dam", "farm_pond", "percolation_tank", "contour_trench"):
            with self.subTest(class_id=class_id):
                result = self.result(class_id=class_id, top_candidate_class_id=class_id,
                                     predicted_class=self.labels[class_id])
                result.validate_labels(self.labels)

    def test_unselected_threshold_is_preserved_and_requires_review(self):
        result = self.result()
        self.assertIsNone(result.to_dict()["threshold"])
        self.assertTrue(result.requires_verification)
        with self.assertRaisesRegex(ValueError, "unselected threshold"):
            self.result(requires_verification=False)

    def test_fallback_retains_candidate_and_its_score(self):
        result = self.result(class_id="other_unknown", predicted_class=self.labels["other_unknown"],
                             threshold=0.8)
        result.validate_labels(self.labels)
        self.assertEqual(result.top_candidate_class_id, "check_dam")
        self.assertEqual(result.confidence, 0.6)
        self.assertTrue(result.requires_verification)

    def test_low_score_cannot_be_reported_as_an_accepted_class(self):
        with self.assertRaisesRegex(ValueError, "below the threshold"):
            self.result(threshold=0.8)
        with self.assertRaisesRegex(ValueError, "Other/Unknown requires"):
            self.result(class_id="other_unknown", predicted_class=self.labels["other_unknown"],
                        threshold=0.8, requires_verification=False)

    def test_threshold_boundary_and_probability_endpoints(self):
        for score in (0, 0.6, 1):
            with self.subTest(score=score):
                result = self.result(confidence=score, threshold=score)
                self.assertIsInstance(result.confidence, float)
                self.assertIsInstance(result.threshold, float)
        # A future release can allow automatic acceptance at the threshold.
        self.result(confidence=0.8, threshold=0.8, requires_verification=False)

    def test_invalid_scores_and_thresholds_are_rejected(self):
        for field in ("confidence", "threshold"):
            for value in (-0.1, 1.1, float("nan"), float("inf"), float("-inf"), True, "0.6"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.result(**{field: value})
        with self.assertRaises(ValueError):
            self.result(confidence=None)

    def test_invalid_identity_fields_and_boolean_flags_are_rejected(self):
        cases = (
            {"class_id": "Check Dam"}, {"top_candidate_class_id": ""},
            {"predicted_class": " "}, {"predicted_class": " Check Dam"},
            {"predicted_class": "a" * 257}, {"model_version": ""},
            {"model_version": "v" * 129}, {"model_hash": ""},
            {"model_hash": "g" * 64}, {"model_hash": "a" * 63},
            {"requires_verification": 1}, {"requires_verification": "true"},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.result(**changes)

    def test_unknown_is_not_a_trained_candidate_and_known_class_must_match(self):
        with self.assertRaisesRegex(ValueError, "trained intervention"):
            self.result(top_candidate_class_id="other_unknown")
        with self.assertRaisesRegex(ValueError, "top candidate or other_unknown"):
            self.result(class_id="farm_pond", predicted_class=self.labels["farm_pond"])

    def test_label_validation_rejects_removed_classes_and_incorrect_display_names(self):
        with self.assertRaisesRegex(ValueError, "absent from the public labels"):
            self.result(class_id="plantation", top_candidate_class_id="plantation",
                        predicted_class="Plantation").validate_labels(self.labels)
        with self.assertRaisesRegex(ValueError, "configured display label"):
            self.result(predicted_class="Farm Pond").validate_labels(self.labels)

    def test_internal_result_is_json_safe_and_has_no_backend_generated_ids(self):
        payload = self.result().to_dict()
        self.assertEqual(set(payload), {
            "class_id", "predicted_class", "confidence", "requires_verification",
            "top_candidate_class_id", "threshold", "model_version", "model_hash",
        })
        self.assertEqual(json.loads(json.dumps(payload, allow_nan=False)), payload)

    def test_public_fields_fit_the_existing_backend_response_contract(self):
        result = self.result()
        payload = {"prediction_id": "synthetic-prediction-id", "photo_id": "synthetic-photo-id",
                   **result.to_public_fields()}
        self.assertEqual(set(payload), {
            "prediction_id", "photo_id", "class_id", "predicted_class",
            "confidence", "requires_verification", "model_version",
        })
        self.assertEqual(payload["confidence"], 0.6)
        self.assertTrue(payload["requires_verification"])

    def test_result_is_immutable_and_serialized_copies_are_independent(self):
        result = self.result()
        with self.assertRaises(FrozenInstanceError):
            result.requires_verification = False
        copy = result.to_dict()
        copy["confidence"] = 1.0
        self.assertEqual(result.confidence, 0.6)


if __name__ == "__main__":
    unittest.main()
