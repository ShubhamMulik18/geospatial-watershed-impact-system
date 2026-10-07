from io import BytesIO
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from PIL import Image

from app.db.session import get_db
from app.main import app


def _make_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), "white")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _client_with_mock_db():
    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app), db


def test_upload_photo_returns_canonical_response(tmp_path) -> None:
    client, db = _client_with_mock_db()

    from app.api.routes import photos

    original_service = photos.PhotoService

    class TestPhotoService(original_service):
        def __init__(self, db):
            super().__init__(db=db, storage_root=tmp_path / "photos")

    try:
        from unittest.mock import patch

        with patch(
            "app.api.routes.photos.PhotoService",
            TestPhotoService,
        ):
            response = client.post(
                "/api/photos/upload",
                files={
                    "file": (
                        "field-photo.jpg",
                        _make_jpeg_bytes(),
                        "image/jpeg",
                    )
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert set(data) == {
        "photo_id",
        "latitude",
        "longitude",
        "capture_date",
        "exif_status",
        "warnings",
    }
    assert data["photo_id"]
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["capture_date"] is None
    assert data["exif_status"] == "missing"
    assert data["warnings"] == [
        "GPS location is unavailable.",
        "Capture date is unavailable.",
    ]


def test_upload_photo_rejects_unsupported_type() -> None:
    client, _ = _client_with_mock_db()

    try:
        response = client.post(
            "/api/photos/upload",
            files={
                "file": (
                    "field-photo.txt",
                    b"not-an-image",
                    "text/plain",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Unsupported photo type."


def test_upload_photo_rejects_oversized_file() -> None:
    client, _ = _client_with_mock_db()

    oversized_data = b"x" * (10 * 1024 * 1024 + 1)

    try:
        response = client.post(
            "/api/photos/upload",
            files={
                "file": (
                    "large-photo.jpg",
                    oversized_data,
                    "image/jpeg",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The uploaded photo exceeds the 10 MB size limit."
    )


def test_upload_photo_rejects_corrupt_image() -> None:
    client, _ = _client_with_mock_db()

    try:
        response = client.post(
            "/api/photos/upload",
            files={
                "file": (
                    "corrupt-photo.jpg",
                    b"not-a-real-jpeg",
                    "image/jpeg",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The uploaded file is not a valid image."
    )

def test_upload_photo_returns_exif_gps_and_capture_date(tmp_path) -> None:
    client, _ = _client_with_mock_db()

    from app.api.routes import photos

    original_service = photos.PhotoService

    class TestPhotoService(original_service):
        def __init__(self, db):
            super().__init__(db=db, storage_root=tmp_path / "photos")

    image = Image.new("RGB", (20, 20), "white")
    exif = image.getexif()
    exif[36867] = "2026:09:15 14:30:00"
    exif[34853] = {
        1: "N",
        2: (16.0, 42.0, 0.0),
        3: "E",
        4: (74.0, 14.0, 0.0),
    }

    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())

    try:
        from unittest.mock import patch

        with patch(
            "app.api.routes.photos.PhotoService",
            TestPhotoService,
        ):
            response = client.post(
                "/api/photos/upload",
                files={
                    "file": (
                        "field-photo.jpg",
                        buffer.getvalue(),
                        "image/jpeg",
                    )
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert data["latitude"] == 16.7
    assert data["longitude"] == 74.23333333333333
    assert data["capture_date"] == "2026-09-15"
    assert data["exif_status"] == "available"
    assert data["warnings"] == []
def test_create_prediction_returns_canonical_response() -> None:
    from unittest.mock import MagicMock, patch
    import uuid

    from app.api.routes.photos import get_ai_adapter
    from app.integrations.ai.base import PredictionResult

    client, db = _client_with_mock_db()

    photo_id = uuid.uuid4()
    prediction = MagicMock()
    prediction.id = uuid.uuid4()
    prediction.photo_id = photo_id
    prediction.class_id = "check_dam"
    prediction.predicted_label = "Check Dam"
    prediction.confidence = 0.91
    prediction.review_flag = False
    prediction.model_version = "test-model-v1"
    prediction.model_hash = "a" * 64
    prediction.top_candidate_class_id = "check_dam"
    prediction.threshold = 0.80

    adapter = MagicMock()
    adapter.predict.return_value = PredictionResult(
        class_id="check_dam",
        predicted_class="Check Dam",
        confidence=0.91,
        requires_verification=False,
        top_candidate_class_id="check_dam",
        threshold=0.80,
        model_version="test-model-v1",
        model_hash="a" * 64,
    )

    app.dependency_overrides[get_ai_adapter] = lambda: adapter

    try:
        with patch(
            "app.api.routes.photos.PredictionService.create_prediction",
            return_value=prediction,
        ) as create_prediction:
            response = client.post(
                f"/api/photos/{photo_id}/prediction",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert set(data) == {
        "prediction_id",
        "photo_id",
        "class_id",
        "predicted_class",
        "confidence",
        "requires_verification",
        "model_version",
    }

    assert data["prediction_id"] == str(prediction.id)
    assert data["photo_id"] == str(photo_id)
    assert data["class_id"] == "check_dam"
    assert data["predicted_class"] == "Check Dam"
    assert data["confidence"] == 0.91
    assert data["requires_verification"] is False
    assert data["model_version"] == "test-model-v1"

    assert "model_hash" not in data
    assert "top_candidate_class_id" not in data
    assert "threshold" not in data

    create_prediction.assert_called_once_with(str(photo_id))
    db.commit.assert_called_once()
