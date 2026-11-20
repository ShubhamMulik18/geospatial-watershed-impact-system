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
from app.utils.ocr import extract_coordinates_from_image_bytes
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
        # 1. EXIF metadata extraction
        exif = extract_exif(data)

        # 2. OCR metadata extraction from visible photo text stamps
        ocr_result = extract_coordinates_from_image_bytes(data)

        # GPS coordinates priority: OCR if present, else EXIF
        if ocr_result.latitude is not None and ocr_result.longitude is not None:
            latitude = ocr_result.latitude
            longitude = ocr_result.longitude
            gps_from_ocr = True
        elif exif.latitude is not None and exif.longitude is not None:
            latitude = exif.latitude
            longitude = exif.longitude
            gps_from_ocr = False
        elif ocr_result.latitude is not None or ocr_result.longitude is not None:
            latitude = ocr_result.latitude if ocr_result.latitude is not None else exif.latitude
            longitude = ocr_result.longitude if ocr_result.longitude is not None else exif.longitude
            gps_from_ocr = True
        else:
            latitude = exif.latitude
            longitude = exif.longitude
            gps_from_ocr = False

        # Capture date source priority:
        # Priority 1: Genuine EXIF capture date
        # Priority 2: OCR recognized date from photo text stamp
        # Priority 3: None (unavailable)
        if exif.capture_date is not None:
            capture_date = exif.capture_date
            date_from_ocr = False
        elif ocr_result.capture_date is not None:
            capture_date = ocr_result.capture_date
            date_from_ocr = True
        else:
            capture_date = None
            date_from_ocr = False

        # EXIF status accurately reflects actual EXIF metadata (not falsely labeling OCR as EXIF)
        exif_status = exif.status

        # Build informative metadata warnings describing provenance
        metadata_warnings: list[str] = []
        if latitude is None or longitude is None:
            metadata_warnings.append("GPS location is unavailable.")
        elif gps_from_ocr and (exif.latitude is None or exif.longitude is None):
            metadata_warnings.append("GPS location extracted from photo text stamp via OCR (EXIF GPS unavailable).")

        if capture_date is None:
            metadata_warnings.append("Capture date is unavailable.")
        elif date_from_ocr and exif.capture_date is None:
            metadata_warnings.append("Capture date extracted from photo text stamp via OCR (EXIF date unavailable).")

        existing_photo = (
            self.db.query(Photo).filter(Photo.sha256 == sha256).first()
        )
        if isinstance(existing_photo, Photo):
            existing_photo.original_name = original_name
            existing_photo.mime_type = content_type or ""
            existing_photo.byte_size = byte_size
            existing_photo.gps_latitude = latitude
            existing_photo.gps_longitude = longitude
            existing_photo.captured_at = capture_date
            existing_photo.exif_status = exif_status
            existing_photo.metadata_warnings = metadata_warnings
            self.db.flush()
            return existing_photo

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
            gps_latitude=latitude,
            gps_longitude=longitude,
            captured_at=capture_date,
            exif_status=exif_status,
        )
        photo.metadata_warnings = metadata_warnings

        self.db.add(photo)
        self.db.flush()

        return photo
