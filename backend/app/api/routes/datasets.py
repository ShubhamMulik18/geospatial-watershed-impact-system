import json

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.dataset import DatasetResponse
from app.services.dataset_response import build_dataset_response
from app.services.dataset_service import DatasetService


router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get(
    "",
    response_model=list[DatasetResponse],
    status_code=status.HTTP_200_OK,
)
def list_datasets(
    capability: str | None = None,
    db: Session = Depends(get_db),
) -> list[DatasetResponse]:
    datasets = DatasetService(db=db).list_datasets(
        capability=capability,
    )

    return [
        build_dataset_response(dataset)
        for dataset in datasets
    ]

@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile = File(...),
    display_name: str = Form(...),
    metadata_json: str = Form(...),
    db: Session = Depends(get_db),
) -> DatasetResponse:
    try:
        metadata = json.loads(metadata_json)

        if not isinstance(metadata, dict):
            raise ValueError("metadata_json must contain a JSON object.")

        dataset = DatasetService(db=db).create_dataset(
            stream=file.file,
            original_name=file.filename or "",
            display_name=display_name,
            metadata=metadata,
        )

        db.commit()

        return build_dataset_response(dataset)

    except AppError:
        db.rollback()
        raise
    except (ValueError, json.JSONDecodeError) as exc:
        db.rollback()
        raise AppError(str(exc), status_code=400) from exc
    except Exception:
        db.rollback()
        raise