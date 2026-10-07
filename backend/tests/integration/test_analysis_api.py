import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.main import app
from app.models.analysis import Analysis
from app.models.analysis_dataset import AnalysisDataset
from app.models.dataset import Dataset
from app.models.photo import Photo
from app.models.prediction import Prediction


client = TestClient(app)


def _make_photo() -> Photo:
    return Photo(
        id=uuid.uuid4(),
        safe_path="photos/api-analysis.jpg",
        original_name="api-analysis.jpg",
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
        capabilities=["ndvi", "water"],
        manifest={"source": "api-integration-test"},
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


def test_create_analysis_api_returns_202_and_persists_analysis() -> None:
    db = SessionLocal()

    photo = _make_photo()
    prediction = _make_prediction(photo)

    dataset_a = _make_dataset(
        display_name="API Dataset 2021",
        acquisition_date=date(2021, 2, 15),
        sha256="a" * 64,
    )
    dataset_b = _make_dataset(
        display_name="API Dataset 2026",
        acquisition_date=date(2026, 2, 17),
        sha256="b" * 64,
    )

    analysis_id = None

    try:
        db.add_all([photo, prediction, dataset_a, dataset_b])
        db.commit()

        response = client.post(
            "/api/analyses",
            json={
                "photo_id": str(photo.id),
                "polygon": {
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
                "dataset_ids": [
                    str(dataset_a.id),
                    str(dataset_b.id),
                ],
                "indicators": ["ndvi", "water"],
            },
        )

        assert response.status_code == 202

        body = response.json()

        assert body["schema_version"] == "1.0"
        assert body["status"] == "created"
        assert body["stage"] == "created"
        assert body["inputs"]["photo_id"] == str(photo.id)
        assert body["inputs"]["dataset_ids"] == [
            str(dataset_a.id),
            str(dataset_b.id),
        ]
        assert body["inputs"]["indicators"] == ["ndvi", "water"]

        analysis_id = uuid.UUID(body["analysis_id"])

        persisted = db.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        ).scalar_one()

        links = db.execute(
            select(AnalysisDataset)
            .where(AnalysisDataset.analysis_id == analysis_id)
            .order_by(AnalysisDataset.sequence)
        ).scalars().all()

        assert persisted.status == "created"
        assert persisted.photo_id == photo.id
        assert persisted.prediction_id == prediction.id
        assert persisted.prediction_snapshot["class"] == "Check Dam"
        assert len(links) == 2

    finally:
        if db.in_transaction():
            db.rollback()

        if analysis_id is not None:
            db.execute(
                delete(AnalysisDataset).where(
                    AnalysisDataset.analysis_id == analysis_id
                )
            )
            db.execute(
                delete(Analysis).where(
                    Analysis.id == analysis_id
                )
            )

        db.execute(
            delete(Prediction).where(
                Prediction.id == prediction.id
            )
        )
        db.execute(
            delete(Photo).where(
                Photo.id == photo.id
            )
        )
        db.execute(
            delete(Dataset).where(
                Dataset.id.in_([dataset_a.id, dataset_b.id])
            )
        )
        db.commit()
        db.close()
def test_get_analysis_api_returns_persisted_analysis() -> None:
    db = SessionLocal()

    photo = _make_photo()
    prediction = _make_prediction(photo)

    dataset_a = _make_dataset(
        display_name="GET Dataset 2021",
        acquisition_date=date(2021, 2, 15),
        sha256="c" * 64,
    )
    dataset_b = _make_dataset(
        display_name="GET Dataset 2026",
        acquisition_date=date(2026, 2, 17),
        sha256="d" * 64,
    )

    analysis_id = None

    try:
        db.add_all([photo, prediction, dataset_a, dataset_b])
        db.commit()

        create_response = client.post(
            "/api/analyses",
            json={
                "photo_id": str(photo.id),
                "polygon": {
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
                "dataset_ids": [str(dataset_a.id), str(dataset_b.id)],
                "indicators": ["ndvi", "water"],
            },
        )

        assert create_response.status_code == 202
        analysis_id = uuid.UUID(create_response.json()["analysis_id"])

        response = client.get(f"/api/analyses/{analysis_id}")

        assert response.status_code == 200

        body = response.json()

        assert body["schema_version"] == "1.0"
        assert body["analysis_id"] == str(analysis_id)
        assert body["status"] == "created"
        assert body["stage"] == "created"
        assert body["inputs"]["photo_id"] == str(photo.id)
        assert body["inputs"]["dataset_ids"] == [
            str(dataset_a.id),
            str(dataset_b.id),
        ]
        assert body["inputs"]["indicators"] == ["ndvi", "water"]
        assert body["inputs"]["polygon"] == {
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
        }
        assert body["prediction"]["class"] == "Check Dam"
        assert body["prediction"]["class_id"] == "check_dam"
        assert body["prediction"]["confidence"] == 0.92
        assert body["metrics"] is None
        assert body["series"] == []
        assert body["comparisons"] == []
        assert body["layers"] == []
        assert body["quality"] is None
        assert body["warnings"] == []
        assert body["provenance"] is None
        assert body["report_status"] == "not_requested"
        assert body["error"] is None

    finally:
        if db.in_transaction():
            db.rollback()

        if analysis_id is not None:
            db.execute(
                delete(AnalysisDataset).where(
                    AnalysisDataset.analysis_id == analysis_id
                )
            )
            db.execute(
                delete(Analysis).where(
                    Analysis.id == analysis_id
                )
            )

        db.execute(
            delete(Prediction).where(
                Prediction.id == prediction.id
            )
        )
        db.execute(
            delete(Photo).where(
                Photo.id == photo.id
            )
        )
        db.execute(
            delete(Dataset).where(
                Dataset.id.in_([dataset_a.id, dataset_b.id])
            )
        )
        db.commit()
        db.close()


def test_get_analysis_api_returns_404_for_unknown_analysis() -> None:
    response = client.get(f"/api/analyses/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NotFoundError"
    assert response.json()["error"]["message"] == "Analysis not found."
