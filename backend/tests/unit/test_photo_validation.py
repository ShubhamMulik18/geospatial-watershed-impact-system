import pytest

from app.storage.photo_validation import (
    InvalidPhotoError,
    MAX_PHOTO_SIZE_BYTES,
    validate_photo_content_type,
    validate_photo_size,
    validate_photo_suffix,
)


def test_valid_photo_size() -> None:
    validate_photo_size(1024)


def test_empty_photo_is_rejected() -> None:
    with pytest.raises(InvalidPhotoError, match="empty"):
        validate_photo_size(0)


def test_oversized_photo_is_rejected() -> None:
    with pytest.raises(InvalidPhotoError, match="10 MB"):
        validate_photo_size(MAX_PHOTO_SIZE_BYTES + 1)


@pytest.mark.parametrize(
    ("content_type", "expected_suffix"),
    [
        ("image/jpeg", ".jpg"),
        ("image/png", ".png"),
        ("IMAGE/JPEG", ".jpg"),
    ],
)
def test_supported_content_types(content_type: str, expected_suffix: str) -> None:
    assert validate_photo_content_type(content_type) == expected_suffix


def test_unsupported_content_type_is_rejected() -> None:
    with pytest.raises(InvalidPhotoError, match="Unsupported photo type"):
        validate_photo_content_type("application/pdf")


@pytest.mark.parametrize("filename", ["photo.jpg", "photo.jpeg", "photo.png"])
def test_supported_photo_extensions(filename: str) -> None:
    assert validate_photo_suffix(filename) in {".jpg", ".jpeg", ".png"}


def test_unsupported_photo_extension_is_rejected() -> None:
    with pytest.raises(InvalidPhotoError, match="Unsupported photo extension"):
        validate_photo_suffix("photo.exe")