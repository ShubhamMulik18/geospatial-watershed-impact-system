from pathlib import Path

import pytest

from app.integrations.ai.adapter import DevelopmentAIAdapter


def test_development_ai_adapter_returns_mock_prediction(tmp_path: Path) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"test-photo")

    result = DevelopmentAIAdapter().predict(photo)

    assert result.class_id == "other_unknown"
    assert result.predicted_class == "Other/Unknown"
    assert result.confidence == 0.0
    assert result.requires_verification is True
    assert result.top_candidate_class_id == "check_dam"
    assert result.threshold is None
    assert result.model_version == "development-mock-v1"
    assert result.model_hash == "c9be1e9db3b66570b508644e9c88efbb0ca50a4f2d9a7efd7ae4e30302964c9b"


def test_development_ai_adapter_rejects_missing_photo(tmp_path: Path) -> None:
    photo = tmp_path / "missing.jpg"

    with pytest.raises(FileNotFoundError):
        DevelopmentAIAdapter().predict(photo)
