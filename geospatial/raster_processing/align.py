import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.enums import Resampling


def align_raster(
    source_path,
    output_shape,
    output_transform,
    output_crs,
    resampling=Resampling.bilinear,
):
    """
    Reproject and align a raster to a common grid.
    """

    with rasterio.open(source_path) as src:
        source = src.read(1)

        destination = np.empty(
            output_shape,
            dtype=source.dtype,
        )

        reproject(
            source=source,
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=output_transform,
            dst_crs=output_crs,
            resampling=resampling,
        )

    return destination