from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.photo import EXIFStatus, PhotoResponse


def test_photo_response_matches_complete_contract():
    response = PhotoResponse(
        photo_id="photo-001",
        latitude=16.7,
        longitude=74.24,
        capture_date=date(2026, 2, 17),
        exif_status=EXIFStatus.AVAILABLE,
        warnings=[],
    )

    assert response.model_dump() == {
        "photo_id": "photo-001",
        "latitude": 16.7,
        "longitude": 74.24,
        "capture_date": date(2026, 2, 17),
        "exif_status": "available",
        "warnings": [],
    }


def test_photo_response_allows_missing_exif():
    response = PhotoResponse(
        photo_id="photo-001",
        latitude=None,
        longitude=None,
        capture_date=None,
        exif_status=EXIFStatus.MISSING,
        warnings=["Capture date is unavailable."],
    )

    assert response.latitude is None
    assert response.longitude is None
    assert response.capture_date is None
    assert response.exif_status == EXIFStatus.MISSING
    assert response.warnings == ["Capture date is unavailable."]


@pytest.mark.parametrize(
    "latitude, longitude",
    [
        (91.0, 74.24),
        (-91.0, 74.24),
        (16.7, 181.0),
        (16.7, -181.0),
    ],
)
def test_photo_response_rejects_invalid_coordinates(latitude, longitude):
    with pytest.raises(ValidationError):
        PhotoResponse(
            photo_id="photo-001",
            latitude=latitude,
            longitude=longitude,
            capture_date=None,
            exif_status=EXIFStatus.PARTIAL,
        )