from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
from pathlib import Path
from app.core.config import get_settings
from app.services.artifact_service import ArtifactService
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisInputs,
    AnalysisRequest,
    AnalysisResponse,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    try:
        analysis = AnalysisService(db=db).create_analysis(request)
        db.commit()

        return AnalysisResponse(
            schema_version="1.0",
            analysis_id=str(analysis.id),
            status=analysis.status,
            stage="created",
            inputs=AnalysisInputs(
                photo_id=request.photo_id,
                polygon=request.polygon,
                dataset_ids=request.dataset_ids,
                indicators=request.indicators,
            ),
            prediction=None,
            metrics=None,
            series=[],
            comparisons=[],
            layers=[],
            quality=None,
            warnings=[],
            provenance=None,
            report_status="not_requested",
            error=None,
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

@router.get(
    "/{analysis_id}/artifacts/{artifact_id}",
    status_code=status.HTTP_200_OK,
)
def download_artifact(
    analysis_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        artifact_uuid = uuid.UUID(artifact_id)
    except ValueError as exc:
        raise AppError(
            "Invalid analysis or artifact ID.",
            status_code=404,
            code="ARTIFACT_NOT_FOUND",
        ) from exc

    settings = get_settings()

    path, mime_type, _ = ArtifactService(
        db=db,
        storage_root=Path(settings.artifact_storage_root),
    ).get_artifact_file(
        analysis_id=analysis_uuid,
        artifact_id=artifact_uuid,
    )

    return FileResponse(
        path=path,
        media_type=mime_type,
    )