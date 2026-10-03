from rasterio.warp import transform_bounds

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetResponse


def build_dataset_response(dataset: Dataset) -> DatasetResponse:
    bounds = dataset.bounds

    left, bottom, right, top = transform_bounds(
        dataset.crs,
        "EPSG:4326",
        bounds["left"],
        bounds["bottom"],
        bounds["right"],
        bounds["top"],
    )

    manifest = dataset.manifest or {}

    water_methods = manifest.get("water_methods", [])

    quality_mask_available = bool(
        dataset.quality_metadata
        or manifest.get("quality_mask")
        or manifest.get("quality_mask_path")
    )

    warnings: list[str] = list(manifest.get("warnings", []))

    return DatasetResponse(
        dataset_id=str(dataset.id),
        display_name=dataset.display_name,
        year=dataset.year,
        coverage_available=True,
        acquisition_date=dataset.acquisition_date,
        supported_indicators=list(dataset.capabilities),
        water_methods=list(water_methods),
        bounds_wgs84=(left, bottom, right, top),
        resolution_metres=float(dataset.resolution["x"])
        if dataset.resolution
        else None,
        quality_mask_available=quality_mask_available,
        warnings=warnings,
    )