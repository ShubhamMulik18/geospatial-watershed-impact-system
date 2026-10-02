from datetime import date, datetime
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError


class EXIFData:
    def __init__(
        self,
        latitude: float | None,
        longitude: float | None,
        capture_date: date | None,
        status: str,
        warnings: list[str],
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.capture_date = capture_date
        self.status = status
        self.warnings = warnings


def validate_image_bytes(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    return Image.open(BytesIO(data))


def _rational_to_float(value: Any) -> float:
    return float(value)


def _convert_gps_coordinate(values: Any, reference: Any) -> float:
    degrees, minutes, seconds = values

    coordinate = (
        _rational_to_float(degrees)
        + _rational_to_float(minutes) / 60
        + _rational_to_float(seconds) / 3600
    )

    if reference in {"S", "W"}:
        coordinate = -coordinate

    return coordinate


def _parse_capture_date(exif: dict[int, Any]) -> date | None:
    value = exif.get(36867) or exif.get(306)

    if not isinstance(value, str):
        return None

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def extract_exif(data: bytes) -> EXIFData:
    try:
        image = Image.open(BytesIO(data))
        exif = image.getexif()

        if not exif:
            return EXIFData(
                latitude=None,
                longitude=None,
                capture_date=None,
                status="missing",
                warnings=[
                    "GPS location is unavailable.",
                    "Capture date is unavailable.",
                ],
            )

        gps = exif.get_ifd(34853)
        latitude = None
        longitude = None

        if gps:
            latitude_values = gps.get(2)
            latitude_ref = gps.get(1)
            longitude_values = gps.get(4)
            longitude_ref = gps.get(3)

            if latitude_values and latitude_ref:
                latitude = _convert_gps_coordinate(
                    latitude_values,
                    latitude_ref,
                )

            if longitude_values and longitude_ref:
                longitude = _convert_gps_coordinate(
                    longitude_values,
                    longitude_ref,
                )

        capture_date = _parse_capture_date(dict(exif))

        warnings: list[str] = []

        if latitude is None:
            warnings.append("GPS location is unavailable.")

        if longitude is None:
            if "GPS location is unavailable." not in warnings:
                warnings.append("GPS location is unavailable.")

        if capture_date is None:
            warnings.append("Capture date is unavailable.")

        if latitude is not None and longitude is not None and capture_date is not None:
            status = "available"
        elif latitude is not None or longitude is not None or capture_date is not None:
            status = "partial"
        else:
            status = "missing"

        return EXIFData(
            latitude=latitude,
            longitude=longitude,
            capture_date=capture_date,
            status=status,
            warnings=warnings,
        )

    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return EXIFData(
            latitude=None,
            longitude=None,
            capture_date=None,
            status="invalid",
            warnings=["EXIF metadata could not be parsed."],
        )