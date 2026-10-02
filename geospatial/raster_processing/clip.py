from pathlib import Path

import rasterio
from rasterio.mask import mask


def clip_raster(
    raster_path: str | Path,
    geometry,
    output_path: str | Path,
) -> Path:
    """
    Clip a raster using a Shapely geometry.
    """
    raster_path = Path(raster_path)
    output_path = Path(output_path)

    with rasterio.open(raster_path) as src:
        clipped, transform = mask(
            src,
            [geometry.__geo_interface__],
            crop=True,
        )

        profile = src.profile.copy()
        profile.update(
            height=clipped.shape[1],
            width=clipped.shape[2],
            transform=transform,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(clipped)

    return output_path