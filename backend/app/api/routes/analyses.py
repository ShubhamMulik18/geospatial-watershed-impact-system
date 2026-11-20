from pathlib import Path
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import SessionLocal, get_db
from app.models.analysis import Analysis
from app.models.user import User
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
    ReportStatus,
)
from app.services.analysis_service import AnalysisService
from app.services.artifact_registration_service import ArtifactRegistrationService
from app.services.artifact_service import ArtifactService
from app.services.layer_service import build_layer_descriptors
from app.workers.analysis_worker import AnalysisWorker
from geospatial.reports.build_report import build_report

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _run_worker_job() -> None:
    db = SessionLocal()
    try:
        worker = AnalysisWorker(db=db)
        worker.run_once()
    except Exception:
        pass
    finally:
        db.close()


def _format_analysis_response(analysis: Analysis, db: Session) -> AnalysisResponse:
    try:
        polygon_geojson = db.execute(
            select(func.ST_AsGeoJSON(analysis.polygon))
        ).scalar_one()
        polygon = json.loads(polygon_geojson)
    except Exception:
        polygon = {"type": "Polygon", "coordinates": []}

    result_data = analysis.result.result if analysis.result else {}

    prediction = None
    if analysis.prediction_snapshot:
        prediction = PredictionSnapshot.model_validate(
            analysis.prediction_snapshot
        )

    metrics_fields = set(AnalysisMetrics.model_fields.keys())
    metrics = (
        AnalysisMetrics.model_validate(
            {k: v for k, v in result_data["metrics"].items() if k in metrics_fields}
        )
        if result_data.get("metrics") is not None
        else None
    )

    series_fields = set(AnalysisSeriesPoint.model_fields.keys())
    series = [
        AnalysisSeriesPoint.model_validate(
            {k: v for k, v in item.items() if k in series_fields}
        )
        for item in result_data.get("series", [])
    ]

    comp_fields = set(AnalysisComparison.model_fields.keys())
    comparisons = [
        AnalysisComparison.model_validate(
            {k: v for k, v in item.items() if k in comp_fields}
        )
        for item in result_data.get("comparisons", [])
    ]

    quality_fields = set(AnalysisQuality.model_fields.keys())
    quality = (
        AnalysisQuality.model_validate(
            {k: v for k, v in result_data["quality"].items() if k in quality_fields}
        )
        if result_data.get("quality") is not None
        else None
    )

    prov_fields = set(AnalysisProvenance.model_fields.keys())
    provenance = (
        AnalysisProvenance.model_validate(
            {k: v for k, v in result_data["provenance"].items() if k in prov_fields}
        )
        if result_data.get("provenance") is not None
        else None
    )

    error = None
    if analysis.error:
        error = AnalysisError(
            code="ANALYSIS_FAILED",
            message=analysis.error,
        )

    dataset_ids = [
        str(link.dataset_id)
        for link in sorted(
            analysis.dataset_links,
            key=lambda link: link.sequence,
        )
    ]

    artifacts = list(analysis.artifacts or [])
    layers = build_layer_descriptors(
        analysis_id=analysis.id,
        polygon=polygon,
        artifacts=artifacts,
        default_dataset_ids=dataset_ids,
    )

    has_report = any(
        a.kind == "report" or a.mime_type == "application/pdf"
        for a in artifacts
    )
    report_status = (
        ReportStatus.READY if has_report
        else (ReportStatus.NOT_REQUESTED if analysis.status != "completed" else ReportStatus.NOT_REQUESTED)
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
            dataset_ids=dataset_ids,
            indicators=analysis.indicators,
        ),
        prediction=prediction,
        metrics=metrics,
        series=series,
        comparisons=comparisons,
        layers=layers,
        quality=quality,
        warnings=[
            warning.message
            for warning in analysis.warnings
        ],
        provenance=provenance,
        report_status=report_status,
        error=error,
    )


@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    try:
        analysis = AnalysisService(db=db).create_analysis(request)
        db.commit()

        background_tasks.add_task(_run_worker_job)

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
            report_status=ReportStatus.NOT_REQUESTED,
            error=None,
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "",
    response_model=list[AnalysisResponse],
    status_code=status.HTTP_200_OK,
)
def list_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalysisResponse]:
    analyses = db.execute(
        select(Analysis).order_by(Analysis.created_at.desc()).limit(20)
    ).scalars().all()

    return [_format_analysis_response(analysis, db) for analysis in analyses]


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    try:
        analysis = AnalysisService(db=db).get_analysis(analysis_id)
        return _format_analysis_response(analysis, db)
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{analysis_id}/report",
    status_code=status.HTTP_200_OK,
)
def download_report(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    try:
        uuid.UUID(analysis_id)
    except ValueError as exc:
        raise AppError(
            "Invalid analysis ID.",
            status_code=404,
            code="ANALYSIS_NOT_FOUND",
        ) from exc

    analysis = AnalysisService(db=db).get_analysis(analysis_id)
    if analysis.status != "completed":
        raise AppError(
            f"Analysis is currently '{analysis.status}'. Report is only available for completed analyses.",
            status_code=409,
            code="ANALYSIS_NOT_COMPLETED",
        )

    settings = get_settings()
    storage_root = Path(settings.artifact_storage_root)

    output_dir = storage_root / str(analysis.id)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file_name = f"report_{analysis.id}.pdf"
    report_file_path = output_dir / report_file_name

    # Collect all raster layer previews
    raster_layers = []
    for art in (analysis.artifacts or []):
        if art.mime_type == "image/png" or art.kind.startswith("preview"):
            art_path = (storage_root / art.safe_relative_path).resolve()
            if art_path.is_file():
                meta = dict(art.metadata_json or {})
                raster_layers.append({
                    "kind": art.kind,
                    "dataset_id": meta.get("dataset_id"),
                    "path": str(art_path),
                })

    # Field photo path
    photo_file_path = None
    if analysis.photo and getattr(analysis.photo, "safe_path", None):
        candidate_photo = Path(analysis.photo.safe_path)
        if candidate_photo.is_file():
            photo_file_path = str(candidate_photo.resolve())
        else:
            for base in [
                Path(__file__).resolve().parents[4],
                Path(__file__).resolve().parents[3],
                Path.cwd(),
                Path("D:/geospatial-watershed-impact-system"),
            ]:
                full_cand = (base / candidate_photo).resolve()
                if full_cand.is_file():
                    photo_file_path = str(full_cand)
                    break

    # Polygon GeoJSON
    polygon_geojson = None
    try:
        from geoalchemy2.shape import to_shape
        polygon_geojson = to_shape(analysis.polygon).__geo_interface__
    except Exception:
        pass

    # Datasets information from links
    dataset_info = []
    for link in sorted(analysis.dataset_links, key=lambda l: l.sequence):
        meta = dict(link.dataset_metadata_snapshot or {})
        dataset_info.append({
            "dataset_id": str(link.dataset_id),
            "display_name": meta.get("display_name") or f"Sentinel-2 Tile ({meta.get('year', 'Observation')})",
            "acquisition_date": meta.get("acquisition_date") or str(meta.get("year", "")),
            "year": meta.get("year"),
        })

    res_data = analysis.result.result if analysis.result and isinstance(analysis.result.result, dict) else {}

    payload = {
        "analysis_id": str(analysis.id),
        "title": "Geospatial Watershed Impact Analysis Report",
        "created_at": analysis.created_at.strftime("%Y-%m-%d %H:%M UTC") if analysis.created_at else None,
        "metrics": res_data.get("metrics", {}),
        "series": res_data.get("series", []),
        "comparisons": res_data.get("comparisons", []),
        "quality": res_data.get("quality", {}),
        "provenance": res_data.get("provenance", {}),
        "prediction": analysis.prediction_snapshot or {},
        "photo_path": photo_file_path,
        "photo_latitude": analysis.photo.gps_latitude if analysis.photo else None,
        "photo_longitude": analysis.photo.gps_longitude if analysis.photo else None,
        "photo_captured_at": analysis.photo.captured_at.strftime("%Y-%m-%d %H:%M") if analysis.photo and analysis.photo.captured_at else None,
        "polygon": polygon_geojson,
        "datasets": dataset_info,
        "raster_layers": raster_layers,
    }

    build_report(payload, report_file_path)

    report_artifact = next(
        (a for a in (analysis.artifacts or []) if a.kind == "report" or a.mime_type == "application/pdf"),
        None,
    )
    if report_artifact is None:
        ArtifactRegistrationService(
            db=db,
            storage_root=storage_root,
        ).register_artifacts(
            analysis_id=analysis.id,
            output_dir=output_dir,
            artifacts=[
                {
                    "kind": "report",
                    "relative_path": report_file_name,
                    "metadata": {"type": "pdf_report"},
                }
            ],
        )
        db.commit()

    return FileResponse(
        path=report_file_path,
        media_type="application/pdf",
        filename=f"watershed_analysis_{analysis.id}.pdf",
    )


@router.get(
    "/{analysis_id}/artifacts/{artifact_id}",
    status_code=status.HTTP_200_OK,
)
def download_artifact(
    analysis_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
