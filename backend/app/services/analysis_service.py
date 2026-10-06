import uuid
from datetime import datetime, timezone
from geoalchemy2 import WKTElement

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.integrations.geospatial.base import AnalysisResult as GeospatialAnalysisResult
from app.models.analysis import Analysis
from app.models.analysis_dataset import AnalysisDataset
from app.models.analysis_result import AnalysisResult
from app.models.analysis_warning import AnalysisWarning
from app.models.dataset import Dataset
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisStatus,
    AnalysisInputs,
    Indicator,
    PredictionSnapshot,
)


class AnalysisService:
    """Create and persist structurally validated analysis requests."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_analysis(self, request: AnalysisRequest) -> Analysis:
        photo = self._get_photo(request.photo_id)
        prediction = self._get_prediction(photo.id)
        datasets = self._get_datasets(request.dataset_ids)

        self._validate_indicator_capabilities(
            datasets=datasets,
            indicators=request.indicators,
        )

        prediction_snapshot = self._build_prediction_snapshot(prediction)

        analysis = Analysis(
            id=uuid.uuid4(),
            photo_id=photo.id,
            prediction_id=prediction.id,
            prediction_snapshot=prediction_snapshot,
            polygon=WKTElement(
                self._build_polygon_wkt(request),
                srid=4326,
            ),
            indicators=[indicator.value for indicator in request.indicators],
            status=AnalysisStatus.CREATED.value,
        )

        self.db.add(analysis)
        self.db.flush()

        for sequence, dataset in enumerate(datasets):
            self.db.add(
                AnalysisDataset(
                    analysis_id=analysis.id,
                    dataset_id=dataset.id,
                    sequence=sequence,
                    dataset_metadata_snapshot=self._build_dataset_snapshot(
                        dataset
                    ),
                    dataset_sha256=dataset.sha256,
                )
            )

        self.db.flush()

        return analysis

    def get_analysis(self, analysis_id: str) -> Analysis:
        """Load an analysis and its persisted response data."""
        try:
            analysis_uuid = uuid.UUID(analysis_id)
        except ValueError as exc:
            raise NotFoundError("Analysis not found.") from exc

        analysis = self.db.get(Analysis, analysis_uuid)

        if analysis is None:
            raise NotFoundError("Analysis not found.")

        return analysis

    def persist_analysis_result(
        self,
        analysis: Analysis,
        result: GeospatialAnalysisResult,
    ) -> AnalysisResult:
        """Persist a completed geospatial adapter result and its warnings."""
        provenance = dict(result.provenance or {})
        pipeline_version = str(
            provenance.get("pipeline_version")
            or provenance.get("adapter")
            or "unknown"
        )

        persisted_result = AnalysisResult(
            analysis_id=analysis.id,
            schema_version="1.0",
            result={
                "metrics": result.metrics,
                "series": result.series,
                "comparisons": result.comparisons,
                "quality": result.quality,
                "provenance": provenance,
            },
            pipeline_version=pipeline_version,
            completed_at=datetime.now(timezone.utc),
        )

        analysis.result = persisted_result

        analysis.warnings.clear()
        for warning in result.warnings:
            analysis.warnings.append(
                AnalysisWarning(
                    code="GEOSPATIAL_WARNING",
                    message=str(warning),
                    scope="analysis",
                )
            )

        self.db.flush()
        return persisted_result

    def _get_photo(self, photo_id: str) -> Photo:
        try:
            photo_uuid = uuid.UUID(photo_id)
        except ValueError:
            raise NotFoundError("Photo not found.")

        photo = self.db.get(Photo, photo_uuid)

        if photo is None:
            raise NotFoundError("Photo not found.")

        return photo

    def _get_prediction(self, photo_id: uuid.UUID) -> Prediction:
        prediction = (
            self.db.query(Prediction)
            .filter(Prediction.photo_id == photo_id)
            .order_by(Prediction.created_at.desc())
            .first()
        )

        if prediction is None:
           raise AppError(
                "A prediction is required before creating an analysis.",
                status_code=409,
                code="PREDICTION_REQUIRED",
            )

        return prediction

    def _get_datasets(self, dataset_ids: list[str]) -> list[Dataset]:
        parsed_ids: list[uuid.UUID] = []

        for dataset_id in dataset_ids:
            try:
                parsed_ids.append(uuid.UUID(dataset_id))
            except ValueError:
                raise NotFoundError(
                    f"Dataset '{dataset_id}' was not found."
                )

        datasets_by_id = {
            dataset.id: dataset
            for dataset in (
                self.db.query(Dataset)
                .filter(Dataset.id.in_(parsed_ids))
                .all()
            )
        }

        missing_ids = [
            dataset_id
            for dataset_id in parsed_ids
            if dataset_id not in datasets_by_id
        ]

        if missing_ids:
            raise NotFoundError(
                f"Dataset '{missing_ids[0]}' was not found."
            )

        return [datasets_by_id[dataset_id] for dataset_id in parsed_ids]

    @staticmethod
    def _validate_indicator_capabilities(
        datasets: list[Dataset],
        indicators: list[Indicator],
    ) -> None:
        requested = {indicator.value for indicator in indicators}

        for dataset in datasets:
            capabilities = set(dataset.capabilities or [])

            unsupported = requested - capabilities

            if unsupported:
                indicator = sorted(unsupported)[0]

                raise AppError(
                    (
                        f"Dataset '{dataset.id}' does not support "
                        f"indicator '{indicator}'."
                    ),
                    status_code=422,
                )

    @staticmethod
    def _build_prediction_snapshot(
        prediction: Prediction,
    ) -> dict:
        return PredictionSnapshot(
            class_name=prediction.predicted_label,
            class_id=str(prediction.label_id),
            confidence=prediction.confidence,
            requires_verification=prediction.review_flag,
            model_version=prediction.model_version,
        ).model_dump(by_alias=True)

    @staticmethod
    def _build_dataset_snapshot(dataset: Dataset) -> dict:
        return {
            "dataset_id": str(dataset.id),
            "display_name": dataset.display_name,
            "acquisition_date": dataset.acquisition_date.isoformat(),
            "year": dataset.year,
            "crs": dataset.crs,
            "transform": dataset.transform,
            "resolution": dataset.resolution,
            "bounds": dataset.bounds,
            "bands": dataset.bands,
            "scale": dataset.scale,
            "offset": dataset.offset,
            "capabilities": dataset.capabilities,
            "manifest": dataset.manifest,
        }

    @staticmethod
    @staticmethod
    def _build_polygon_wkt(request: AnalysisRequest) -> str:
        rings_wkt = []

        for ring in request.polygon.coordinates:
            coordinates = ", ".join(
                f"{longitude} {latitude}"
                for longitude, latitude in ring
            )
            rings_wkt.append(f"({coordinates})")

        return f"POLYGON ({', '.join(rings_wkt)})"