def compare_values(before, after):
    """
    Compare a value before and after an intervention or time period.
    """

    if before is None or after is None:
        return {
            "before": before,
            "after": after,
            "absolute_change": None,
            "percentage_change": None,
        }

    absolute_change = after - before

    if before == 0:
        percentage_change = None
    else:
        percentage_change = (absolute_change / before) * 100

    return {
        "before": float(before),
        "after": float(after),
        "absolute_change": float(absolute_change),
        "percentage_change": (
            float(percentage_change)
            if percentage_change is not None
            else None
        ),
    }
def compare_arrays(before, after):
    """
    Calculate pixel-wise change between two raster arrays.
    """

    import numpy as np

    before = np.asarray(before, dtype=float)
    after = np.asarray(after, dtype=float)

    if before.shape != after.shape:
        raise ValueError(
            "Before and after arrays must have the same shape."
        )

    difference = after - before

    valid = np.isfinite(before) & np.isfinite(after)

    difference[~valid] = np.nan

    return difference
def compare_time_series(values):
    """
    Compare a time series and calculate changes between consecutive values.
    """

    if len(values) < 2:
        return []

    comparisons = []

    for i in range(len(values) - 1):
        before = values[i]
        after = values[i + 1]

        comparisons.append(
            compare_values(before, after)
        )

    return comparisons
def validate_comparison_shapes(before, after):
    """
    Validate that two raster arrays have the same shape.
    """

    if before.shape != after.shape:
        raise ValueError(
            "Before and after rasters must have the same shape."
        )

    return True
