from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.integrations.ai.adapter import DevelopmentAIAdapter
from app.integrations.ai.base import AIAdapter
from app.integrations.ai.production_adapter import ProductionAIAdapter
from app.schemas.photo import PhotoResponse
from app.schemas.prediction import PredictionResponse
from app.services.photo_service import PhotoService
from app.services.prediction_service import PredictionService


router = APIRouter(prefix="/photos", tags=["photos"])


def get_ai_adapter() -> AIAdapter:
    settings = get_settings()

    if settings.app_env.lower() == "production":
        return ProductionAIAdapter(
            bundle_dir=Path(settings.ai_bundle_dir),
            device=settings.ai_device,
        )

    return DevelopmentAIAdapter()


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


@router.post(
    "/{photo_id}/prediction",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction(
    photo_id: str,
    db: Session = Depends(get_db),
    ai_adapter: AIAdapter = Depends(get_ai_adapter),
) -> PredictionResponse:
    try:
        prediction = PredictionService(
            db=db,
            ai_adapter=ai_adapter,
        ).create_prediction(photo_id)

        db.commit()

        return PredictionResponse(
            prediction_id=str(prediction.id),
            photo_id=str(prediction.photo_id),
            class_id=prediction.class_id,
            predicted_class=prediction.predicted_label,
            confidence=prediction.confidence,
            requires_verification=prediction.review_flag,
            model_version=prediction.model_version,
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
