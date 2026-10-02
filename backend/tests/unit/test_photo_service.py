from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.models.photo import Photo
from app.services.photo_service import PhotoService


def _make_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), "white")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_create_photo_validates_stores_and_persists(tmp_path: Path) -> None:
    db = MagicMock()
    service = PhotoService(
        db=db,
        storage_root=tmp_path / "photos",
    )

    photo = service.create_photo(
        data=_make_jpeg_bytes(),
        original_name="field-photo.jpg",
        content_type="image/jpeg",
    )

    assert isinstance(photo, Photo)
    assert photo.original_name == "field-photo.jpg"
    assert photo.mime_type == "image/jpeg"
    assert photo.byte_size > 0
    assert len(photo.sha256) == 64
    assert photo.exif_status == "missing"

    stored_path = Path(photo.safe_path)
    assert stored_path.exists()
    assert stored_path.parent == tmp_path / "photos"
    assert stored_path.name == f"{photo.id}.jpg"

    db.add.assert_called_once_with(photo)
    db.flush.assert_called_once()


def test_create_photo_rejects_invalid_image_bytes(tmp_path: Path) -> None:
    db = MagicMock()
    service = PhotoService(
        db=db,
        storage_root=tmp_path / "photos",
    )

    with pytest.raises(ValueError, match="not a valid image"):
        service.create_photo(
            data=b"not-an-image",
            original_name="field-photo.jpg",
            content_type="image/jpeg",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_create_photo_rejects_mismatched_content_type_and_extension(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    service = PhotoService(
        db=db,
        storage_root=tmp_path / "photos",
    )

    with pytest.raises(
        ValueError,
        match="content type and file extension do not match",
    ):
        service.create_photo(
            data=_make_jpeg_bytes(),
            original_name="field-photo.png",
            content_type="image/jpeg",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()
