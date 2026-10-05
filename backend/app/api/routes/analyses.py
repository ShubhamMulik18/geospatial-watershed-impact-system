from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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