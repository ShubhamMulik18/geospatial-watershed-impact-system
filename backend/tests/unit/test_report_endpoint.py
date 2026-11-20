import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from starlette.responses import FileResponse

from app.api.routes.analyses import download_report
from app.core.exceptions import AppError


def test_download_report_raises_when_invalid_uuid():
    db = MagicMock()
    with pytest.raises(AppError) as exc_info:
        download_report("not-a-uuid", db=db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "ANALYSIS_NOT_FOUND"


def test_download_report_raises_when_not_completed():
    analysis_id = str(uuid.uuid4())
    db = MagicMock()

    mock_analysis = MagicMock()
    mock_analysis.id = uuid.UUID(analysis_id)
    mock_analysis.status = "running"

    with patch("app.api.routes.analyses.AnalysisService") as mock_service_cls:
        mock_service_cls.return_value.get_analysis.return_value = mock_analysis
        with pytest.raises(AppError) as exc_info:
            download_report(analysis_id, db=db)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "ANALYSIS_NOT_COMPLETED"


def test_download_report_generates_and_registers_pdf(tmp_path: Path):
    analysis_id = str(uuid.uuid4())
    db = MagicMock()

    mock_analysis = MagicMock()
    mock_analysis.id = uuid.UUID(analysis_id)
    mock_analysis.status = "completed"
    mock_analysis.artifacts = []
    mock_analysis.result = MagicMock()
    mock_analysis.result.result = {"metrics": {"ndvi_change": 0.15}}
    mock_analysis.prediction_snapshot = {"class": "Check Dam", "confidence": 0.92}

    mock_settings = MagicMock()
    mock_settings.artifact_storage_root = str(tmp_path / "artifacts")

    with patch("app.api.routes.analyses.AnalysisService") as mock_service_cls, \
         patch("app.api.routes.analyses.get_settings", return_value=mock_settings), \
         patch("app.api.routes.analyses.ArtifactRegistrationService") as mock_reg_cls:

        mock_service_cls.return_value.get_analysis.return_value = mock_analysis

        response = download_report(analysis_id, db=db)

        assert isinstance(response, FileResponse)
        assert response.media_type == "application/pdf"
        assert response.filename == f"watershed_analysis_{analysis_id}.pdf"
        assert Path(response.path).exists()
        assert Path(response.path).stat().st_size > 0

        # Verify ArtifactRegistrationService was called to register the generated report
        mock_reg_cls.return_value.register_artifacts.assert_called_once()
        db.commit.assert_called_once()
