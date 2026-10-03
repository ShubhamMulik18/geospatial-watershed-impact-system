from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import rasterio
from rasterio.warp import transform_bounds


@dataclass(frozen=True)
class DatasetInspection:
    crs: str
    transform: dict[str, float]
    resolution: dict[str, float]
    bounds: dict[str, float]
    bounds_wgs84: dict[str, float]
    bands: list[dict[str, Any]]
    scale: dict[str, float]
    offset: dict[str, float]
    width: int
    height: int
    count: int
    nodata: float | int | None
    acquisition_date: date | None


def inspect_dataset(path: Path) -> DatasetInspection:
    with rasterio.open(path) as src:
        crs = src.crs
        if crs is None:
            raise ValueError("Dataset CRS is missing.")

        bounds = src.bounds

        wgs84_left, wgs84_bottom, wgs84_right, wgs84_top = transform_bounds(
            crs,
            "EPSG:4326",
            bounds.left,
            bounds.bottom,
            bounds.right,
            bounds.top,
        )

        bands: list[dict[str, Any]] = []
        for band_index in range(1, src.count + 1):
            bands.append(
                {
                    "index": band_index,
                    "dtype": src.dtypes[band_index - 1],
                    "nodata": src.nodatavals[band_index - 1],
                }
            )

        return DatasetInspection(
            crs=crs.to_string(),
            transform={
                "a": src.transform.a,
                "b": src.transform.b,
                "c": src.transform.c,
                "d": src.transform.d,
                "e": src.transform.e,
                "f": src.transform.f,
            },
            resolution={
                "x": float(src.res[0]),
                "y": float(src.res[1]),
            },
            bounds={
                "left": float(bounds.left),
                "bottom": float(bounds.bottom),
                "right": float(bounds.right),
                "top": float(bounds.top),
            },
            bounds_wgs84={
                "left": float(wgs84_left),
                "bottom": float(wgs84_bottom),
                "right": float(wgs84_right),
                "top": float(wgs84_top),
            },
            bands=bands,
            scale={
                str(index): float(value)
                for index, value in enumerate(src.scales, start=1)
            },
            offset={
                str(index): float(value)
                for index, value in enumerate(src.offsets, start=1)
            },
            width=src.width,
            height=src.height,
            count=src.count,
            nodata=src.nodata,
            acquisition_date=None,
        )