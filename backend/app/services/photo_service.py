from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.models.photo import Photo
from app.storage.photo_storage import generate_photo_path
from app.storage.photo_validation import (
    validate_photo_content_type,
    validate_photo_size,
    validate_photo_suffix,
)
from app.utils.file_hash import calculate_sha256
from app.utils.photo_exif import extract_exif, validate_image_bytes


PHOTO_STORAGE_ROOT = Path("uploads/photos")


class PhotoService:
    def __init__(
        self,
        db: Session,
        storage_root: Path = PHOTO_STORAGE_ROOT,
    ) -> None:
        self.db = db
        self.storage_root = storage_root

    def create_photo(
        self,
        data: bytes,
        original_name: str,
        content_type: str | None,
    ) -> Photo:
        byte_size = len(data)

        validate_photo_size(byte_size)
        content_suffix = validate_photo_content_type(content_type)
        filename_suffix = validate_photo_suffix(original_name)

        if filename_suffix == ".jpeg":
            filename_suffix = ".jpg"

        if content_suffix != filename_suffix:
            raise ValueError("Photo content type and file extension do not match.")

        validate_image_bytes(data)

        sha256 = calculate_sha256(data)
        exif = extract_exif(data)

        photo_id = uuid.uuid4()
        storage_path = generate_photo_path(
            self.storage_root,
            photo_id,
            filename_suffix,
        )

        self.storage_root.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(data)

        photo = Photo(
            id=photo_id,
            safe_path=str(storage_path),
            original_name=original_name,
            mime_type=content_type or "",
            byte_size=byte_size,
            sha256=sha256,
            gps_latitude=exif.latitude,
            gps_longitude=exif.longitude,
            captured_at=exif.capture_date,
            exif_status=exif.status,
        )

        self.db.add(photo)
        self.db.flush()

        return photo
