"""Check installable inference without training files or a real model bundle.

Run from the repository root in the AI environment:
    python -m unittest discover -s ai/tests -p 'test_inference_package.py' -v

Needs pip, setuptools>=68 and wheel as test/build tools. Builds only a temporary
source copy; never reads real photos, private manifests or saved model weights.
The existing predictor fixture supplies controlled weights and a generated image.
"""

from __future__ import annotations

from email.parser import Parser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

from ai.tests import test_predictor as predictor_fixtures


def run_checked(args, cwd):
    completed = subprocess.run(
        [sys.executable, *args], cwd=cwd, capture_output=True, text=True,
        env={**os.environ, "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
        timeout=120,
    )
    if completed.returncode:
        raise AssertionError(completed.stdout + completed.stderr)
    return completed.stdout


class InferencePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        cls.source = cls.root / "package-source"
        cls.source.mkdir()
        actual_ai = Path(__file__).resolve().parents[1]
        for name in ("pyproject.toml", "MANIFEST.in"):
            shutil.copy2(actual_ai / name, cls.source / name)
        shutil.copytree(actual_ai / "inference", cls.source / "inference",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Fake sentinels prove exclusion rules. Never copy the user's data/models.
        for name in ("data/manifests/private/private.csv", "data/raw/private.jpg",
                     "models/private.pt", "training/train.py", "tests/test_private.py",
                     "config/classes.json"):
            sentinel = cls.source / name
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text("PACKAGE EXCLUSION TEST ONLY\n", encoding="utf-8")
        cls.archives = cls.root / "archives"
        cls.archives.mkdir()
        run_checked(["-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
                     "--wheel-dir", str(cls.archives), str(cls.source)], cls.root)
        cls.wheel = next(cls.archives.glob("*.whl"))
        run_checked(["-c", "import sys; from setuptools.build_meta import build_sdist; "
                     "build_sdist(sys.argv[1])", str(cls.archives)], cls.source)
        cls.sdist = next(cls.archives.glob("*.tar.gz"))

    def test_archives_exclude_training_models_and_private_data(self):
        expected = {"contracts.py", "model.py", "model_loader.py", "predictor.py", "preprocess.py"}
        with zipfile.ZipFile(self.wheel) as archive:
            names = archive.namelist()
            runtime = {name for name in names if not any(p.endswith(".dist-info") for p in Path(name).parts)}
            self.assertEqual(runtime, {f"ai/inference/{name}" for name in expected})
            metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
            metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
            self.assertEqual(metadata["Name"], "watershed-ai")
            self.assertEqual(metadata["Version"], "0.1.0.dev1")
            dependencies = metadata.get_all("Requires-Dist", [])
            for dependency in ("torch", "torchvision", "Pillow"):
                self.assertTrue(any(value.startswith(dependency) for value in dependencies))
            self.assertEqual(len(dependencies), 3)
        with tarfile.open(self.sdist) as archive:
            paths = [Path(*Path(name).parts[1:]) for name in archive.getnames()]
        excluded = {"data", "models", "training", "tests", "config", "build", "dist"}
        for path in paths:
            self.assertFalse(set(path.parts) & excluded, str(path))
            self.assertNotIn(path.suffix, {".pt", ".pth", ".jpg", ".csv", ".pyc"})
        self.assertIn(Path("pyproject.toml"), paths)
        self.assertIn(Path("inference/BACKEND_HANDOFF.md"), paths)

    def test_installed_prediction_outside_repo_uses_no_training_dependencies(self):
        site = self.root / "installed"
        run_checked(["-m", "pip", "install", "--no-deps", "--no-compile",
                     "--target", str(site), str(self.wheel)], self.root)
        # Reuse the tested synthetic fixture, not the user's development weights.
        fixture_type = predictor_fixtures.PredictorTests
        self.addCleanup(fixture_type.doClassCleanups)
        fixture_type.setUpClass()
        fixture = fixture_type("test_real_bundle_prediction_matches_shared_preprocessing_and_softmax")
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        outside = self.root / "outside-repository"
        outside.mkdir()
        program = r'''
import importlib.abc
import importlib.metadata
import json
from pathlib import Path
import sys
from unittest.mock import patch

site, bundle, photo = map(Path, sys.argv[1:])
sys.path.insert(0, str(site))
class NoTrainingImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "yaml" or fullname.startswith(("ai.training", "ai.data", "ai.config")):
            raise AssertionError("Inference attempted a training/data dependency: " + fullname)
sys.meta_path.insert(0, NoTrainingImports())
import torch
torch.set_num_threads(1)
from ai.inference import predictor
assert Path(predictor.__file__).is_relative_to(site)
assert importlib.metadata.version("watershed-ai") == "0.1.0.dev1"
with patch("torchvision.models._api.load_state_dict_from_url",
           side_effect=AssertionError("Inference must not download weights")):
    instance = predictor.load_predictor(bundle, device="cpu")
    first = instance.predict(image_path=photo)
    second = instance.predict(image_path=photo)
assert first.to_dict() == second.to_dict()
assert first.class_id == first.top_candidate_class_id == "farm_pond"
assert first.predicted_class == "Farm Pond"
assert first.threshold is None and first.requires_verification is True
assert len(first.model_hash) == 64
assert len(first.to_dict()) == 8 and len(first.to_public_fields()) == 5
for name, module in tuple(sys.modules.items()):
    if name.startswith("ai.") and getattr(module, "__file__", None):
        assert Path(module.__file__).is_relative_to(site), name
print(json.dumps(first.to_dict(), allow_nan=False))
'''
        output = run_checked(["-I", "-c", program, str(site), str(fixture.bundle),
                              str(fixture.image)], outside)
        result = json.loads(output)
        self.assertEqual(result["class_id"], "farm_pond")
        self.assertIsNone(result["threshold"])
        self.assertTrue(result["requires_verification"])


if __name__ == "__main__":
    unittest.main()
