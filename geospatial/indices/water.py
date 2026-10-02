import numpy as np


def calculate_ndwi(green, nir):
    """
    Calculate NDWI using Green and NIR bands.

    NDWI = (Green - NIR) / (Green + NIR)
    """

    green = np.asarray(green, dtype=float)
    nir = np.asarray(nir, dtype=float)

    denominator = green + nir

    ndwi = np.full_like(
        denominator,
        np.nan,
        dtype=float,
    )

    valid = denominator != 0

    ndwi[valid] = (
        (green[valid] - nir[valid])
        / denominator[valid]
    )

    return ndwi
def calculate_mndwi(green, swir):
    """
    Calculate MNDWI using Green and SWIR bands.

    MNDWI = (Green - SWIR) / (Green + SWIR)
    """

    green = np.asarray(green, dtype=float)
    swir = np.asarray(swir, dtype=float)

    denominator = green + swir

    mndwi = np.full_like(
        denominator,
        np.nan,
        dtype=float,
    )

    valid = denominator != 0

    mndwi[valid] = (
        (green[valid] - swir[valid])
        / denominator[valid]
    )

    return mndwi
def validate_water_index(index):
    """
    Validate that water-index values are within the expected range [-1, 1].
    """
    valid = index[np.isfinite(index)]

    if valid.size == 0:
        return True

    if np.any(valid < -1) or np.any(valid > 1):
        raise ValueError(
            "Water index values must be between -1 and 1."
        )

    return True