"""
Standalone Verification Script for Photo OCR GPS Coordinate Extraction.

Usage:
    # 1. Run automated verification on synthetic stamped images:
    python backend/scripts/verify_photo_ocr.py

    # 2. Test an actual photograph from your computer or camera:
    python backend/scripts/verify_photo_ocr.py path/to/your/field_photo.jpg
"""

import sys
from io import BytesIO
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from PIL import Image, ImageDraw, ImageFont
from app.utils.ocr import extract_coordinates_from_image_bytes
from app.utils.coordinate_parser import parse_coordinates_from_text


def get_font(size: int = 24):
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


def create_demo_photo(lines: list[str], output_path: Path) -> Path:
    """Create a realistic demo field photo with a visible coordinate banner."""
    img = Image.new("RGB", (800, 600), color=(50, 75, 55))
    d = ImageDraw.Draw(img)
    font = get_font(24)

    banner_height = 40 + len(lines) * 35
    banner_top = 600 - banner_height - 20
    d.rectangle((20, banner_top, 780, banner_top + banner_height), fill=(15, 23, 42))

    y = banner_top + 15
    for line in lines:
        d.text((40, y), line, fill=(255, 255, 255), font=font)
        y += 35

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=95)
    return output_path


def test_file(file_path: Path):
    print("=" * 65)
    print(f"TESTING FILE: {file_path}")
    print("=" * 65)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return

    data = file_path.read_bytes()
    result = extract_coordinates_from_image_bytes(data)

    print(f"Recognized Raw Text : {result.recognized_text!r}")
    print(f"Extracted Latitude  : {result.latitude}")
    print(f"Extracted Longitude : {result.longitude}")
    print(f"Detection Format    : {result.format_detected}")
    print(f"Metadata Status     : {result.status}")
    print(f"Warnings            : {result.warnings}")

    if result.latitude is not None and result.longitude is not None:
        print("\nSUCCESS: Coordinates successfully extracted from visible photo pixels via OCR!")
    else:
        print("\nINFO: No valid coordinates found in visible text.")
    print("=" * 65)


def main():
    if len(sys.argv) > 1:
        custom_path = Path(sys.argv[1])
        test_file(custom_path)
        return

    print("No input image specified. Running automated synthetic verification...\n")
    sample_dir = Path("sample_data/test_photos")
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 1. Decimal coordinates demo
    demo1 = create_demo_photo([
        "KOLHAPUR WATERSHED PROJECT",
        "Latitude: 16.7050 N",
        "Longitude: 74.2450 E",
        "Date: 2026-10-24 11:30:00",
    ], sample_dir / "demo_decimal_stamp.jpg")
    test_file(demo1)

    # 2. DMS coordinates demo
    demo2 = create_demo_photo([
        "CHECK DAM SITE #4",
        "16 deg 42 min 18 sec N",
        "74 deg 14 min 42 sec E",
    ], sample_dir / "demo_dms_stamp.jpg")
    test_file(demo2)

    # 3. Clean photo with no coordinates
    img_plain = Image.new("RGB", (400, 300), color=(100, 120, 100))
    demo3 = sample_dir / "demo_no_coordinates.jpg"
    img_plain.save(demo3, "JPEG")
    test_file(demo3)


if __name__ == "__main__":
    main()

