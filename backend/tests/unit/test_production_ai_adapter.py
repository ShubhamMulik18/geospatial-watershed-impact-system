from pathlib import Path
import sys
import types

from app.integrations.ai.production_adapter import ProductionAIAdapter


def test_production_ai_adapter_loads_predictor_once_and_maps_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundle_dir = tmp_path / "bundle"
    photo_path = tmp_path / "photo.jpg"
    photo_path.write_bytes(b"photo")

    loaded = {}
    predictor = types.SimpleNamespace(
        predict=lambda image_path: types.SimpleNamespace(
            class_id="check_dam",
            predicted_class="Check Dam",
            confidence=0.91,
            requires_verification=False,
            top_candidate_class_id="check_dam",
            threshold=0.8,
            model_version="dev-20261005-v1",
            model_hash="a" * 64,
        )
    )

    def fake_load_predictor(received_bundle_dir, *, device):
        loaded["bundle_dir"] = received_bundle_dir
        loaded["device"] = device
        loaded["calls"] = loaded.get("calls", 0) + 1
        return predictor

    predictor_module = types.ModuleType("ai.inference.predictor")
    predictor_module.load_predictor = fake_load_predictor

    inference_module = types.ModuleType("ai.inference")
    inference_module.predictor = predictor_module

    ai_module = types.ModuleType("ai")
    ai_module.inference = inference_module

    monkeypatch.setitem(sys.modules, "ai", ai_module)
    monkeypatch.setitem(sys.modules, "ai.inference", inference_module)
    monkeypatch.setitem(sys.modules, "ai.inference.predictor", predictor_module)

    adapter = ProductionAIAdapter(bundle_dir, device="cpu")

    assert loaded["bundle_dir"] == bundle_dir
    assert loaded["device"] == "cpu"
    assert loaded["calls"] == 1

    result = adapter.predict(photo_path)

    assert result.class_id == "check_dam"
    assert result.predicted_class == "Check Dam"
    assert result.confidence == 0.91
    assert result.requires_verification is False
    assert result.top_candidate_class_id == "check_dam"
    assert result.threshold == 0.8
    assert result.model_version == "dev-20261005-v1"
    assert result.model_hash == "a" * 64
