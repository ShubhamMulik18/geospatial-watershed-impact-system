"""
Date parsing utility for extracting capture dates from OCR recognized text stamps
found on field photographs (such as GPS Map Camera watermarks).

Supports:
- Day of week + date: e.g. "Wednesday, 18/11/2026 08:19 PM"
- Standard European / Indian format: "18/11/2026", "18-11-2026", "18.11.2026"
- Text month names: "18 Nov 2026", "18 November 2026", "Nov 18, 2026"
- ISO 8601 / EXIF formatted dates: "2026-11-18", "2026:11:18", "2026/11/18"
- Labeled dates: "Date: 18/11/2026", "Captured: 2026-11-18"
- Robust OCR normalization for character misreads (e.g. bullet points, vertical bars, spaces around separators)
"""

from datetime import date
import re

MONTH_MAP: dict[str, int] = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _clean_ocr_date_text(text: str) -> str:
    """Normalize OCR text noise and common character misreads in date/time strings."""
    if not text:
        return ""
    cleaned = (
        text.replace("\u00a0", " ")
        .replace("\u2022", " ")
        .replace("•", " ")
        .replace("|", "/")
        .replace("\\", "/")
        .replace("—", "-")
        .replace("–", "-")
    )
    # Collapse multiple spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned


def parse_date_from_text(raw_text: str) -> date | None:
    """
    Search recognized OCR text for a valid capture date.
    Returns datetime.date if found and valid, or None.
    """
    if not raw_text or not raw_text.strip():
        return None

    text = _clean_ocr_date_text(raw_text)

    # 1. Day-of-week prefix + DD/MM/YYYY (e.g. "Wednesday, 18/11/2026" or "Wed, 18-11-2026")
    m = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*[,\s]+"
        r"(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(19\d\d|20\d\d)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d)
        except ValueError:
            pass

    # 2. Text month formats: e.g. "18 Nov 2026", "18 November 2026"
    month_names = "|".join(MONTH_MAP.keys())
    m = re.search(
        rf"\b(\d{{1,2}})\s+({month_names})\s+(19\d\d|20\d\d)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        d, mo_str, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        try:
            return date(y, MONTH_MAP[mo_str], d)
        except ValueError:
            pass

    # "Nov 18, 2026" or "November 18 2026"
    m = re.search(
        rf"\b({month_names})\s+(\d{{1,2}})[,\s]+(19\d\d|20\d\d)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        mo_str, d, y = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        try:
            return date(y, MONTH_MAP[mo_str], d)
        except ValueError:
            pass

    # 3. ISO / EXIF standard format: YYYY-MM-DD or YYYY:MM:DD or YYYY/MM/DD
    m = re.search(
        r"\b(19\d\d|20\d\d)[/\-\.:](\d{1,2})[/\-\.:](\d{1,2})\b",
        text,
    )
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d)
        except ValueError:
            pass

    # 4. Explicit labeled date format: e.g. "Date: 18/11/2026" or "Captured: 18-11-2026"
    m = re.search(
        r"(?:date|captured|timestamp|time)[:\s]+(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(19\d\d|20\d\d)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d)
        except ValueError:
            pass

    # 5. Standard standalone DD/MM/YYYY or DD-MM-YYYY
    # Prefer DD/MM/YYYY (standard in field photos and Indian/international camera stamps)
    for match in re.finditer(
        r"\b(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(19\d\d|20\d\d)\b",
        text,
    ):
        v1, v2, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        # If v1 > 12, it must be day
        if v1 > 12 and 1 <= v2 <= 12:
            try:
                return date(y, v2, v1)
            except ValueError:
                continue
        # If v2 > 12, it must be MM/DD/YYYY
        elif v2 > 12 and 1 <= v1 <= 12:
            try:
                return date(y, v1, v2)
            except ValueError:
                continue
        # Default: assume DD/MM/YYYY
        elif 1 <= v1 <= 31 and 1 <= v2 <= 12:
            try:
                return date(y, v2, v1)
            except ValueError:
                continue

    return None

