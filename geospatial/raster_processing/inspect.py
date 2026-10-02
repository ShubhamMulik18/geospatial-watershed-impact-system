from pathlib import Path

import rasterio


def inspect_dataset(dataset_path: str | Path) -> dict:
    """
    Inspect a raster dataset and return important metadata.
    """

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Raster dataset not found: {dataset_path}")

    with rasterio.open(dataset_path) as src:
        return {
            "path": str(dataset_path),
            "driver": src.driver,
            "width": src.width,
            "height": src.height,
            "band_count": src.count,
            "crs": src.crs.to_string() if src.crs else None,
            "resolution": src.res,
            "bounds": {
                "left": src.bounds.left,
                "bottom": src.bounds.bottom,
                "right": src.bounds.right,
                "top": src.bounds.top,
            },
            "nodata": src.nodata,
            "dtype": src.dtypes,
        }