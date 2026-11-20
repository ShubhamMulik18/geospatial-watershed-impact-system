import numpy as np

from geospatial.analysis.statistics import (
    calculate_statistics,
    calculate_valid_fraction,
    calculate_area_from_mask,
    calculate_change,
)


def test_calculate_statistics():
    data = np.array([1, 2, 3, np.nan])

    result = calculate_statistics(data)

    assert result["mean"] == 2.0
    assert result["minimum"] == 1.0
    assert result["maximum"] == 3.0
    assert result["median"] == 2.0
    assert result["valid_pixel_count"] == 3


def test_valid_fraction():
    data = np.array([1, 2, np.nan, 4])

    result = calculate_valid_fraction(data)

    assert result == 0.75


def test_area_calculation():
    mask = np.array(
        [
            [True, True],
            [False, False],
        ]
    )

    result = calculate_area_from_mask(
        mask,
        50,
        50,
    )

    assert result == 0.5


def test_change_calculation():
    result = calculate_change(10, 15)

    assert result["absolute_change"] == 5.0
    assert result["percentage_change"] == 50.0


def test_change_from_zero():
    result = calculate_change(0, 10)

    assert result["absolute_change"] == 10.0
    assert result["percentage_change"] is None
