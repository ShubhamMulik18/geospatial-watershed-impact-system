from datetime import date
from io import BytesIO

from PIL import Image

from app.utils.photo_exif import extract_exif, validate_image_bytes


def _make_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), "white")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_validate_image_bytes_accepts_valid_jpeg() -> None:
    image = validate_image_bytes(_make_jpeg_bytes())

    assert image.format == "JPEG"


def test_validate_image_bytes_rejects_invalid_bytes() -> None:
    try:
        validate_image_bytes(b"not-an-image")
    except ValueError as exc:
        assert str(exc) == "The uploaded file is not a valid image."
    else:
        raise AssertionError("Expected invalid image bytes to be rejected.")


def test_extract_exif_returns_missing_when_metadata_is_absent() -> None:
    result = extract_exif(_make_jpeg_bytes())

    assert result.latitude is None
    assert result.longitude is None
    assert result.capture_date is None
    assert result.status == "missing"
    assert "GPS location is unavailable." in result.warnings
    assert "Capture date is unavailable." in result.warnings


def test_extract_exif_returns_invalid_for_malformed_bytes() -> None:
    result = extract_exif(b"not-an-image")

    assert result.latitude is None
    assert result.longitude is None
    assert result.capture_date is None
    assert result.status == "invalid"
    assert result.warnings == ["EXIF metadata could not be parsed."]


def test_capture_date_parser_supports_standard_exif_date() -> None:
    image = Image.new("RGB", (20, 20), "white")
    exif = image.getexif()
    exif[36867] = "2026:09:15 14:30:00"

    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())

    result = extract_exif(buffer.getvalue())

    assert result.capture_date == date(2026, 9, 15)
    assert result.status == "partial"
    assert "Capture date is unavailable." not in result.warnings

def test_extract_exif_reads_gps_coordinates() -> None:
    image = Image.new("RGB", (20, 20), "white")
    exif = image.getexif()

    gps_ifd = {
        1: "N",
        2: (16.0, 42.0, 0.0),
        3: "E",
        4: (74.0, 14.0, 0.0),
    }

    exif[34853] = gps_ifd

    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())

    result = extract_exif(buffer.getvalue())

    assert result.latitude == 16.7
    assert result.longitude == 74.23333333333333
    assert result.status == "partial"
    assert "GPS location is unavailable." not in result.warnings
