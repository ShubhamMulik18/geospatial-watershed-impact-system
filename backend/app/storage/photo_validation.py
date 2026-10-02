from pathlib import Path

from app.core.exceptions import AppError


MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


class InvalidPhotoError(AppError):
    """Raised when an uploaded photo fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


def validate_photo_size(byte_size: int) -> None:
    if byte_size <= 0:
        raise InvalidPhotoError("The uploaded photo is empty.")

    if byte_size > MAX_PHOTO_SIZE_BYTES:
        raise InvalidPhotoError("The uploaded photo exceeds the 10 MB size limit.")


def validate_photo_content_type(content_type: str | None) -> str:
    normalized = (content_type or "").lower().strip()

    if normalized not in ALLOWED_IMAGE_TYPES:
        raise InvalidPhotoError("Unsupported photo type.")

    return ALLOWED_IMAGE_TYPES[normalized]


def validate_photo_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()

    if suffix not in {".jpg", ".jpeg", ".png"}:
        raise InvalidPhotoError("Unsupported photo extension.")

    return suffix