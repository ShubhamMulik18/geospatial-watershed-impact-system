import numpy as np

from geospatial.indices.ndvi import calculate_ndvi
from geospatial.indices.water import calculate_mndwi


def test_ndvi_basic():
    nir = np.array([0.8, 0.6], dtype=float)
    red = np.array([0.2, 0.2], dtype=float)

    result = calculate_ndvi(nir, red)

    expected = np.array([0.6, 0.5])

    np.testing.assert_allclose(result, expected)


def test_ndvi_zero_denominator():
    nir = np.array([0.0])
    red = np.array([0.0])

    result = calculate_ndvi(nir, red)

    assert np.isnan(result[0])


def test_mndwi_basic():
    green = np.array([0.6, 0.5], dtype=float)
    swir = np.array([0.2, 0.1], dtype=float)

    result = calculate_mndwi(green, swir)

    expected = np.array(
        [
            (0.6 - 0.2) / (0.6 + 0.2),
            (0.5 - 0.1) / (0.5 + 0.1),
        ]
    )

    np.testing.assert_allclose(result, expected)


def test_sentinel2_reflectance_scaling():
    # Official Sentinel-2 L2A metadata:
    # Reflectance = DN * 0.0001 - 0.1

    green_dn = np.array([7000], dtype=float)
    red_dn = np.array([3000], dtype=float)
    nir_dn = np.array([7000], dtype=float)
    swir_dn = np.array([3000], dtype=float)

    green = green_dn * 0.0001 - 0.1
    red = red_dn * 0.0001 - 0.1
    nir = nir_dn * 0.0001 - 0.1
    swir = swir_dn * 0.0001 - 0.1

    ndvi = calculate_ndvi(nir, red)
    mndwi = calculate_mndwi(green, swir)

    expected_ndvi = (0.6 - 0.2) / (0.6 + 0.2)
    expected_mndwi = (0.6 - 0.2) / (0.6 + 0.2)

    np.testing.assert_allclose(ndvi, [expected_ndvi])
    np.testing.assert_allclose(mndwi, [expected_mndwi])