from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pytest

from app.utils.ocr import extract_coordinates_from_image_bytes, recognize_text_from_image_file


def _get_font(size: int = 28):
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


def _create_stamped_image_bytes(
    lines: list[str],
    stamp_position: str = "bottom",
    image_size: tuple[int, int] = (800, 600),
) -> bytes:
    """Create a realistic JPEG photo with a stamped geotag banner."""
    # Create background image simulating field photography
    img = Image.new("RGB", image_size, color=(60, 80, 60))
    d = ImageDraw.Draw(img)

    font = _get_font(24)

    banner_height = 40 + len(lines) * 35
    w, h = image_size

    if stamp_position == "bottom":
        banner_top = h - banner_height - 20
    else:
        banner_top = 20

    # Draw semi-transparent dark banner (like GPS Map Camera)
    banner_box = (20, banner_top, w - 20, banner_top + banner_height)
    d.rectangle(banner_box, fill=(15, 23, 42))

    # Render stamped text lines
    y = banner_top + 15
    for line in lines:
        d.text((40, y), line, fill=(255, 255, 255), font=font)
        y += 35

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def test_real_ocr_decimal_degrees():
    img_bytes = _create_stamped_image_bytes([
        "WATERSHED FIELD OBSERVATION",
        "Latitude: 16.7050 N",
        "Longitude: 74.2450 E",
        "2026-10-24 11:30:00",
    ])

    result = extract_coordinates_from_image_bytes(img_bytes)

    assert result.status == "available"
    assert result.latitude == pytest.approx(16.7050, abs=0.001)
    assert result.longitude == pytest.approx(74.2450, abs=0.001)
    assert len(result.warnings) == 0


def test_real_ocr_southern_western_coordinates():
    img_bytes = _create_stamped_image_bytes([
        "Latitude: 16.7050 S",
        "Longitude: 74.2450 W",
    ])

    result = extract_coordinates_from_image_bytes(img_bytes)

    assert result.status == "available"
    assert result.latitude == pytest.approx(-16.7050, abs=0.001)
    assert result.longitude == pytest.approx(-74.2450, abs=0.001)


def test_real_ocr_dms_coordinates():
    img_bytes = _create_stamped_image_bytes([
        "16 deg 42 min 18 sec N",
        "74 deg 14 min 42 sec E",
    ])

    result = extract_coordinates_from_image_bytes(img_bytes)

    assert result.status == "available"
    assert result.latitude == pytest.approx(16.7050, abs=0.001)
    assert result.longitude == pytest.approx(74.2450, abs=0.001)


def test_real_ocr_image_without_coordinate_stamp():
    # Plain photo with no coordinates
    img = Image.new("RGB", (400, 300), color=(120, 140, 100))
    buffer = BytesIO()
    img.save(buffer, format="JPEG")

    result = extract_coordinates_from_image_bytes(buffer.getvalue())

    assert result.status == "missing"
    assert result.latitude is None
    assert result.longitude is None
    assert "GPS location is unavailable." in result.warnings


def test_real_ocr_partial_coordinate_stamp():
    # Photo with only latitude stamped
    img_bytes = _create_stamped_image_bytes([
        "WATERSHED SURVEY",
        "Latitude: 16.7050 N",
        "Elevation: 580m",
    ])

    result = extract_coordinates_from_image_bytes(img_bytes)

    assert result.status == "partial"
    assert result.latitude == pytest.approx(16.7050, abs=0.001)
    assert result.longitude is None
    assert "GPS location is unavailable." in result.warnings


def test_real_ocr_invalid_image_bytes():
    result = extract_coordinates_from_image_bytes(b"not-a-valid-image-bytes")

    assert result.status == "invalid"
    assert result.latitude is None
    assert result.longitude is None
    assert len(result.warnings) > 0

