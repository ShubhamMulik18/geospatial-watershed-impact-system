from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.integrations.geospatial.base import AnalysisResult
from app.workers.analysis_worker import AnalysisWorker


class FakeAIAdapter:
    def __init__(self) -> None:
        self.called_with: Path | None = None

    def predict(self, photo_path: Path):
        self.called_with = photo_path
        return MagicMock()


class FakeGeospatialAdapter:
    def __init__(self) -> None:
        self.called_request = None
        self.called_output_dir = None

    def run_analysis(self, request, output_dir, progress_callback=None):
        self.called_request = request
        self.called_output_dir = output_dir
        return AnalysisResult(
            metrics={},
            series=[],
            comparisons=[],
            quality={},
            warnings=[],
            provenance={},
            artifacts=[],
        )


class FailingGeospatialAdapter:
    def run_analysis(self, request, output_dir, progress_callback=None):
        raise RuntimeError("scientific processing failed")


def _make_analysis(tmp_path: Path):
    photo_path = tmp_path / "photo.jpg"
    photo_path.write_bytes(b"photo")

    photo = MagicMock()
    photo.safe_path = str(photo_path)

    dataset_link = MagicMock()
    dataset_link.dataset_id = "dataset-001"
    dataset_link.sequence = 0
    dataset_link.dataset_metadata_snapshot = {
        "path": "datasets/dataset-001.tif",
        "crs": "EPSG:32643",
    }
    dataset_link.dataset_sha256 = "dataset-hash"

    analysis = MagicMock()
    analysis.id = "analysis-001"
    analysis.status = "queued"
    analysis.error = None
    analysis.photo = photo
    analysis.polygon = "polygon"
    analysis.indicators = ["ndvi"]
    analysis.dataset_links = [dataset_link]

    return analysis


def test_process_job_completes_successfully(tmp_path: Path) -> None:
    db = MagicMock()
    repository = MagicMock()
    ai_adapter = FakeAIAdapter()
    geospatial_adapter = FakeGeospatialAdapter()

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=ai_adapter,
        geospatial_adapter=geospatial_adapter,
    )

    analysis = _make_analysis(tmp_path)

    worker.process_job(analysis)

    assert analysis.status == "completed"
    assert analysis.error is None
    assert ai_adapter.called_with == tmp_path / "photo.jpg"

    assert geospatial_adapter.called_request["analysis_id"] == "analysis-001"
    assert geospatial_adapter.called_request["indicators"] == ["ndvi"]
    assert geospatial_adapter.called_request["datasets"][0]["dataset_id"] == "dataset-001"
    assert geospatial_adapter.called_request["datasets"][0]["sha256"] == "dataset-hash"

    db.commit.assert_called()


def test_process_job_marks_failed_on_processing_error(tmp_path: Path) -> None:
    db = MagicMock()
    repository = MagicMock()

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=FakeAIAdapter(),
        geospatial_adapter=FailingGeospatialAdapter(),
    )

    analysis = _make_analysis(tmp_path)
    repository.get_analysis.return_value = analysis

    worker.process_job(analysis)

    assert analysis.status == "failed"
    assert analysis.error == "scientific processing failed"
    db.rollback.assert_called_once()
    db.commit.assert_called()

def test_recover_expired_jobs_commits_when_jobs_recovered() -> None:
    db = MagicMock()
    repository = MagicMock()
    repository.recover_expired_analyses.return_value = 2

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=FakeAIAdapter(),
        geospatial_adapter=FakeGeospatialAdapter(),
    )

    recovered = worker.recover_expired_jobs()

    assert recovered == 2
    repository.recover_expired_analyses.assert_called_once_with(db=db)
    db.commit.assert_called_once()

def test_run_once_returns_false_when_no_job_is_available() -> None:
    db = MagicMock()
    repository = MagicMock()
    repository.recover_expired_analyses.return_value = 0
    repository.claim_next_analysis.return_value = None

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=FakeAIAdapter(),
        geospatial_adapter=FakeGeospatialAdapter(),
    )

    processed = worker.run_once()

    assert processed is False
    repository.recover_expired_analyses.assert_called_once_with(db=db)
    repository.claim_next_analysis.assert_called_once()

def test_run_once_processes_claimed_job(tmp_path: Path) -> None:
    db = MagicMock()
    repository = MagicMock()
    repository.recover_expired_analyses.return_value = 0

    ai_adapter = FakeAIAdapter()
    geospatial_adapter = FakeGeospatialAdapter()

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=ai_adapter,
        geospatial_adapter=geospatial_adapter,
    )

    analysis = _make_analysis(tmp_path)
    repository.claim_next_analysis.return_value = analysis

    worker.run_once()

    assert analysis.status == "completed"
    repository.recover_expired_analyses.assert_called_once_with(db=db)
    repository.claim_next_analysis.assert_called_once()
    assert ai_adapter.called_with == tmp_path / "photo.jpg"

def test_renew_job_lease_commits_when_renewed() -> None:
    db = MagicMock()
    repository = MagicMock()
    repository.renew_lease.return_value = True

    worker = AnalysisWorker(
        db=db,
        repository=repository,
        ai_adapter=FakeAIAdapter(),
        geospatial_adapter=FakeGeospatialAdapter(),
    )

    analysis = MagicMock()
    analysis.id = "analysis-001"

    renewed = worker.renew_job_lease(analysis)

    assert renewed is True
    repository.renew_lease.assert_called_once_with(
        db=db,
        analysis_id="analysis-001",
        lease_seconds=worker.lease_seconds,
    )
    db.commit.assert_called_once()

def test_progress_callback_renews_lease_after_heartbeat_interval(
    tmp_path: Path,
    monkeypatch,
):
    worker = AnalysisWorker(
        db=MagicMock(),
        repository=MagicMock(),
        ai_adapter=FakeAIAdapter(),
        geospatial_adapter=FakeGeospatialAdapter(),
    )

    worker.heartbeat_interval_seconds = 10

    analysis = _make_analysis(tmp_path)

    renew_calls = []

    def fake_renew_job_lease(job):
        renew_calls.append(job)
        return True

    worker.renew_job_lease = fake_renew_job_lease

    current_time = iter([100.0, 105.0, 109.0, 111.0])
    monkeypatch.setattr(
        "app.workers.analysis_worker.time.monotonic",
        lambda: next(current_time),
    )

    callback = worker._build_progress_callback(analysis)

    callback("validating")
    assert renew_calls == []

    callback("processing")
    assert renew_calls == []

    callback("processing")
    assert renew_calls == [analysis]