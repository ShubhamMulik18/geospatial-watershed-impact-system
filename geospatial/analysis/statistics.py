import numpy as np


def calculate_statistics(data):
    """
    Calculate basic statistics for valid raster values.
    """

    data = np.asarray(data, dtype=float)

    valid = data[np.isfinite(data)]

    if valid.size == 0:
        return {
            "mean": None,
            "minimum": None,
            "maximum": None,
            "median": None,
            "valid_pixel_count": 0,
        }

    return {
        "mean": float(np.mean(valid)),
        "minimum": float(np.min(valid)),
        "maximum": float(np.max(valid)),
        "median": float(np.median(valid)),
        "valid_pixel_count": int(valid.size),
    }
def calculate_valid_fraction(data):
    """
    Calculate the fraction of valid pixels.
    """

    data = np.asarray(data, dtype=float)

    total_pixels = data.size

    if total_pixels == 0:
        return 0.0

    valid_pixels = np.count_nonzero(np.isfinite(data))

    return float(valid_pixels / total_pixels)
def calculate_area_from_mask(mask, pixel_width, pixel_height):
    """
    Calculate area in hectares from a boolean pixel mask.
    """

    mask = np.asarray(mask, dtype=bool)

    valid_pixels = int(np.count_nonzero(mask))

    pixel_area_m2 = abs(pixel_width * pixel_height)

    area_m2 = valid_pixels * pixel_area_m2

    area_hectares = area_m2 / 10000.0

    return float(area_hectares)
def calculate_change(before, after):
    """
    Calculate absolute and percentage change.
    """

    if before is None or after is None:
        return {
            "absolute_change": None,
            "percentage_change": None,
        }

    absolute_change = after - before

    if before == 0:
        percentage_change = None
    else:
        percentage_change = (absolute_change / before) * 100

    return {
        "absolute_change": float(absolute_change),
        "percentage_change": (
            float(percentage_change)
            if percentage_change is not None
            else None
        ),
    }

