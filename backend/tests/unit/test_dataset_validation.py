import pytest

from app.storage.dataset_validation import (
    InvalidDatasetError,
    validate_dataset_filename,
    validate_dataset_size,
)


@pytest.mark.parametrize("filename", ["sample.tif", "sample.TIF", "sample.tiff"])
def test_validate_dataset_filename_accepts_geotiff(filename):
    assert validate_dataset_filename(filename) in {".tif", ".tiff"}


@pytest.mark.parametrize(
    "filename",
    ["sample.jpg", "sample.png", "sample.jp2", "sample"],
)
def test_validate_dataset_filename_rejects_non_geotiff(filename):
    with pytest.raises(InvalidDatasetError):
        validate_dataset_filename(filename)


def test_validate_dataset_size_accepts_valid_size():
    validate_dataset_size(1024, 2048)


def test_validate_dataset_size_rejects_empty_file():
    with pytest.raises(InvalidDatasetError):
        validate_dataset_size(0, 2048)


def test_validate_dataset_size_rejects_oversized_file():
    with pytest.raises(InvalidDatasetError):
        validate_dataset_size(2049, 2048)