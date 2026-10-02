from datetime import date
from io import BytesIO

from PIL import Image
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.photo import Photo
from app.services.photo_service import PhotoService


def _make_jpeg_with_exif() -> bytes:
    image = Image.new("RGB", (20, 20), "white")
    exif = image.getexif()

    exif[36867] = "2026:09:15 14:30:00"
    exif[34853] = {
        1: "N",
        2: (16.0, 42.0, 0.0),
        3: "E",
        4: (74.0, 14.0, 0.0),
    }

    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())

    return buffer.getvalue()


def test_photo_persists_to_postgresql(tmp_path) -> None:
    data = _make_jpeg_with_exif()

    db = SessionLocal()

    try:
        service = PhotoService(
            db=db,
            storage_root=tmp_path / "photos",
        )

        photo = service.create_photo(
            data=data,
            original_name="integration-photo.jpg",
            content_type="image/jpeg",
        )

        db.commit()

        persisted = db.execute(
            select(Photo).where(Photo.id == photo.id)
        ).scalar_one()

        assert persisted.original_name == "integration-photo.jpg"
        assert persisted.mime_type == "image/jpeg"
        assert persisted.byte_size == len(data)
        assert persisted.sha256 == photo.sha256
        assert persisted.gps_latitude == 16.7
        assert persisted.gps_longitude == 74.23333333333333
        assert persisted.captured_at == date(2026, 9, 15)
        assert persisted.exif_status == "available"

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(
            delete(Photo).where(Photo.original_name == "integration-photo.jpg")
        )
        db.commit()
        db.close()