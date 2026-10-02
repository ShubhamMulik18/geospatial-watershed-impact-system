import numpy as np


def valid_data_mask(data, nodata=None):
    """
    Create a mask showing which raster pixels contain valid data.
    """
    mask = np.isfinite(data)

    if nodata is not None:
        mask &= data != nodata

    return mask


def valid_pixel_fraction(data, nodata=None):
    """
    Calculate the fraction of valid pixels in a raster array.
    """
    mask = valid_data_mask(data, nodata)

    if mask.size == 0:
        return 0.0

    return float(mask.mean())
def check_minimum_valid_fraction(
    data,
    nodata=None,
    minimum_fraction=0.50,
):
    """
    Check whether the raster has enough valid pixels.
    """
    fraction = valid_pixel_fraction(data, nodata)

    if fraction < minimum_fraction:
        raise ValueError(
            f"Valid pixel fraction {fraction:.2f} "
            f"is below minimum required {minimum_fraction:.2f}."
        )

    return fraction
def apply_nodata_mask(data, nodata=None):
    """
    Replace invalid pixels with NaN.
    """
    result = data.astype(float).copy()

    mask = ~valid_data_mask(result, nodata)
    result[mask] = np.nan

    return result