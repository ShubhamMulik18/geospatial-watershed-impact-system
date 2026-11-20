"""
Optical Character Recognition (OCR) module for extracting visible coordinate stamps
from field photographs.

Uses genuine local OCR:
1. Windows.Media.Ocr native engine on Windows (zero extra dependencies, 100% offline).
2. Tesseract-OCR CLI if installed and available in PATH.
"""

from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from PIL import Image, ImageEnhance, ImageOps

from app.utils.coordinate_parser import ParsedCoordinates, parse_coordinates_from_text
from app.utils.date_parser import parse_date_from_text


@dataclass
class OCRCoordinateResult:
    latitude: float | None
    longitude: float | None
    capture_date: date | None = None
    recognized_text: str = ""
    format_detected: str | None = None
    status: str = "missing"  # "available", "partial", "missing", "invalid"
    warnings: list[str] = field(default_factory=list)


def _get_win_ocr_script_path() -> Path:
    return Path(__file__).parent / "win_ocr.ps1"


def _run_tesseract(image_path: Path) -> str:
    """Run Tesseract CLI if available in PATH."""
    tesseract_bin = shutil.which("tesseract")
    if not tesseract_bin:
        return ""
    try:
        proc = subprocess.run(
            [tesseract_bin, str(image_path), "stdout", "--oem", "1", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return proc.stdout.strip()
    except Exception:
        return ""


def _run_windows_ocr(image_path: Path) -> str:
    """Run Windows.Media.Ocr via PowerShell."""
    script_path = _get_win_ocr_script_path()
    if not script_path.exists():
        return ""
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-ImagePath",
                str(image_path.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return proc.stdout.strip()
    except Exception:
        return ""


def recognize_text_from_image_file(image_path: Path) -> str:
    """
    Run genuine local OCR on the given image path.
    Tries Windows.Media.Ocr on Windows, then Tesseract.
    """
    if os.name == "nt":
        text = _run_windows_ocr(image_path)
        if text:
            return text

    text = _run_tesseract(image_path)
    return text


def _generate_candidate_crops(image: Image.Image) -> list[Image.Image]:
    """
    Extract regions where geotag stamps typically appear:
    - Full image
    - Bottom 30% banner
    - Top 25% banner
    Also applies contrast enhancement.
    """
    candidates = []

    # 1. Full image
    candidates.append(image)

    w, h = image.size

    # 2. Bottom banner (most common in GPS camera apps)
    if h > 80:
        bottom_box = (0, int(h * 0.68), w, h)
        bottom_crop = image.crop(bottom_box)
        candidates.append(bottom_crop)

    # 3. Top banner
    if h > 80:
        top_box = (0, 0, w, int(h * 0.32))
        top_crop = image.crop(top_box)
        candidates.append(top_crop)

    # Enhance contrast and upscale small crops for better OCR recognition
    enhanced_candidates = []
    for img in candidates:
        enhanced_candidates.append(img)
        try:
            # Grayscale + contrast stretch
            gray = ImageOps.grayscale(img)
            enhancer = ImageEnhance.Contrast(gray)
            high_contrast = enhancer.enhance(2.0)
            # If resolution is low, upscale 2x
            if max(img.size) < 1200:
                high_contrast = high_contrast.resize(
                    (high_contrast.width * 2, high_contrast.height * 2),
                    Image.Resampling.BILINEAR,
                )
            enhanced_candidates.append(high_contrast)
        except Exception:
            pass

    return enhanced_candidates


def extract_coordinates_from_image_bytes(data: bytes) -> OCRCoordinateResult:
    """
    Process raw image bytes:
    1. Loads image.
    2. Runs OCR across candidate regions.
    3. Parses and normalizes coordinates and capture dates.
    4. Returns structured OCRCoordinateResult with safe fallbacks.
    """
    try:
        image = Image.open(BytesIO(data))
        # Ensure image is in RGB or L mode
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
    except Exception:
        return OCRCoordinateResult(
            latitude=None,
            longitude=None,
            capture_date=None,
            status="invalid",
            warnings=["The uploaded file is not a valid image."],
        )

    crops = _generate_candidate_crops(image)
    all_recognized_texts = []
    best_coordinates: ParsedCoordinates | None = None
    partial_result: ParsedCoordinates | None = None
    extracted_date: date | None = None

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "candidate.png"

        for crop in crops:
            try:
                crop.save(tmp_path, format="PNG")
                text = recognize_text_from_image_file(tmp_path)
            except Exception:
                continue

            if not text:
                continue

            all_recognized_texts.append(text)

            # Check for date in recognized text
            if extracted_date is None:
                parsed_date = parse_date_from_text(text)
                if parsed_date is not None:
                    extracted_date = parsed_date

            # Check for coordinates
            if best_coordinates is None:
                parsed = parse_coordinates_from_text(text)
                if parsed.is_valid:
                    best_coordinates = parsed
                elif parsed.latitude is not None or parsed.longitude is not None:
                    if partial_result is None or (
                        partial_result.latitude is None and parsed.latitude is not None
                    ) or (
                        partial_result.longitude is None and parsed.longitude is not None
                    ):
                        partial_result = parsed

            # If both coordinates and date are found, we can finish early
            if best_coordinates is not None and extracted_date is not None:
                break

    combined_text = "\n".join(all_recognized_texts)

    # Also try parsing date from combined text if not found in individual crops
    if extracted_date is None and combined_text:
        extracted_date = parse_date_from_text(combined_text)

    if best_coordinates is not None:
        return OCRCoordinateResult(
            latitude=best_coordinates.latitude,
            longitude=best_coordinates.longitude,
            capture_date=extracted_date,
            recognized_text=combined_text,
            format_detected=best_coordinates.format_detected,
            status="available",
            warnings=[],
        )

    # If full pair was not found, check if a partial coordinate was found
    if partial_result and (partial_result.latitude is not None or partial_result.longitude is not None):
        warnings = ["GPS location is unavailable."]
        return OCRCoordinateResult(
            latitude=partial_result.latitude,
            longitude=partial_result.longitude,
            capture_date=extracted_date,
            recognized_text=combined_text,
            format_detected="partial",
            status="partial",
            warnings=warnings,
        )

    # No coordinates recognized
    return OCRCoordinateResult(
        latitude=None,
        longitude=None,
        capture_date=extracted_date,
        recognized_text=combined_text,
        status="missing",
        warnings=["GPS location is unavailable."],
    )

