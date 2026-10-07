import uuid
from datetime import date

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.analysis import Analysis
from app.models.analysis_dataset import AnalysisDataset
from app.models.dataset import Dataset
from app.models.photo import Photo
from app.models.prediction import Prediction
from app.schemas.analysis import AnalysisRequest
from app.services.analysis_service import AnalysisService


def _make_photo() -> Photo:
    return Photo(
        id=uuid.uuid4(),
        safe_path="photos/integration-analysis.jpg",
        original_name="integration-analysis.jpg",
        mime_type="image/jpeg",
        byte_size=1024,
        sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        exif_status="valid",
    )


def _make_dataset(
    *,
    display_name: str,
    acquisition_date: date,
    sha256: str,
    capabilities: list[str],
) -> Dataset:
    return Dataset(
        id=uuid.uuid4(),
        display_name=display_name,
        acquisition_date=acquisition_date,
        year=acquisition_date.year,
        path=f"datasets/{display_name.lower().replace(' ', '-')}.tif",
        sha256=sha256,
        crs="EPSG:32643",
        transform={
            "a": 10.0,
            "b": 0.0,
            "c": 500000.0,
            "d": 0.0,
            "e": -10.0,
            "f": 2000000.0,
        },
        resolution={"x": 10.0, "y": 10.0},
        bounds={
            "left": 500000.0,
            "bottom": 1999980.0,
            "right": 500020.0,
            "top": 2000000.0,
        },
        bands=[
            {"band": 1, "description": "Band 1"},
            {"band": 2, "description": "Band 2"},
            {"band": 3, "description": "Band 3"},
        ],
        scale=None,
        offset=None,
        quality_metadata={},
        capabilities=capabilities,
        manifest={"source": "integration-test"},
    )


def _make_prediction(photo: Photo) -> Prediction:
    return Prediction(
        id=uuid.uuid4(),
        photo_id=photo.id,
        model_version="intervention-mobilenetv2-v1",
        model_hash="test-model-hash",
        class_id="check_dam",
        predicted_label="Check Dam",
        confidence=0.92,
        top_candidate_class_id="check_dam",
        threshold=0.5,
        review_flag=False,
    )


def _make_request(
    photo: Photo,
    dataset_a: Dataset,
    dataset_b: Dataset,
) -> AnalysisRequest:
    return AnalysisRequest(
        photo_id=str(photo.id),
        polygon={
            "type": "Polygon",
            "coordinates": [
                [
                    [74.24, 16.70],
                    [74.25, 16.70],
                    [74.25, 16.71],
                    [74.24, 16.71],
                    [74.24, 16.70],
                ]
            ],
        },
        dataset_ids=[str(dataset_a.id), str(dataset_b.id)],
        indicators=["ndvi", "water"],
    )


def test_analysis_persists_prediction_and_dataset_snapshots() -> None:
    db = SessionLocal()

    photo = _make_photo()
    prediction = _make_prediction(photo)

    dataset_a = _make_dataset(
        display_name="Integration Dataset 2021",
        acquisition_date=date(2021, 2, 15),
        sha256="a" * 64,
        capabilities=["ndvi", "water"],
    )
    dataset_b = _make_dataset(
        display_name="Integration Dataset 2026",
        acquisition_date=date(2026, 2, 17),
        sha256="b" * 64,
        capabilities=["ndvi", "water"],
    )

    try:
        db.add_all([photo, prediction, dataset_a, dataset_b])
        db.commit()

        service = AnalysisService(db)
        analysis = service.create_analysis(
            _make_request(photo, dataset_a, dataset_b)
        )

        db.commit()

        persisted = db.execute(
            select(Analysis).where(Analysis.id == analysis.id)
        ).scalar_one()

        links = db.execute(
            select(AnalysisDataset)
            .where(AnalysisDataset.analysis_id == analysis.id)
            .order_by(AnalysisDataset.sequence)
        ).scalars().all()

        assert persisted.status == "created"
        assert persisted.photo_id == photo.id
        assert persisted.prediction_id == prediction.id
        assert persisted.indicators == ["ndvi", "water"]

        assert persisted.prediction_snapshot == {
            "class": "Check Dam",
            "class_id": "check_dam",
            "confidence": 0.92,
            "requires_verification": False,
            "model_version": "intervention-mobilenetv2-v1",
        }

        assert len(links) == 2
        assert links[0].dataset_id == dataset_a.id
        assert links[0].sequence == 0
        assert links[0].dataset_sha256 == "a" * 64
        assert links[0].dataset_metadata_snapshot["display_name"] == (
            "Integration Dataset 2021"
        )
        assert links[0].dataset_metadata_snapshot["year"] == 2021

        assert links[1].dataset_id == dataset_b.id
        assert links[1].sequence == 1
        assert links[1].dataset_sha256 == "b" * 64
        assert links[1].dataset_metadata_snapshot["display_name"] == (
            "Integration Dataset 2026"
        )
        assert links[1].dataset_metadata_snapshot["year"] == 2026

        assert persisted.polygon is not None

    finally:
        if db.in_transaction():
            db.rollback()

        if "analysis" in locals():
            db.execute(
                delete(AnalysisDataset).where(
                    AnalysisDataset.analysis_id == analysis.id
                )
            )
            db.execute(
                delete(Analysis).where(Analysis.id == analysis.id)
            )

        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.execute(
            delete(Dataset).where(
                Dataset.id.in_([dataset_a.id, dataset_b.id])
            )
        )
        db.commit()
        db.close()


def test_analysis_requires_prediction() -> None:
    db = SessionLocal()

    photo = _make_photo()
    dataset_a = _make_dataset(
        display_name="Missing Prediction Dataset 2021",
        acquisition_date=date(2021, 2, 15),
        sha256="c" * 64,
        capabilities=["ndvi", "water"],
    )
    dataset_b = _make_dataset(
        display_name="Missing Prediction Dataset 2026",
        acquisition_date=date(2026, 2, 17),
        sha256="d" * 64,
        capabilities=["ndvi", "water"],
    )

    try:
        db.add_all([photo, dataset_a, dataset_b])
        db.commit()

        service = AnalysisService(db)

        try:
            service.create_analysis(
                _make_request(photo, dataset_a, dataset_b)
            )
        except Exception as exc:
            assert exc.status_code == 409
            assert exc.code == "PREDICTION_REQUIRED"
        else:
            raise AssertionError(
                "AnalysisService should reject analysis creation without prediction."
            )

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.execute(
            delete(Dataset).where(
                Dataset.id.in_([dataset_a.id, dataset_b.id])
            )
        )
        db.commit()
        db.close()


def test_analysis_rejects_unsupported_indicator() -> None:
    db = SessionLocal()

    photo = _make_photo()
    prediction = _make_prediction(photo)

    dataset_a = _make_dataset(
        display_name="Unsupported Indicator Dataset 2021",
        acquisition_date=date(2021, 2, 15),
        sha256="e" * 64,
        capabilities=["ndvi"],
    )
    dataset_b = _make_dataset(
        display_name="Unsupported Indicator Dataset 2026",
        acquisition_date=date(2026, 2, 17),
        sha256="f" * 64,
        capabilities=["ndvi"],
    )

    try:
        db.add_all([photo, prediction, dataset_a, dataset_b])
        db.commit()

        service = AnalysisService(db)

        try:
            service.create_analysis(
                _make_request(photo, dataset_a, dataset_b)
            )
        except Exception as exc:
            assert exc.status_code == 422
        else:
            raise AssertionError(
                "AnalysisService should reject unsupported indicators."
            )

    finally:
        if db.in_transaction():
            db.rollback()

        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.execute(delete(Photo).where(Photo.id == photo.id))
        db.execute(
            delete(Dataset).where(
                Dataset.id.in_([dataset_a.id, dataset_b.id])
            )
        )
        db.commit()
        db.close()
