from unittest.mock import MagicMock
import uuid

import pytest

from app.models.artifact import Artifact
from app.services.layer_service import (
    build_layer_descriptors,
    calculate_polygon_bounds_wgs84,
)


def _sample_polygon():
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [74.0, 18.0],
                [74.5, 18.0],
                [74.5, 18.5],
                [74.0, 18.5],
                [74.0, 18.0],
            ]
        ],
    }


def test_calculate_polygon_bounds_wgs84():
    bounds = calculate_polygon_bounds_wgs84(_sample_polygon())
    assert bounds == (74.0, 18.0, 74.5, 18.5)


def test_calculate_polygon_bounds_wgs84_empty():
    assert calculate_polygon_bounds_wgs84(None) == (0.0, 0.0, 0.0, 0.0)
    assert calculate_polygon_bounds_wgs84({"coordinates": []}) == (0.0, 0.0, 0.0, 0.0)


def test_build_layer_descriptors_empty_artifacts():
    analysis_id = uuid.uuid4()
    layers = build_layer_descriptors(
        analysis_id=analysis_id,
        polygon=_sample_polygon(),
        artifacts=[],
    )
    assert layers == []


def test_build_layer_descriptors_pairs_raster_and_preview():
    analysis_id = uuid.uuid4()
    raster_id = uuid.uuid4()
    preview_id = uuid.uuid4()

    raster_artifact = MagicMock(spec=Artifact)
    raster_artifact.id = raster_id
    raster_artifact.kind = "ndvi_raster"
    raster_artifact.mime_type = "image/tiff"
    raster_artifact.metadata_json = {"dataset_id": "dataset-2023"}

    preview_artifact = MagicMock(spec=Artifact)
    preview_artifact.id = preview_id
    preview_artifact.kind = "preview_ndvi"
    preview_artifact.mime_type = "image/png"
    preview_artifact.metadata_json = {"dataset_id": "dataset-2023"}

    layers = build_layer_descriptors(
        analysis_id=analysis_id,
        polygon=_sample_polygon(),
        artifacts=[raster_artifact, preview_artifact],
        default_dataset_ids=["dataset-2023"],
    )

    assert len(layers) == 1
    layer = layers[0]
    assert layer.layer_id == str(raster_id)
    assert layer.kind == "ndvi"
    assert layer.dataset_id == "dataset-2023"
    assert layer.download_url == f"/api/analyses/{analysis_id}/artifacts/{raster_id}"
    assert layer.preview_url == f"/api/analyses/{analysis_id}/artifacts/{preview_id}"
    assert layer.bounds_wgs84 == (74.0, 18.0, 74.5, 18.5)
    assert layer.preview_crs == "EPSG:4326"
    assert "Low NDVI (< 0.2)" in layer.legend


def test_build_layer_descriptors_standalone_raster_and_water_legend():
    analysis_id = uuid.uuid4()
    water_id = uuid.uuid4()

    water_artifact = MagicMock(spec=Artifact)
    water_artifact.id = water_id
    water_artifact.kind = "mndwi_raster"
    water_artifact.mime_type = "image/tiff"
    water_artifact.metadata_json = {"dataset_id": "dataset-2026"}

    layers = build_layer_descriptors(
        analysis_id=analysis_id,
        polygon=_sample_polygon(),
        artifacts=[water_artifact],
        default_dataset_ids=["dataset-2026"],
    )

    assert len(layers) == 1
    layer = layers[0]
    assert layer.layer_id == str(water_id)
    assert layer.kind == "water"
    assert layer.dataset_id == "dataset-2026"
    assert layer.preview_url == f"/api/analyses/{analysis_id}/artifacts/{water_id}"
    assert layer.download_url == f"/api/analyses/{analysis_id}/artifacts/{water_id}"
    assert "Detected Water" in layer.legend

