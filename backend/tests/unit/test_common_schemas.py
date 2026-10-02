import pytest
from pydantic import ValidationError

from app.schemas.common import BoundsWGS84, Confidence, Latitude, Longitude
from pydantic import TypeAdapter


def test_latitude_accepts_valid_value():
    adapter = TypeAdapter(Latitude)

    assert adapter.validate_python(16.7) == 16.7


def test_latitude_rejects_out_of_range_value():
    adapter = TypeAdapter(Latitude)

    with pytest.raises(ValidationError):
        adapter.validate_python(91.0)


def test_longitude_accepts_valid_value():
    adapter = TypeAdapter(Longitude)

    assert adapter.validate_python(74.24) == 74.24


def test_confidence_accepts_range():
    adapter = TypeAdapter(Confidence)

    assert adapter.validate_python(0.92) == 0.92


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_finite_float_rejects_non_finite_values(value):
    from app.schemas.common import FiniteFloat

    adapter = TypeAdapter(FiniteFloat)

    with pytest.raises(ValidationError):
        adapter.validate_python(value)


def test_bounds_wgs84_can_be_constructed():
    bounds = BoundsWGS84(
        min_longitude=74.0,
        min_latitude=16.5,
        max_longitude=74.5,
        max_latitude=17.0,
    )

    assert bounds.as_list() == [74.0, 16.5, 74.5, 17.0]