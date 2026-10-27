import pytest

from geospatial.raster_processing.manifest import DatasetManifest


def valid_manifest():
    return DatasetManifest(
        acquisition_date="2026-01-01",
        sensor="TestSensor",
        product="TestProduct",
        bands={
            "red": 4,
            "nir": 5,
            "green": 3,
        },
        band_scaling={
            "red": {"scale": 0.0001, "offset": 0.0},
            "nir": {"scale": 0.0001, "offset": 0.0},
            "green": {"scale": 0.0001, "offset": 0.0},
        },
    )


def test_valid_manifest():
    manifest = valid_manifest()
    manifest.validate()


def test_missing_required_band():
    manifest = valid_manifest()
    del manifest.bands["nir"]

    with pytest.raises(ValueError, match="Missing required bands"):
        manifest.validate()


def test_invalid_band_number():
    manifest = valid_manifest()
    manifest.bands["red"] = 0

    with pytest.raises(ValueError, match="Invalid raster band number"):
        manifest.validate()


def test_missing_band_scaling():
    manifest = valid_manifest()
    del manifest.band_scaling["green"]

    with pytest.raises(ValueError, match="Missing scaling information"):
        manifest.validate()


def test_sentinel2_20260329_manifest():
    manifest = DatasetManifest(
        acquisition_date="2026-03-29",
        sensor="Sentinel-2B",
        product="MSIL2A",
        bands={
            "green": 3,
            "red": 4,
            "nir": 8,
            "swir": 11,
        },
        band_scaling={
            "green": {"scale": 0.0001, "offset": -0.1},
            "red": {"scale": 0.0001, "offset": -0.1},
            "nir": {"scale": 0.0001, "offset": -0.1},
            "swir": {"scale": 0.0001, "offset": -0.1},
        },
        quality_mask={
            "reference": "SCL_20m",
            "valid_classes": [4, 5, 6],
            "description": "Sentinel-2 Scene Classification Layer",
        },
        source="Sentinel-2B MSIL2A",
    )

    manifest.validate()

    assert manifest.acquisition_date == "2026-03-29"
    assert manifest.sensor == "Sentinel-2B"
    assert manifest.product == "MSIL2A"
    assert manifest.bands["green"] == 3
    assert manifest.bands["red"] == 4
    assert manifest.bands["nir"] == 8
    assert manifest.bands["swir"] == 11
    assert manifest.band_scaling["red"]["scale"] == 0.0001
    assert manifest.band_scaling["red"]["offset"] == -0.1
    assert manifest.quality_mask["valid_classes"] == [4, 5, 6]