from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio
from rasterio.mask import mask

from geospatial.contracts import (
    AnalysisRequest,
    ArtifactDescriptor,
    GeospatialResult,
)
from geospatial.indices.ndvi import calculate_ndvi
from geospatial.indices.water import calculate_mndwi
from geospatial.analysis.statistics import (
    calculate_statistics,
    calculate_valid_fraction,
    calculate_change,
)
from geospatial.raster_processing.geometry import (
    polygon_from_geojson,
    validate_geometry,
    transform_geometry,
)
from geospatial.outputs.rasters import save_raster


SUPPORTED_INDICATORS = {"ndvi", "water"}


def _get_first_dataset(request):
    if not request.dataset_specs:
        raise ValueError("At least one dataset specification is required.")
    return request.dataset_specs[0]


def _get_raster_path(dataset):
    path = (
        dataset.get("path")
        or dataset.get("raster_path")
        or dataset.get("resolved_path")
    )
    if not path:
        raise ValueError(
            "Dataset specification is missing its resolved raster path."
        )

    raster_path = Path(path)
    if not raster_path.is_file():
        raise FileNotFoundError(
            f"Raster file does not exist: {raster_path}"
        )
    return raster_path


def _get_band_mapping(dataset):
    bands = dataset.get("bands")
    manifest = dataset.get("manifest")

    if not bands and isinstance(manifest, dict):
        bands = manifest.get("bands")

    if not isinstance(bands, dict):
        raise ValueError(
            "Dataset must provide semantic band mappings, "
            "for example {'red': 4, 'nir': 5}."
        )

    return bands


def _get_scaling(dataset, band_name, band_number):
    """Return verified scale and offset; do not guess defaults."""
    manifest = dataset.get("manifest") or {}
    band_scaling = (
        dataset.get("band_scaling")
        or manifest.get("band_scaling")
        or {}
    )

    scaling = band_scaling.get(band_name)
    if scaling is not None:
        if "scale" not in scaling or "offset" not in scaling:
            raise ValueError(
                f"Scaling for '{band_name}' must include scale and offset."
            )
        return float(scaling["scale"]), float(scaling["offset"])

    scales = dataset.get("scale")
    offsets = dataset.get("offset")

    if scales is not None or offsets is not None:
        if scales is None or offsets is None:
            raise ValueError(
                "Dataset scale and offset metadata must both be provided."
            )

        scale = scales.get(str(band_number), scales.get(band_number))
        offset = offsets.get(str(band_number), offsets.get(band_number))

        if scale is None or offset is None:
            raise ValueError(
                f"Missing scale/offset for raster band {band_number} "
                f"('{band_name}')."
            )

        return float(scale), float(offset)

    raise ValueError(
        f"Missing verified scale/offset metadata for '{band_name}'."
    )


def _read_scaled_band(src, dataset, band_name, band_number):
    if not isinstance(band_number, int) or band_number < 1:
        raise ValueError(
            f"Invalid one-based band index for '{band_name}': "
            f"{band_number!r}"
        )

    if band_number > src.count:
        raise ValueError(
            f"Band '{band_name}' maps to band {band_number}, "
            f"but the raster contains only {src.count} band(s)."
        )

    raw = src.read(band_number, masked=True).astype(np.float32)
    raw_data = np.asarray(raw.filled(np.nan), dtype=np.float32)

    scale, offset = _get_scaling(dataset, band_name, band_number)
    data = raw_data * scale + offset

    manifest = dataset.get("manifest") or {}
    nodata = dataset.get("nodata", manifest.get("nodata", src.nodata))

    if nodata is not None:
        data[raw_data == nodata] = np.nan

    data[~np.isfinite(raw_data)] = np.nan
    return data


def _validate_requested_indicators(indicators):
    if not indicators:
        raise ValueError("At least one indicator must be requested.")

    unknown = set(indicators) - SUPPORTED_INDICATORS
    if unknown:
        raise ValueError(
            f"Unsupported indicator(s): {sorted(unknown)}. "
            f"Supported indicators are {sorted(SUPPORTED_INDICATORS)}."
        )


def run_analysis(request, output_dir, progress_callback=None):
    """
    Calculate requested NDVI and/or MNDWI indicators from raster datasets.

    Dataset specifications must contain a resolved raster path, semantic
    one-based band mappings, and verified scale/offset metadata.
    The request polygon must be GeoJSON in EPSG:4326.
    """
    if not isinstance(request, AnalysisRequest):
        raise TypeError("request must be an AnalysisRequest.")

    _validate_requested_indicators(request.indicators)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    geometry = polygon_from_geojson(request.polygon)
    validate_geometry(geometry)

    required_bands = set()
    if "ndvi" in request.indicators:
        required_bands.update(("red", "nir"))
    if "water" in request.indicators:
        required_bands.update(("green", "swir"))

    all_statistics = {}
    series = []
    artifacts = []
    warnings = []
    dataset_ids = []

    for index, dataset in enumerate(request.dataset_specs):
        dataset_id = str(dataset.get("dataset_id", f"dataset-{index + 1}"))
        dataset_ids.append(dataset_id)

        raster_path = _get_raster_path(dataset)
        band_mapping = _get_band_mapping(dataset)

        missing = required_bands - set(band_mapping)
        if missing:
            raise ValueError(
                f"Dataset '{dataset_id}' is missing required band mappings: "
                f"{sorted(missing)}."
            )

        with rasterio.open(raster_path) as src:
            if src.crs is None:
                raise ValueError(
                    f"Raster '{raster_path}' has no CRS."
                )

            raster_geometry = transform_geometry(
                geometry,
                "EPSG:4326",
                src.crs,
            )

            try:
                clipped, clipped_transform = mask(
                    src,
                    [raster_geometry.__geo_interface__],
                    crop=True,
                    filled=False,
                )
            except ValueError as exc:
                raise ValueError(
                    f"Polygon does not overlap raster for dataset "
                    f"'{dataset_id}', or the raster cannot be clipped: {exc}"
                ) from exc

            # Read the required source bands and apply verified scaling.
            band_arrays = {}
            for band_name in required_bands:
                band_number = band_mapping[band_name]
                raw_band = clipped[band_number - 1]

                raw = np.ma.asarray(raw_band, dtype=np.float32)
                raw_data = np.asarray(raw.filled(np.nan), dtype=np.float32)

                scale, offset = _get_scaling(
                    dataset, band_name, band_number
                )
                scaled = raw_data * scale + offset
                scaled[np.ma.getmaskarray(raw)] = np.nan

                manifest = dataset.get("manifest") or {}
                nodata = dataset.get(
                    "nodata", manifest.get("nodata", src.nodata)
                )
                if nodata is not None:
                    scaled[raw_data == nodata] = np.nan

                scaled[~np.isfinite(raw_data)] = np.nan
                band_arrays[band_name] = scaled

            result_transform = clipped_transform
            result_crs = src.crs
            pixel_width, pixel_height = src.res

        dataset_series = {"dataset_id": dataset_id}

        for indicator in request.indicators:
            if indicator == "ndvi":
                values = calculate_ndvi(
                    band_arrays["nir"],
                    band_arrays["red"],
                )
                artifact_kind = "ndvi_raster"
                metric_prefix = "ndvi"

            else:
                values = calculate_mndwi(
                    band_arrays["green"],
                    band_arrays["swir"],
                )
                artifact_kind = "mndwi_raster"
                metric_prefix = "mndwi"

            values = np.asarray(values, dtype=np.float32)
            values[~np.isfinite(values)] = np.nan

            stats = calculate_statistics(values)
            all_statistics.setdefault(metric_prefix, []).append(stats)
            dataset_series[f"mean_{metric_prefix}"] = stats["mean"]

            relative_path = (
                Path("rasters")
                / f"{dataset_id}_{indicator}.tif"
            )
            absolute_path = output_dir / relative_path

            save_raster(
                values,
                absolute_path,
                result_transform,
                result_crs,
            )

            artifacts.append(
                ArtifactDescriptor(
                    artifact_id=str(uuid4()),
                    kind=artifact_kind,
                    relative_path=relative_path.as_posix(),
                    dataset_id=dataset_id,
                )
            )

            if indicator == "water":
                threshold = float(
                    request.processing_config.get(
                        "water_threshold", 0.0
                    )
                )
                water_mask = np.isfinite(values) & (values > threshold)

                pixel_area_m2 = abs(pixel_width * pixel_height)
                area_hectares = (
                    int(np.count_nonzero(water_mask))
                    * pixel_area_m2
                    / 10000.0
                )

                dataset_series["water_area_hectares"] = float(
                    area_hectares
                )
                dataset_series["water_threshold"] = threshold

        valid_fractions = [
            calculate_valid_fraction(values)
            for values in band_arrays.values()
        ]

        dataset_series["valid_pixel_fraction"] = (
            min(valid_fractions) if valid_fractions else 0.0
        )
        series.append(dataset_series)

        if progress_callback is not None:
            progress_callback(
                int(100 * (index + 1) / len(request.dataset_specs))
            )

    if not series:
        raise ValueError("No datasets were provided for analysis.")

    metrics = {}
    statistics = {}

    for indicator, stats_list in all_statistics.items():
        statistics[indicator] = stats_list

        valid_means = [
            item["mean"]
            for item in stats_list
            if item["mean"] is not None
        ]
        metrics[f"mean_{indicator}"] = (
            float(np.mean(valid_means)) if valid_means else None
        )

    comparisons = []

    for previous, current in zip(series, series[1:]):
        comparison = {
            "from_dataset": previous["dataset_id"],
            "to_dataset": current["dataset_id"],
            "indicators": {},
        }

        for indicator in request.indicators:
            metric_name = (
                "mean_ndvi" if indicator == "ndvi"
                else "mean_mndwi"
            )
            comparison["indicators"][metric_name] = calculate_change(
                previous.get(metric_name),
                current.get(metric_name),
            )

        if (
            "water_area_hectares" in previous
            and "water_area_hectares" in current
        ):
            comparison["indicators"]["water_area_hectares"] = calculate_change(
                previous["water_area_hectares"],
                current["water_area_hectares"],
            )
        comparisons.append(comparison)

    quality = {
        "datasets_processed": len(series),
        "valid_pixel_fraction_by_dataset": {
            item["dataset_id"]: item["valid_pixel_fraction"]
            for item in series
        },
    }

    return GeospatialResult(
        metrics=metrics,
        series=series,
        comparisons=comparisons,
        quality=quality,
        warnings=warnings,
        provenance={
            "analysis_id": request.analysis_id,
            "dataset_ids": dataset_ids,
            "indicators_calculated": request.indicators,
            "water_index": "MNDWI",
            "water_threshold": float(
                request.processing_config.get("water_threshold", 0.0)
            ),
            "statistics": statistics,
        },
        artifacts=artifacts,
    )