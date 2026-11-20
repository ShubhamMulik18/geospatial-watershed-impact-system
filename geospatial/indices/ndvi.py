import numpy as np


def calculate_ndvi(nir, red):
    """
    Calculate NDVI from NIR and Red bands.

    NDVI = (NIR - Red) / (NIR + Red)
    """

    nir = np.asarray(nir, dtype=float)
    red = np.asarray(red, dtype=float)

    denominator = nir + red

    ndvi = np.full_like(
        denominator,
        np.nan,
        dtype=float,
    )

    valid = denominator != 0

    ndvi[valid] = (
        (nir[valid] - red[valid])
        / denominator[valid]
    )

    return ndvi
def ndvi_statistics(ndvi):
    """
    Calculate basic statistics for an NDVI array.
    """
    valid = ndvi[np.isfinite(ndvi)]

    if valid.size == 0:
        return {
            "mean": None,
            "minimum": None,
            "maximum": None,
        }

    return {
        "mean": float(np.mean(valid)),
        "minimum": float(np.min(valid)),
        "maximum": float(np.max(valid)),
    }
def validate_ndvi(ndvi):
    """
    Validate that NDVI values are within the expected range [-1, 1].
    """
    valid = ndvi[np.isfinite(ndvi)]

    if valid.size == 0:
        return True

    if np.any(valid < -1) or np.any(valid > 1):
        raise ValueError("NDVI values must be between -1 and 1.")

    return True