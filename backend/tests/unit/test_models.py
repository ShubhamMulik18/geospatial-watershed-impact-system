from sqlalchemy import UniqueConstraint

from app import models
from app.db.base import Base


EXPECTED_TABLES = {
    "photos",
    "datasets",
    "predictions",
    "analyses",
    "analysis_datasets",
    "analysis_results",
    "analysis_warnings",
    "artifacts",
}


def test_all_expected_models_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_photo_location_is_point_wgs84() -> None:
    column = Base.metadata.tables["photos"].c.location

    assert column.nullable is True
    assert column.type.geometry_type.upper() == "POINT"
    assert column.type.srid == 4326


def test_analysis_polygon_is_polygon_wgs84() -> None:
    column = Base.metadata.tables["analyses"].c.polygon

    assert column.nullable is False
    assert column.type.geometry_type.upper() == "POLYGON"
    assert column.type.srid == 4326


def test_analysis_dataset_has_unique_analysis_dataset_pair() -> None:
    table = Base.metadata.tables["analysis_datasets"]

    constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        set(constraint.columns.keys()) == {"analysis_id", "dataset_id"}
        for constraint in constraints
    )


def test_analysis_result_has_unique_analysis_id() -> None:
    table = Base.metadata.tables["analysis_results"]

    assert table.c.analysis_id.unique is True