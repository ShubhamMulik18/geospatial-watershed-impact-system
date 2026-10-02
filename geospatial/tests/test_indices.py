import numpy as np

from geospatial.indices.ndvi import (
    calculate_ndvi,
    validate_ndvi,
)

from geospatial.indices.water import (
    calculate_ndwi,
    calculate_mndwi,
    validate_water_index,
)


def test_ndvi():
    red = np.array([0.2])
    nir = np.array([0.6])

    result = calculate_ndvi(nir, red)

    assert np.isclose(result[0], 0.5)


def test_ndvi_zero_denominator():
    red = np.array([0.0])
    nir = np.array([0.0])

    result = calculate_ndvi(nir, red)

    assert np.isnan(result[0])


def test_ndvi_validation():
    ndvi = np.array([-1.0, 0.0, 0.5, 1.0])

    assert validate_ndvi(ndvi)


def test_ndwi():
    green = np.array([0.6])
    nir = np.array([0.2])

    result = calculate_ndwi(green, nir)

    assert np.isclose(result[0], 0.5)


def test_mndwi():
    green = np.array([0.6])
    swir = np.array([0.2])

    result = calculate_mndwi(green, swir)

    assert np.isclose(result[0], 0.5)


def test_water_index_validation():
    index = np.array([-1.0, 0.0, 0.5, 1.0])

    assert validate_water_index(index)
