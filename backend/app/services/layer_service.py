from typing import Any
import uuid

from app.models.artifact import Artifact
from app.schemas.analysis import LayerDescriptor


def calculate_polygon_bounds_wgs84(
    polygon: dict[str, Any] | None,
) -> tuple[float, float, float, float]:
    """Calculate (min_lon, min_lat, max_lon, max_lat) bounds from GeoJSON polygon."""
    if not polygon or not isinstance(polygon, dict):
        return (0.0, 0.0, 0.0, 0.0)

    coordinates = polygon.get("coordinates", [])
    all_points: list[list[float]] = []

    for ring in coordinates:
        if isinstance(ring, list):
            for point in ring:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    all_points.append(point)

    if not all_points:
        return (0.0, 0.0, 0.0, 0.0)

    min_lon = min(float(p[0]) for p in all_points)
    max_lon = max(float(p[0]) for p in all_points)
    min_lat = min(float(p[1]) for p in all_points)
    max_lat = max(float(p[1]) for p in all_points)

    return (min_lon, min_lat, max_lon, max_lat)


def _normalize_kind(raw_kind: str) -> str:
    lower = raw_kind.lower()
    if "ndvi" in lower:
        return "ndvi"
    if "water" in lower or "mndwi" in lower:
        return "water"
    return raw_kind


def _default_legend(normalized_kind: str) -> dict[str, object]:
    if normalized_kind == "ndvi":
        return {
            "Low NDVI (< 0.2)": "Sparse / Bare Soil",
            "Moderate NDVI (0.2 - 0.5)": "Shrub / Crops",
            "High NDVI (> 0.5)": "Dense Vegetation",
        }
    if normalized_kind == "water":
        return {
            "Detected Water": "Surface Water Body",
            "Non-Water": "Land / Vegetation",
            "Index Method": "MNDWI (Green - SWIR)",
        }
    return {}


def build_layer_descriptors(
    *,
    analysis_id: uuid.UUID | str,
    polygon: dict[str, Any] | None,
    artifacts: list[Artifact],
    default_dataset_ids: list[str] | None = None,
) -> list[LayerDescriptor]:
    """Build canonical LayerDescriptors from registered analysis artifacts."""
    if not artifacts:
        return []

    default_bounds = calculate_polygon_bounds_wgs84(polygon)
    fallback_dataset_id = (
        default_dataset_ids[0]
        if default_dataset_ids and len(default_dataset_ids) > 0
        else "dataset-1"
    )

    preview_map: dict[tuple[str, str], Artifact] = {}
    preview_artifacts: set[uuid.UUID] = set()

    for art in artifacts:
        meta = dict(art.metadata_json or {})
        ds_id = str(meta.get("dataset_id") or fallback_dataset_id)
        norm_kind = _normalize_kind(art.kind)

        is_preview = (
            art.mime_type == "image/png"
            or art.kind.lower().startswith("preview")
        )
        if is_preview:
            preview_map[(ds_id, norm_kind)] = art
            preview_artifacts.add(art.id)

    layers: list[LayerDescriptor] = []
    paired_previews: set[uuid.UUID] = set()

    # First, build layers from rasters (or non-preview artifacts)
    for art in artifacts:
        if art.id in preview_artifacts:
            continue
        if art.kind == "report" or art.mime_type == "application/pdf":
            continue

        meta = dict(art.metadata_json or {})
        ds_id = str(meta.get("dataset_id") or fallback_dataset_id)
        norm_kind = _normalize_kind(art.kind)

        bounds = default_bounds
        if "bounds_wgs84" in meta and isinstance(meta["bounds_wgs84"], (list, tuple)):
            if len(meta["bounds_wgs84"]) == 4:
                bounds = tuple(float(x) for x in meta["bounds_wgs84"])

        preview_crs = str(meta.get("preview_crs") or "EPSG:4326")
        download_url = f"/api/analyses/{analysis_id}/artifacts/{art.id}"

        preview_url = download_url
        matching_preview = preview_map.get((ds_id, norm_kind))
        if matching_preview is not None:
            preview_url = f"/api/analyses/{analysis_id}/artifacts/{matching_preview.id}"
            paired_previews.add(matching_preview.id)

        legend = meta.get("legend")
        if not isinstance(legend, dict):
            legend = _default_legend(norm_kind)

        layers.append(
            LayerDescriptor(
                layer_id=str(art.id),
                kind=norm_kind,
                dataset_id=ds_id,
                preview_url=preview_url,
                download_url=download_url,
                bounds_wgs84=bounds,
                preview_crs=preview_crs,
                legend=legend,
            )
        )

    # Second, add any preview artifacts that were not paired with a raster
    for art in artifacts:
        if art.id in preview_artifacts and art.id not in paired_previews:
            meta = dict(art.metadata_json or {})
            ds_id = str(meta.get("dataset_id") or fallback_dataset_id)
            norm_kind = _normalize_kind(art.kind)

            bounds = default_bounds
            if "bounds_wgs84" in meta and isinstance(meta["bounds_wgs84"], (list, tuple)):
                if len(meta["bounds_wgs84"]) == 4:
                    bounds = tuple(float(x) for x in meta["bounds_wgs84"])

            preview_crs = str(meta.get("preview_crs") or "EPSG:4326")
            url = f"/api/analyses/{analysis_id}/artifacts/{art.id}"

            legend = meta.get("legend")
            if not isinstance(legend, dict):
                legend = _default_legend(norm_kind)

            layers.append(
                LayerDescriptor(
                    layer_id=str(art.id),
                    kind=norm_kind,
                    dataset_id=ds_id,
                    preview_url=url,
                    download_url=url,
                    bounds_wgs84=bounds,
                    preview_crs=preview_crs,
                    legend=legend,
                )
            )

    return layers

