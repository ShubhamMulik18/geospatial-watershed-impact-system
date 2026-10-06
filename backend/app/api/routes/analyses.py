from pathlib import Path
import json
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.artifact_service import ArtifactService
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisError,
    AnalysisInputs,
    AnalysisMetrics,
    AnalysisProvenance,
    AnalysisQuality,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSeriesPoint,
    AnalysisComparison,
    PredictionSnapshot,
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
    "/{analysis_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    try:
        analysis = AnalysisService(db=db).get_analysis(analysis_id)

        polygon_geojson = db.execute(
            select(func.ST_AsGeoJSON(analysis.polygon))
        ).scalar_one()

        polygon = json.loads(polygon_geojson)

        result_data = analysis.result.result if analysis.result else {}

        prediction = None
        if analysis.prediction_snapshot:
            prediction = PredictionSnapshot.model_validate(
                analysis.prediction_snapshot
            )

        metrics = (
            AnalysisMetrics.model_validate(result_data["metrics"])
            if result_data.get("metrics") is not None
            else None
        )

        series = [
            AnalysisSeriesPoint.model_validate(item)
            for item in result_data.get("series", [])
        ]

        comparisons = [
            AnalysisComparison.model_validate(item)
            for item in result_data.get("comparisons", [])
        ]

        quality = (
            AnalysisQuality.model_validate(result_data["quality"])
            if result_data.get("quality") is not None
            else None
        )

        provenance = (
            AnalysisProvenance.model_validate(result_data["provenance"])
            if result_data.get("provenance") is not None
            else None
        )

        error = None
        if analysis.error:
            error = AnalysisError(
                code="ANALYSIS_FAILED",
                message=analysis.error,
            )

        return AnalysisResponse(
            schema_version=analysis.result.schema_version
            if analysis.result
            else "1.0",
            analysis_id=str(analysis.id),
            status=analysis.status,
            stage=analysis.status,
            inputs=AnalysisInputs(
                photo_id=str(analysis.photo_id),
                polygon=polygon,
                dataset_ids=[
                    str(link.dataset_id)
                    for link in sorted(
                        analysis.dataset_links,
                        key=lambda link: link.sequence,
                    )
                ],
                indicators=analysis.indicators,
            ),
            prediction=prediction,
            metrics=metrics,
            series=series,
            comparisons=comparisons,
            layers=[],
            quality=quality,
            warnings=[
                warning.message
                for warning in analysis.warnings
            ],
            provenance=provenance,
            report_status="not_requested",
            error=error,
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
