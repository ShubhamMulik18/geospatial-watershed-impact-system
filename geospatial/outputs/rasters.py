from pathlib import Path

import numpy as np
import rasterio


def save_raster(
    data,
    output_path,
    transform,
    crs,
    nodata=-9999.0,
):
    """
    Save a single-band raster array as a GeoTIFF.
    """

    data = np.asarray(data, dtype=np.float32)

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_data = np.where(
        np.isfinite(data),
        data,
        nodata,
    ).astype(np.float32)

    height, width = output_data.shape

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(output_data, 1)

    return output_path