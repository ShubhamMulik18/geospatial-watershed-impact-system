"""
Extract, normalize, and validate geographic coordinates from recognized OCR text.

Supports:
- Decimal Degrees (DD): e.g. "16.7050° N, 74.2450° E", "Lat: 16.7050 Long: 74.2450"
- Degrees Minutes Seconds (DMS): e.g. "16° 42' 18\" N, 74° 14' 42\" E"
- Degrees Decimal Minutes (DDM): e.g. "16° 42.3' N, 74° 14.7' E"
- Signed decimal coordinate pairs: e.g. "-16.7050, -74.2450"
- Directional indicators: N, S, E, W (with negative values for S and W)
- Out-of-range bounds checking: [-90, 90] for latitude, [-180, 180] for longitude
"""

from dataclasses import dataclass
import math
import re
from typing import Any


@dataclass
class ParsedCoordinates:
    latitude: float | None
    longitude: float | None
    format_detected: str | None = None
    is_valid: bool = False


def _clean_ocr_text(text: str) -> str:
    """Normalize OCR text noise, unusual spaces, and common character misreads."""
    if not text:
        return ""
    # Replace non-breaking spaces, unusual dashes, smart quotes
    cleaned = (
        text.replace("\u00a0", " ")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("`", "'")
        .replace("′", "'")
        .replace("″", '"')
        .replace("º", "°")
    )
    return cleaned


def _dms_to_decimal(degrees: float, minutes: float, seconds: float, direction: str | None = None) -> float:
    val = abs(degrees) + (minutes / 60.0) + (seconds / 3600.0)
    if direction in {"S", "W"} or (direction is None and degrees < 0):
        val = -val
    return round(val, 6)


def _ddm_to_decimal(degrees: float, minutes: float, direction: str | None = None) -> float:
    val = abs(degrees) + (minutes / 60.0)
    if direction in {"S", "W"} or (direction is None and degrees < 0):
        val = -val
    return round(val, 6)


def _is_valid_latitude(lat: float | None) -> bool:
    if lat is None or math.isnan(lat) or math.isinf(lat):
        return False
    return -90.0 <= lat <= 90.0


def _is_valid_longitude(lon: float | None) -> bool:
    if lon is None or math.isnan(lon) or math.isinf(lon):
        return False
    return -180.0 <= lon <= 180.0


def parse_coordinates_from_text(raw_text: str) -> ParsedCoordinates:
    """
    Search recognized text for latitude and longitude coordinates.
    Returns ParsedCoordinates with None for missing or unparseable values.
    """
    if not raw_text or not raw_text.strip():
        return ParsedCoordinates(latitude=None, longitude=None, is_valid=False)

    text = _clean_ocr_text(raw_text)

    # 1. Try explicit labeled DMS format:
    # e.g., "16° 42' 18" N" or "16 deg 42 min 18 sec N"
    dms_lat_match = re.search(
        r"(?:lat(?:itude)?[:\s]*)?(\d{1,2})\s*(?:°|deg|d|\s)\s*(\d{1,2})\s*(?:'|min|m|\s)\s*(\d{1,2}(?:\.\d+)?)\s*(?:\"|sec|s|\s)?\s*([NS])\b",
        text,
        re.IGNORECASE,
    )
    dms_lon_match = re.search(
        r"(?:lon(?:gitude)?[:\s]*)?(\d{1,3})\s*(?:°|deg|d|\s)\s*(\d{1,2})\s*(?:'|min|m|\s)\s*(\d{1,2}(?:\.\d+)?)\s*(?:\"|sec|s|\s)?\s*([EW])\b",
        text,
        re.IGNORECASE,
    )

    if dms_lat_match and dms_lon_match:
        lat = _dms_to_decimal(
            float(dms_lat_match.group(1)),
            float(dms_lat_match.group(2)),
            float(dms_lat_match.group(3)),
            dms_lat_match.group(4).upper(),
        )
        lon = _dms_to_decimal(
            float(dms_lon_match.group(1)),
            float(dms_lon_match.group(2)),
            float(dms_lon_match.group(3)),
            dms_lon_match.group(4).upper(),
        )
        if _is_valid_latitude(lat) and _is_valid_longitude(lon):
            return ParsedCoordinates(latitude=lat, longitude=lon, format_detected="dms", is_valid=True)

    # 2. Try explicit labeled DDM format:
    # e.g., "16° 42.3' N" and "74° 14.7' E"
    ddm_lat_match = re.search(
        r"(?:lat(?:itude)?[:\s]*)?(\d{1,2})\s*(?:°|deg|d|\s)\s*(\d{1,2}\.\d+)\s*(?:'|min|m|\s)?\s*([NS])\b",
        text,
        re.IGNORECASE,
    )
    ddm_lon_match = re.search(
        r"(?:lon(?:gitude)?[:\s]*)?(\d{1,3})\s*(?:°|deg|d|\s)\s*(\d{1,2}\.\d+)\s*(?:'|min|m|\s)?\s*([EW])\b",
        text,
        re.IGNORECASE,
    )
    if ddm_lat_match and ddm_lon_match:
        lat = _ddm_to_decimal(
            float(ddm_lat_match.group(1)),
            float(ddm_lat_match.group(2)),
            ddm_lat_match.group(3).upper(),
        )
        lon = _ddm_to_decimal(
            float(ddm_lon_match.group(1)),
            float(ddm_lon_match.group(2)),
            ddm_lon_match.group(3).upper(),
        )
        if _is_valid_latitude(lat) and _is_valid_longitude(lon):
            return ParsedCoordinates(latitude=lat, longitude=lon, format_detected="ddm", is_valid=True)

    # 3. Explicit labeled Decimal Degrees with Lat / Long keywords:
    # e.g., "Latitude: 16.7050° N" / "Longitude: 74.2450° E" or "Lat: 16.7050, Long: 74.2450"
    lat_val: float | None = None
    lon_val: float | None = None

    lat_label_match = re.search(
        r"(?:lat(?:itude)?)\s*[:=]?\s*([+-]?\d{1,3}(?:\.\d+)?)\s*(?:°|deg|o|\b)?\s*(?:([NS])\b)?",
        text,
        re.IGNORECASE,
    )
    lon_label_match = re.search(
        r"(?:lon(?:g(?:itude)?)?)\s*[:=]?\s*([+-]?\d{1,3}(?:\.\d+)?)\s*(?:°|deg|o|\b)?\s*(?:([EW])\b)?",
        text,
        re.IGNORECASE,
    )

    if lat_label_match:
        val = float(lat_label_match.group(1))
        direction = lat_label_match.group(2)
        if direction:
            val = abs(val) if direction.upper() == "N" else -abs(val)
        lat_val = round(val, 6)

    if lon_label_match:
        val = float(lon_label_match.group(1))
        direction = lon_label_match.group(2)
        if direction:
            val = abs(val) if direction.upper() == "E" else -abs(val)
        lon_val = round(val, 6)

    if lat_val is not None and lon_val is not None:
        if _is_valid_latitude(lat_val) and _is_valid_longitude(lon_val):
            return ParsedCoordinates(latitude=lat_val, longitude=lon_val, format_detected="labeled_decimal", is_valid=True)
        # If explicitly out of bounds (e.g. Lat 150 N), reject
        return ParsedCoordinates(
            latitude=lat_val if _is_valid_latitude(lat_val) else None,
            longitude=lon_val if _is_valid_longitude(lon_val) else None,
            format_detected="labeled_decimal",
            is_valid=False,
        )

    # 4. Decimal pair with cardinal letters:
    # e.g., "16.7050° N, 74.2450° E" or "16.7050 N 74.2450 E" or "16.70500 N Longitude 74.24500 E"
    cardinal_pair_match = re.search(
        r"([+-]?\d{1,2}(?:\.\d+)?)\s*(?:°|deg|o|\b)?\s*([NS])\b[\s,;/-]+([+-]?\d{1,3}(?:\.\d+)?)\s*(?:°|deg|o|\b)?\s*([EW])\b",
        text,
        re.IGNORECASE,
    )
    if cardinal_pair_match:
        raw_lat = float(cardinal_pair_match.group(1))
        lat_dir = cardinal_pair_match.group(2).upper()
        raw_lon = float(cardinal_pair_match.group(3))
        lon_dir = cardinal_pair_match.group(4).upper()

        lat = abs(raw_lat) if lat_dir == "N" else -abs(raw_lat)
        lon = abs(raw_lon) if lon_dir == "E" else -abs(raw_lon)

        if _is_valid_latitude(lat) and _is_valid_longitude(lon):
            return ParsedCoordinates(latitude=round(lat, 6), longitude=round(lon, 6), format_detected="cardinal_decimal_pair", is_valid=True)

    # 5. Raw decimal pair separated by comma or semicolon:
    # e.g., "16.7050, 74.2450" or "-16.7050, -74.2450"
    raw_pair_match = re.search(
        r"(?<!\d)([+-]?\d{1,2}\.\d{3,8})[\s,;]+([+-]?\d{1,3}\.\d{3,8})(?!\d)",
        text,
    )
    if raw_pair_match:
        lat = float(raw_pair_match.group(1))
        lon = float(raw_pair_match.group(2))
        if _is_valid_latitude(lat) and _is_valid_longitude(lon):
            return ParsedCoordinates(latitude=round(lat, 6), longitude=round(lon, 6), format_detected="raw_decimal_pair", is_valid=True)

    # 6. Check for partial matches (only latitude or only longitude)
    partial_lat: float | None = None
    partial_lon: float | None = None

    if lat_label_match and _is_valid_latitude(lat_val):
        partial_lat = lat_val
    elif dms_lat_match:
        dms_lat = _dms_to_decimal(
            float(dms_lat_match.group(1)),
            float(dms_lat_match.group(2)),
            float(dms_lat_match.group(3)),
            dms_lat_match.group(4).upper(),
        )
        if _is_valid_latitude(dms_lat):
            partial_lat = dms_lat
    else:
        lone_lat = re.search(r"(\d{1,2}(?:\.\d+)?)\s*(?:°|deg)?\s*([NS])\b", text, re.IGNORECASE)
        if lone_lat:
            val = float(lone_lat.group(1))
            d = lone_lat.group(2).upper()
            val = abs(val) if d == "N" else -abs(val)
            if _is_valid_latitude(val):
                partial_lat = round(val, 6)

    if lon_label_match and _is_valid_longitude(lon_val):
        partial_lon = lon_val
    elif dms_lon_match:
        dms_lon = _dms_to_decimal(
            float(dms_lon_match.group(1)),
            float(dms_lon_match.group(2)),
            float(dms_lon_match.group(3)),
            dms_lon_match.group(4).upper(),
        )
        if _is_valid_longitude(dms_lon):
            partial_lon = dms_lon
    else:
        lone_lon = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(?:°|deg)?\s*([EW])\b", text, re.IGNORECASE)
        if lone_lon:
            val = float(lone_lon.group(1))
            d = lone_lon.group(2).upper()
            val = abs(val) if d == "E" else -abs(val)
            if _is_valid_longitude(val):
                partial_lon = round(val, 6)

    if partial_lat is not None or partial_lon is not None:
        return ParsedCoordinates(
            latitude=partial_lat,
            longitude=partial_lon,
            format_detected="partial",
            is_valid=(partial_lat is not None and partial_lon is not None),
        )

    return ParsedCoordinates(latitude=None, longitude=None, is_valid=False)

