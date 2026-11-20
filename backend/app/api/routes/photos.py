from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.integrations.ai.adapter import DevelopmentAIAdapter
from app.integrations.ai.base import AIAdapter
from app.integrations.ai.production_adapter import ProductionAIAdapter
from app.models.user import User
from app.schemas.photo import PhotoResponse
from app.schemas.prediction import PredictionResponse
from app.services.photo_service import PhotoService
from app.services.prediction_service import PredictionService


router = APIRouter(prefix="/photos", tags=["photos"])


def get_ai_adapter() -> AIAdapter:
    settings = get_settings()

    bundle_dir = Path(settings.ai_bundle_dir)
    if not bundle_dir.is_absolute() and not bundle_dir.exists():
        repo_root = Path(__file__).resolve().parents[4]
        if (repo_root / bundle_dir).exists():
            bundle_dir = repo_root / bundle_dir

    if bundle_dir.is_dir() and (bundle_dir / "model.pt").is_file():
        try:
            return ProductionAIAdapter(
                bundle_dir=bundle_dir,
                device=settings.ai_device,
            )
        except Exception as exc:
            raise AppError(
                f"Production AI model failed to initialize: {exc}",
                status_code=500,
                code="AI_INITIALIZATION_FAILED",
            )

    raise AppError(
        f"Production AI model bundle was not found at '{settings.ai_bundle_dir}'.",
        status_code=500,
        code="AI_BUNDLE_UNAVAILABLE",
    )


@router.post(
    "/upload",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    data = file.file.read()

    try:
        photo = PhotoService(db=db).create_photo(
            data=data,
            original_name=file.filename or "",
            content_type=file.content_type,
        )
        db.commit()
    except AppError:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise AppError(str(exc), status_code=400) from exc
    except Exception:
        db.rollback()
        raise

    warnings = getattr(photo, "metadata_warnings", None)
    if warnings is None:
        warnings = []
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
    current_user: User = Depends(get_current_user),
) -> PredictionResponse:
    try:
        prediction = PredictionService(
            db=db,
            ai_adapter=ai_adapter,
        ).create_prediction(photo_id)

        db.commit()

        warnings = list(getattr(prediction, "warnings", []) or [])
        if prediction.review_flag and not any("verification" in w.lower() for w in warnings):
            warnings.append("Human verification required: development model prediction.")

        return PredictionResponse(
            prediction_id=str(prediction.id),
            photo_id=str(prediction.photo_id),
            class_id=prediction.class_id,
            predicted_class=prediction.predicted_label,
            confidence=prediction.confidence,
            requires_verification=prediction.review_flag,
            model_version=prediction.model_version,
            warnings=warnings,
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
