from datetime import date, datetime, timezone
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.warp import reproject, transform_geom

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
from geospatial.outputs.previews import create_raster_preview


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
    if not raster_path.is_absolute() and not raster_path.exists():
        repo_root = Path(__file__).resolve().parent.parent
        if (repo_root / raster_path).exists():
            raster_path = repo_root / raster_path

    if not raster_path.exists():
        raise FileNotFoundError(
            f"Raster file or directory does not exist: {raster_path}"
        )
    return raster_path


def _get_band_mapping(dataset):
    bands = dataset.get("bands")
    manifest = dataset.get("manifest")

    if not bands and isinstance(manifest, dict):
        bands = manifest.get("bands")

    if isinstance(bands, dict):
        return bands

    # If dataset path is a directory of separate band files (e.g. Sentinel-2 JP2 files)
    raster_path = Path(
        dataset.get("path")
        or dataset.get("raster_path")
        or dataset.get("resolved_path")
        or ""
    )
    if not raster_path.is_absolute() and not raster_path.exists():
        repo_root = Path(__file__).resolve().parent.parent
        if (repo_root / raster_path).exists():
            raster_path = repo_root / raster_path

    if raster_path.is_dir():
        mapping = {}
        for file in raster_path.iterdir():
            name = file.name.upper()
            if "_B04" in name or "_RED" in name:
                mapping["red"] = str(file)
            elif "_B08" in name or "_NIR" in name:
                mapping["nir"] = str(file)
            elif "_B03" in name or "_GREEN" in name:
                mapping["green"] = str(file)
            elif "_B11" in name or "_SWIR" in name:
                mapping["swir"] = str(file)
            elif "_SCL" in name or "_MASK" in name:
                mapping["scl"] = str(file)
        if mapping:
            return mapping

    raise ValueError(
        "Dataset must provide semantic band mappings, "
        "for example {'red': 4, 'nir': 5} or directory containing band files."
    )


def _get_scaling(dataset, band_name, band_number=None):
    """Return verified scale and offset; use Sentinel-2 L2A standards if unconfigured."""
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

    if scales is not None and offsets is not None:
        scale = (
            scales.get(str(band_number), scales.get(band_number))
            if band_number is not None
            else None
        )
        offset = (
            offsets.get(str(band_number), offsets.get(band_number))
            if band_number is not None
            else None
        )

        if scale is not None and offset is not None:
            return float(scale), float(offset)

    # Sentinel-2 Level-2A surface reflectance defaults: DN * 0.0001
    return 0.0001, 0.0


def _validate_requested_indicators(indicators):
    if not indicators:
        raise ValueError("At least one indicator must be requested.")

    unknown = set(indicators) - SUPPORTED_INDICATORS
    if unknown:
        raise ValueError(
            f"Unsupported indicator(s): {sorted(unknown)}. "
            f"Supported indicators are {sorted(SUPPORTED_INDICATORS)}."
        )


def _extract_dataset_date(dataset: dict[str, Any], index: int = 0) -> date:
    """Extract or parse acquisition date from dataset metadata or filename."""
    meta = dataset.get("metadata") or {}
    for key in ("acquisition_date", "date"):
        val = dataset.get(key) or meta.get(key)
        if val:
            if isinstance(val, date) and not isinstance(val, datetime):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val).date()
                except ValueError:
                    pass

    # Search for YYYYMMDD in string fields
    for name_candidate in (
        str(dataset.get("path") or dataset.get("raster_path") or ""),
        str(dataset.get("dataset_id") or ""),
        str(dataset.get("name") or ""),
        str(dataset.get("display_name") or ""),
    ):
        match = re.search(r"20\d{2}[01]\d[0-3]\d", name_candidate)
        if match:
            raw_str = match.group(0)
            try:
                return datetime.strptime(raw_str, "%Y%m%d").date()
            except ValueError:
                pass

        match_year = re.search(r"(?:^|[^\d])(20\d{2})(?:[^\d]|$)", name_candidate)
        if match_year:
            year = int(match_year.group(1))
            return date(year, 10, 15)

    dataset_id = dataset.get("dataset_id", f"dataset-{index + 1}")
    raise ValueError(
        f"Dataset '{dataset_id}' does not contain a valid or parseable acquisition date."
    )


def _read_band_from_source(
    raster_source: Path,
    polygon_geom: Any,
    ref_shape: tuple[int, int] | None = None,
    ref_transform: Any = None,
    ref_crs: Any = None,
    resampling_method: Resampling = Resampling.bilinear,
    band_number: int = 1,
) -> tuple[np.ndarray, Any, Any, tuple[float, float]]:
    """Clip a band from a raster file and reproject to ref grid if needed."""
    with rasterio.open(raster_source) as src:
        src_crs = src.crs
        if src_crs is None:
            src_crs = rasterio.crs.CRS.from_epsg(32643)

        transformed_poly = transform_geom("EPSG:4326", src_crs, polygon_geom)

        clipped, clipped_transform = mask(
            src,
            [transformed_poly],
            crop=True,
            filled=False,
            indexes=band_number,
        )

        res = src.res

        if (
            ref_shape is not None
            and ref_transform is not None
            and ref_crs is not None
            and (clipped.shape != ref_shape or src_crs != ref_crs)
        ):
            source_data = clipped.data if hasattr(clipped, "data") else np.asarray(clipped)
            dest = np.zeros(ref_shape, dtype=clipped.dtype)
            reproject(
                source=source_data,
                destination=dest,
                src_transform=clipped_transform,
                src_crs=src_crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                resampling=resampling_method,
            )
            return dest, ref_transform, ref_crs, res

        return clipped, clipped_transform, src_crs, res


def run_analysis(request, output_dir, progress_callback=None):
    """
    Calculate requested NDVI and/or MNDWI indicators from raster datasets.
    """
    if not isinstance(request, AnalysisRequest):
        raise TypeError("request must be an AnalysisRequest.")

    _validate_requested_indicators(request.indicators)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    polygon_dict = request.polygon
    geometry = polygon_from_geojson(polygon_dict)
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

    per_dataset_valid_masks = {}
    per_dataset_valid_fractions = {}
    cloud_masks_available = {}

    # Sort dataset specifications chronologically by acquisition date
    decorated = []
    for idx, ds in enumerate(request.dataset_specs):
        acq_date = _extract_dataset_date(ds, idx)
        decorated.append((acq_date, ds))
    decorated.sort(key=lambda item: item[0])
    sorted_dataset_specs = [ds for _, ds in decorated]

    for index, dataset in enumerate(sorted_dataset_specs):
        dataset_id = str(dataset.get("dataset_id", f"dataset-{index + 1}"))
        dataset_ids.append(dataset_id)

        raster_path = _get_raster_path(dataset)
        band_mapping = _get_band_mapping(dataset)

        is_directory_dataset = raster_path.is_dir() or any(
            isinstance(v, str) and (Path(v).is_file() or "/" in v or "\\" in v)
            for v in band_mapping.values()
        )

        band_arrays = {}
        scl_mask = None
        result_transform = None
        result_crs = None
        pixel_width, pixel_height = (10.0, 10.0)

        if is_directory_dataset:
            # 1. Open reference band (preferably Red or Green at 10m)
            ref_band_key = "red" if "red" in band_mapping else list(band_mapping.keys())[0]
            ref_path = Path(band_mapping[ref_band_key])
            if not ref_path.exists() and not ref_path.is_absolute() and raster_path.is_dir():
                ref_path = raster_path / ref_path

            ref_clipped, ref_transform, ref_crs, (pw, ph) = _read_band_from_source(
                ref_path,
                geometry.__geo_interface__,
            )
            result_transform = ref_transform
            result_crs = ref_crs
            pixel_width, pixel_height = pw, ph
            ref_shape = ref_clipped.shape
            ref_mask = (
                np.ma.getmaskarray(ref_clipped)
                if hasattr(ref_clipped, "mask")
                else np.zeros(ref_shape, dtype=bool)
            )

            # 2. Check for SCL (Scene Classification Layer)
            scl_path = None
            if "scl" in band_mapping:
                scl_path = Path(band_mapping["scl"])
                if not scl_path.exists() and not scl_path.is_absolute() and raster_path.is_dir():
                    scl_path = raster_path / scl_path
            elif raster_path.is_dir():
                found_scl = next(raster_path.glob("*SCL*"), None)
                if found_scl:
                    scl_path = found_scl

            if scl_path and scl_path.exists():
                scl_raw, _, _, _ = _read_band_from_source(
                    scl_path,
                    geometry.__geo_interface__,
                    ref_shape=ref_shape,
                    ref_transform=ref_transform,
                    ref_crs=ref_crs,
                    resampling_method=Resampling.nearest,
                )
                scl_data = (
                    scl_raw.data if hasattr(scl_raw, "data") else np.asarray(scl_raw)
                )
                # SCL valid classes: 4 (vegetation), 5 (not-vegetated), 6 (water), 7 (unclassified)
                scl_mask = np.isin(scl_data, [4, 5, 6, 7])
                cloud_masks_available[dataset_id] = True
            else:
                cloud_masks_available[dataset_id] = False

            # 3. Read and scale each required band
            for band_name in required_bands:
                if band_name not in band_mapping:
                    raise ValueError(
                        f"Dataset '{dataset_id}' is missing required band mapping: '{band_name}'."
                    )
                b_path = Path(band_mapping[band_name])
                if not b_path.exists() and not b_path.is_absolute() and raster_path.is_dir():
                    b_path = raster_path / b_path

                raw_band, _, _, _ = _read_band_from_source(
                    b_path,
                    geometry.__geo_interface__,
                    ref_shape=ref_shape,
                    ref_transform=ref_transform,
                    ref_crs=ref_crs,
                    resampling_method=Resampling.bilinear,
                )

                raw = np.ma.asarray(raw_band, dtype=np.float32)
                raw_data = np.asarray(raw.filled(np.nan), dtype=np.float32)

                scale, offset = _get_scaling(dataset, band_name)
                scaled = raw_data * scale + offset
                scaled[ref_mask] = np.nan
                scaled[np.ma.getmaskarray(raw)] = np.nan
                scaled[~np.isfinite(raw_data)] = np.nan

                if scl_mask is not None:
                    scaled[~scl_mask] = np.nan

                band_arrays[band_name] = scaled

        else:
            # Single multi-band raster file
            with rasterio.open(raster_path) as src:
                src_crs = src.crs or rasterio.crs.CRS.from_epsg(32643)

                raster_geometry = transform_geometry(
                    geometry,
                    "EPSG:4326",
                    src_crs,
                )

                clipped, clipped_transform = mask(
                    src,
                    [raster_geometry.__geo_interface__],
                    crop=True,
                    filled=False,
                )

                result_transform = clipped_transform
                result_crs = src_crs
                pixel_width, pixel_height = src.res

                for band_name in required_bands:
                    band_number = band_mapping[band_name]
                    raw_band = clipped[band_number - 1]

                    raw = np.ma.asarray(raw_band, dtype=np.float32)
                    raw_data = np.asarray(raw.filled(np.nan), dtype=np.float32)

                    scale, offset = _get_scaling(dataset, band_name, band_number)
                    scaled = raw_data * scale + offset
                    scaled[np.ma.getmaskarray(raw)] = np.nan

                    nodata = dataset.get("nodata", src.nodata)
                    if nodata is not None:
                        scaled[raw_data == nodata] = np.nan

                    scaled[~np.isfinite(raw_data)] = np.nan
                    band_arrays[band_name] = scaled

            cloud_masks_available[dataset_id] = False

        # Calculate valid data mask for this dataset
        finite_masks = [np.isfinite(arr) for arr in band_arrays.values()]
        ds_valid_mask = np.logical_and.reduce(finite_masks) if finite_masks else np.array([])
        per_dataset_valid_masks[dataset_id] = ds_valid_mask

        v_frac = float(ds_valid_mask.mean()) if ds_valid_mask.size > 0 else 0.0
        per_dataset_valid_fractions[dataset_id] = v_frac

        acq_date = _extract_dataset_date(dataset, index)
        date_str = acq_date.isoformat() if hasattr(acq_date, "isoformat") else str(acq_date)

        dataset_series = {
            "dataset_id": dataset_id,
            "date": date_str,
            "valid_pixel_fraction": v_frac,
        }

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

            # Store metrics under multiple expected key aliases
            dataset_series[f"mean_{metric_prefix}"] = stats["mean"]
            if indicator == "ndvi":
                dataset_series["ndvi_mean"] = stats["mean"]

            relative_path = Path("rasters") / f"{dataset_id}_{indicator}.tif"
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

            threshold = float(
                request.processing_config.get("water_threshold", 0.0)
            )

            # Generate and register corresponding georeferenced transparent PNG preview
            generate_previews = bool(
                request.processing_config.get("generate_previews", False)
            )
            if generate_previews:
                preview_rel_path = Path("previews") / f"{dataset_id}_{indicator}.png"
                preview_abs_path = output_dir / preview_rel_path

                create_raster_preview(
                    raster_input=values,
                    output_path=preview_abs_path,
                    indicator=indicator,
                    water_threshold=threshold,
                )

                artifacts.append(
                    ArtifactDescriptor(
                        artifact_id=str(uuid4()),
                        kind=f"preview_{indicator}",
                        relative_path=preview_rel_path.as_posix(),
                        dataset_id=dataset_id,
                    )
                )

            if indicator == "water":
                water_mask = np.isfinite(values) & (values > threshold)
                pixel_area_m2 = abs(pixel_width * pixel_height)
                area_hectares = (
                    int(np.count_nonzero(water_mask))
                    * pixel_area_m2
                    / 10000.0
                )
                dataset_series["water_area_hectares"] = float(area_hectares)
                dataset_series["water_hectares"] = float(area_hectares)
                dataset_series["water_threshold"] = threshold

        series.append(dataset_series)

        if progress_callback is not None:
            progress_callback(
                int(100 * (index + 1) / len(request.dataset_specs))
            )

    if not series:
        raise ValueError("No datasets were provided for analysis.")

    # Compute common valid support across all datasets
    if per_dataset_valid_masks:
        first_mask = next(iter(per_dataset_valid_masks.values()))
        common_valid = np.logical_and.reduce(list(per_dataset_valid_masks.values()))
        common_valid_fraction = float(common_valid.mean()) if common_valid.size > 0 else 0.0
        total_aoi_m2 = first_mask.size * abs(pixel_width * pixel_height)
        aoi_hectares = float(total_aoi_m2 / 10000.0)
        common_valid_hectares = float(
            int(np.count_nonzero(common_valid)) * abs(pixel_width * pixel_height) / 10000.0
        )
    else:
        common_valid_fraction = 1.0
        aoi_hectares = 0.0
        common_valid_hectares = 0.0

    # Build public metrics
    metrics: dict[str, Any] = {}
    statistics: dict[str, Any] = {}

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

    # First and last dataset before/after comparisons
    first_series = series[0]
    last_series = series[-1]

    if "mean_ndvi" in first_series and "mean_ndvi" in last_series:
        ndvi_before = first_series["mean_ndvi"]
        ndvi_after = last_series["mean_ndvi"]
        metrics["ndvi_before"] = ndvi_before
        metrics["ndvi_after"] = ndvi_after
        if ndvi_before is not None and ndvi_after is not None:
            metrics["ndvi_change"] = float(ndvi_after - ndvi_before)

    if "water_area_hectares" in first_series and "water_area_hectares" in last_series:
        water_before = first_series["water_area_hectares"]
        water_after = last_series["water_area_hectares"]
        metrics["water_before_hectares"] = water_before
        metrics["water_after_hectares"] = water_after
        if water_before is not None and water_after is not None:
            water_change = float(water_after - water_before)
            metrics["water_change_hectares"] = water_change
            if water_before > 0:
                metrics["water_change_percent"] = float(water_change / water_before * 100.0)
            else:
                metrics["water_change_percent"] = 0.0

    # Pairwise comparisons
    comparisons = []
    for previous, current in zip(series, series[1:]):
        from_id = previous["dataset_id"]
        to_id = current["dataset_id"]

        comp = {
            "from_dataset": from_id,
            "to_dataset": to_id,
            "before_dataset_id": from_id,
            "after_dataset_id": to_id,
            "indicators": {},
        }

        for indicator in request.indicators:
            metric_name = (
                "mean_ndvi" if indicator == "ndvi"
                else "mean_mndwi"
            )
            change = calculate_change(
                previous.get(metric_name),
                current.get(metric_name),
            )
            comp["indicators"][metric_name] = change
            if indicator == "ndvi":
                comp["ndvi_change"] = change.get("absolute_change")

        if (
            "water_area_hectares" in previous
            and "water_area_hectares" in current
        ):
            w_change = calculate_change(
                previous["water_area_hectares"],
                current["water_area_hectares"],
            )
            comp["indicators"]["water_area_hectares"] = w_change
            comp["water_change_hectares"] = w_change.get("absolute_change")
            comp["water_change_percent"] = w_change.get(
                "percentage_change", w_change.get("percent_change")
            )

        comparisons.append(comp)

    quality = {
        "datasets_processed": len(series),
        "aoi_hectares": aoi_hectares,
        "common_valid_hectares": common_valid_hectares,
        "common_valid_fraction": common_valid_fraction,
        "per_dataset_valid_fraction": per_dataset_valid_fractions,
        "cloud_mask_available": cloud_masks_available,
        "comparison_limitations": [],
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
            "target_crs": str(result_crs.to_string()) if result_crs else "EPSG:32643",
            "target_resolution": float(pixel_width),
            "statistics": statistics,
            "pipeline_version": "1.0",
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        artifacts=artifacts,
    )
