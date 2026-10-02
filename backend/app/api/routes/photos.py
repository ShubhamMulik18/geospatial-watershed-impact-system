from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.photo import PhotoResponse
from app.services.photo_service import PhotoService


router = APIRouter(prefix="/photos", tags=["photos"])


@router.post(
    "/upload",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> PhotoResponse:
    data = await file.read()

    try:
        photo = PhotoService(db=db).create_photo(
            data=data,
            original_name=file.filename or "",
            content_type=file.content_type,
        )
    except AppError:
        raise
    except ValueError as exc:
        raise AppError(str(exc), status_code=400) from exc

    warnings: list[str] = []

    if photo.gps_latitude is None or photo.gps_longitude is None:
        warnings.append("GPS location is unavailable.")

    if photo.captured_at is None:
        warnings.append("Capture date is unavailable.")

    return PhotoResponse(
        photo_id=str(photo.id),
        latitude=photo.gps_latitude,
        longitude=photo.gps_longitude,
        capture_date=photo.captured_at,
        exif_status=photo.exif_status,
        warnings=warnings,
    )
