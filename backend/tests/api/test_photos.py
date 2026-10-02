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