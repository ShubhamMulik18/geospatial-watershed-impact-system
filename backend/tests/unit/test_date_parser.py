from datetime import date

import pytest

from app.utils.date_parser import parse_date_from_text


def test_parse_date_with_day_of_week_and_time():
    text = "Wednesday, 18/11/2026 08:19 PM GMT +05:30 Note : Captured by GPS Map Camera"
    assert parse_date_from_text(text) == date(2026, 11, 18)


def test_parse_date_with_day_of_week_october():
    text = "Wednesday, 28/10/2026 10:43 AM GMT +05:30"
    assert parse_date_from_text(text) == date(2026, 10, 28)


def test_parse_date_iso_format():
    text = "Inspection Timestamp: 2026-11-18 14:30:00"
    assert parse_date_from_text(text) == date(2026, 11, 18)


def test_parse_date_exif_colon_format():
    text = "EXIF 2026:10:24 11:30:00"
    assert parse_date_from_text(text) == date(2026, 10, 24)


def test_parse_date_text_month():
    assert parse_date_from_text("Captured on 18 Nov 2026") == date(2026, 11, 18)
    assert parse_date_from_text("November 18, 2026") == date(2026, 11, 18)
    assert parse_date_from_text("28 October 2026") == date(2026, 10, 28)


def test_parse_date_dd_mm_yyyy():
    assert parse_date_from_text("Date: 15/09/2025") == date(2025, 9, 15)
    assert parse_date_from_text("18-11-2026") == date(2026, 11, 18)
    assert parse_date_from_text("18.11.2026") == date(2026, 11, 18)


def test_parse_date_empty_or_invalid():
    assert parse_date_from_text("") is None
    assert parse_date_from_text("   ") is None
    assert parse_date_from_text("Latitude: 16.7050 Longitude: 74.2450") is None
    assert parse_date_from_text("32/13/2026 invalid date") is None
    assert parse_date_from_text("Project Dam Kolhapur Maharashtra") is None

