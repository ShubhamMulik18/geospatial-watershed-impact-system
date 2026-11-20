from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image, ImageDraw, ImageFont
import pytest
from starlette.datastructures import UploadFile

from app.api.routes.photos import upload_photo
from app.core.exceptions import AppError
from app.schemas.photo import PhotoResponse


def _get_font(size: int = 24):
    for font_path in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _create_stamped_jpeg(
    lines: list[str],
    image_size: tuple[int, int] = (800, 600),
    exif_date: str | None = None,
) -> bytes:
    """Create a JPEG with visually rendered text banner and NO EXIF GPS."""
    img = Image.new("RGB", image_size, color=(70, 90, 70))
    d = ImageDraw.Draw(img)
    font = _get_font(24)

    banner_height = 40 + len(lines) * 35
    w, h = image_size
    banner_top = h - banner_height - 20

    # Draw dark banner
    d.rectangle((20, banner_top, w - 20, banner_top + banner_height), fill=(15, 23, 42))

    y = banner_top + 15
    for line in lines:
        d.text((40, y), line, fill=(255, 255, 255), font=font)
        y += 35

    buffer = BytesIO()
    if exif_date:
        exif = img.getexif()
        exif[36867] = exif_date
        img.save(buffer, format="JPEG", quality=95, exif=exif.tobytes())
    else:
        img.save(buffer, format="JPEG", quality=95)

    return buffer.getvalue()


def _make_upload_file(data: bytes, filename: str = "field-photo.jpg", content_type: str = "image/jpeg") -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=filename,
        headers={"content-type": content_type},
    )


def test_1_decimal_latitude_and_longitude_printed_on_image():
    """1. Decimal latitude and longitude printed on the image."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "FIELD MONITORING OBSERVATION",
        "Latitude: 16.7050 N",
        "Longitude: 74.2450 E",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(16.7050, abs=0.001)
    assert res.longitude == pytest.approx(74.2450, abs=0.001)
    assert "GPS location is unavailable." not in res.warnings
    db.commit.assert_called_once()


def test_2_dms_coordinates_with_directional_indicators():
    """2. DMS coordinates with directional indicators."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "16 deg 42 min 18 sec N",
        "74 deg 14 min 42 sec E",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(16.7050, abs=0.001)
    assert res.longitude == pytest.approx(74.2450, abs=0.001)
    assert "GPS location is unavailable." not in res.warnings


def test_3_southern_and_western_coordinates():
    """3. Southern and western coordinates (verifying negative sign)."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "Latitude: 16.7050 S",
        "Longitude: 74.2450 W",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(-16.7050, abs=0.001)
    assert res.longitude == pytest.approx(-74.2450, abs=0.001)
    assert "GPS location is unavailable." not in res.warnings


def test_4_coordinates_in_different_supported_layout():
    """4. Coordinates printed in a multi-line banner layout with metadata."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "CHECK DAM SITE #3 - KOLHAPUR",
        "Lat: 16.7050 N",
        "Long: 74.2450 E",
        "Elevation: 610m MSL",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(16.7050, abs=0.001)
    assert res.longitude == pytest.approx(74.2450, abs=0.001)


def test_5_photo_with_no_coordinate_stamp():
    """5. A photo with no coordinate stamp."""
    db = MagicMock()
    img = Image.new("RGB", (400, 300), color=(100, 120, 100))
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    upload_file = _make_upload_file(buffer.getvalue())

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude is None
    assert res.longitude is None
    assert "GPS location is unavailable." in res.warnings
    assert res.exif_status == "missing"


def test_6_stamp_with_only_latitude_or_only_longitude():
    """6. A stamp with only latitude or only longitude."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "CHECK DAM SITE",
        "Latitude: 16.7050 N",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(16.7050, abs=0.001)
    assert res.longitude is None
    assert "GPS location is unavailable." in res.warnings
    assert res.exif_status == "missing"


def test_7_invalid_or_out_of_range_coordinates():
    """7. Invalid or out-of-range coordinates."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "Latitude: 95.5000 N",
        "Longitude: 74.2450 E",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    # Latitude > 90 must be rejected
    assert res.latitude is None
    assert res.longitude == pytest.approx(74.2450, abs=0.001)
    assert "GPS location is unavailable." in res.warnings


def test_8_ambiguous_ocr_output():
    """8. Ambiguous OCR output (stamp with random non-coordinate text)."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg([
        "WATERSHED IMPACT SYSTEM",
        "INTERVENTION SITE PHOTOGRAPHY",
        "PROJECT TEAM 2026",
    ])
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude is None
    assert res.longitude is None
    assert "GPS location is unavailable." in res.warnings


def test_9_real_upload_combining_exif_date_and_ocr_gps():
    """9. Combined workflow: EXIF capture date + visible OCR coordinates."""
    db = MagicMock()
    jpeg_bytes = _create_stamped_jpeg(
        lines=[
            "Latitude: 16.7050 N",
            "Longitude: 74.2450 E",
        ],
        exif_date="2026:10:24 11:30:00",
    )
    upload_file = _make_upload_file(jpeg_bytes)

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    assert res.latitude == pytest.approx(16.7050, abs=0.001)
    assert res.longitude == pytest.approx(74.2450, abs=0.001)
    assert res.capture_date == date(2026, 10, 24)
    assert res.exif_status == "partial"
    assert "GPS location extracted from photo text stamp via OCR (EXIF GPS unavailable)." in res.warnings
    assert "GPS location is unavailable." not in res.warnings
    assert "Capture date is unavailable." not in res.warnings


def test_10_invalid_and_corrupt_uploads():
    """10. Validation handling: reject corrupt bytes and extension mismatches."""
    db = MagicMock()

    # Corrupt image bytes
    corrupt_file = _make_upload_file(b"not-an-image-file", "corrupt.jpg", "image/jpeg")
    with pytest.raises(AppError) as exc_info:
        upload_photo(file=corrupt_file, db=db)
    assert exc_info.value.status_code == 400

    # Extension mismatch
    png_img = Image.new("RGB", (20, 20), color="blue")
    buf = BytesIO()
    png_img.save(buf, format="PNG")
    mismatched_file = _make_upload_file(buf.getvalue(), "photo.jpg", "image/png")
    with pytest.raises(AppError) as exc_info:
        upload_photo(file=mismatched_file, db=db)
    assert exc_info.value.status_code == 400


def test_11_actual_user_photo_with_gps_map_camera_stamp():
    """11. Real-world user photo #1: extracts coordinates and capture date via OCR."""
    from pathlib import Path
    img_path = Path("C:/Users/Admin/.gemini/antigravity/brain/935cb3df-b208-41dd-82ef-3918ed2235ee/.user_uploaded/media_1793182873195_11e6a5ea.jpg")
    if not img_path.exists():
        pytest.skip("User attached photo not found on disk.")

    db = MagicMock()
    data = img_path.read_bytes()
    upload_file = _make_upload_file(data, "gps_map_camera_1.jpg", "image/jpeg")

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    # Coordinates visibly stamped on photo: Lat 16.664232° Long 74.230831°
    assert res.latitude == pytest.approx(16.664232, abs=0.0001)
    assert res.longitude == pytest.approx(74.230831, abs=0.0001)
    # Date visibly stamped: Wednesday, 28/10/2026 10:43 AM GMT +05:30
    assert res.capture_date == date(2026, 10, 28)
    assert res.exif_status == "missing"
    assert "GPS location extracted from photo text stamp via OCR (EXIF GPS unavailable)." in res.warnings
    assert "Capture date extracted from photo text stamp via OCR (EXIF date unavailable)." in res.warnings
    assert "Capture date is unavailable." not in res.warnings
    assert "GPS location is unavailable." not in res.warnings


def test_12_new_user_photo_with_gps_map_camera_stamp():
    """12. Real-world user photo #2: extracts 2026-11-18 capture date and coordinates via OCR."""
    from pathlib import Path
    img_path = Path("C:/Users/Admin/.gemini/antigravity/brain/935cb3df-b208-41dd-82ef-3918ed2235ee/.user_uploaded/media_1795082519894_c200e348.jpg")
    if not img_path.exists():
        pytest.skip("User attached photo not found on disk.")

    db = MagicMock()
    data = img_path.read_bytes()
    upload_file = _make_upload_file(data, "gps_map_camera_2.jpg", "image/jpeg")

    res: PhotoResponse = upload_photo(file=upload_file, db=db)

    # Coordinates visibly stamped on photo: Lat 16.6703083° Long 74.2316020°
    assert res.latitude == pytest.approx(16.670308, abs=0.0001)
    assert res.longitude == pytest.approx(74.231602, abs=0.0001)
    # Date visibly stamped: Wednesday, 18/11/2026 08:19 PM GMT +05:30
    assert res.capture_date == date(2026, 11, 18)
    assert res.exif_status == "missing"
    assert "GPS location extracted from photo text stamp via OCR (EXIF GPS unavailable)." in res.warnings
    assert "Capture date extracted from photo text stamp via OCR (EXIF date unavailable)." in res.warnings
    assert "Capture date is unavailable." not in res.warnings
    assert "GPS location is unavailable." not in res.warnings


