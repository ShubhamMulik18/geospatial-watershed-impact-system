from pathlib import Path

from app.core.exceptions import AppError


class InvalidDatasetError(AppError):
    """Raised when an uploaded raster dataset is invalid."""


def validate_dataset_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in {".tif", ".tiff"}:
        raise InvalidDatasetError(
            "Only GeoTIFF dataset files (.tif or .tiff) are supported.",
            status_code=400,
        )

    return suffix


def validate_dataset_size(byte_size: int, max_size_bytes: int) -> None:
    if byte_size <= 0:
        raise InvalidDatasetError(
            "Dataset file is empty.",
            status_code=400,
        )

    if byte_size > max_size_bytes:
        raise InvalidDatasetError(
            f"Dataset file exceeds the maximum allowed size of {max_size_bytes} bytes.",
            status_code=400,
        )