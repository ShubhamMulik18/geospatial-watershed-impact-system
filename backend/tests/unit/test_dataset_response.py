from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.services.dataset_response import build_dataset_response


def test_build_dataset_response_transforms_bounds_to_wgs84() -> None:
    dataset = SimpleNamespace(
        id=uuid4(),
        display_name="Demo region 2026",
        year=2026,
        acquisition_date=date(2026, 9, 15),
        crs="EPSG:32643",
        bounds={
            "left": 500000.0,
            "bottom": 1999980.0,
            "right": 500020.0,
            "top": 2000000.0,
        },
        resolution={"x": 10.0, "y": 10.0},
        capabilities=["ndvi", "water"],
        quality_metadata=None,
        manifest={
            "water_methods": ["ndwi", "mndwi"],
            "warnings": [],
        },
    )

    response = build_dataset_response(dataset)

    assert response.dataset_id == str(dataset.id)
    assert response.display_name == "Demo region 2026"
    assert response.year == 2026
    assert response.acquisition_date == date(2026, 9, 15)
    assert response.supported_indicators == ["ndvi", "water"]
    assert response.water_methods == ["ndwi", "mndwi"]
    assert response.resolution_metres == 10.0
    assert response.quality_mask_available is False
    assert response.coverage_available is True
    assert response.bounds_wgs84[0] > 74.9
    assert response.bounds_wgs84[0] < 75.1
    assert response.bounds_wgs84[1] > 18.0
    assert response.bounds_wgs84[1] < 19.0
    assert response.bounds_wgs84[2] > response.bounds_wgs84[0]
    assert response.bounds_wgs84[3] > response.bounds_wgs84[1]