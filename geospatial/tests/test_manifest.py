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