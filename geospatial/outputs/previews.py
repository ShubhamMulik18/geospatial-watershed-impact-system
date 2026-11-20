from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
import rasterio


def create_raster_preview(
    raster_input: Union[str, Path, np.ndarray],
    output_path: Union[str, Path],
    title: str = "Raster Preview",
    indicator: str = "ndvi",
    water_threshold: float = 0.0,
) -> Path:
    """
    Create a georeferenced RGBA PNG preview with transparent NoData background.

    Uses pure NumPy and Pillow for maximum speed, zero external C-dependencies,
    and exact pixel alignment with map bounds without chart/axis margins.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(raster_input, (str, Path)):
        with rasterio.open(raster_input) as src:
            data = src.read(1, masked=True)
            if np.ma.is_masked(data):
                data = data.filled(np.nan)
            data = np.asarray(data, dtype=np.float32)
    else:
        data = np.asarray(raster_input, dtype=np.float32)
        if data.ndim == 3:
            data = data[0]

    height, width = data.shape
    rgba = np.zeros((height, width, 4), dtype=np.uint8)

    valid_mask = np.isfinite(data)

    if "water" in indicator.lower() or "mndwi" in indicator.lower():
        # Water: blue overlay for detected water
        water_mask = valid_mask & (data > water_threshold)
        rgba[water_mask, 0] = 30
        rgba[water_mask, 1] = 144
        rgba[water_mask, 2] = 255
        rgba[water_mask, 3] = 230  # High opacity blue for surface water

        # Non-water: transparent or subtle neutral tone
        non_water_mask = valid_mask & (~water_mask)
        rgba[non_water_mask, 0] = 180
        rgba[non_water_mask, 1] = 160
        rgba[non_water_mask, 2] = 140
        rgba[non_water_mask, 3] = 30  # Very light wash
    else:
        # NDVI: Red-Yellow-Green continuous gradient
        # Range: -0.2 (bare/water) to 0.8 (dense vegetation)
        valid_vals = data[valid_mask]
        norm = np.clip((valid_vals + 0.2) / 1.0, 0.0, 1.0)

        r = np.zeros_like(norm)
        g = np.zeros_like(norm)
        b = np.full_like(norm, 20.0)

        # First half: Red to Yellow
        first_half = norm < 0.5
        r[first_half] = 220.0
        g[first_half] = 40.0 + 360.0 * norm[first_half]

        # Second half: Yellow to Deep Green
        second_half = ~first_half
        r[second_half] = 220.0 - 360.0 * (norm[second_half] - 0.5)
        g[second_half] = 220.0 - 70.0 * (norm[second_half] - 0.5)

        rgba[valid_mask, 0] = np.clip(r, 0, 255).astype(np.uint8)
        rgba[valid_mask, 1] = np.clip(g, 0, 255).astype(np.uint8)
        rgba[valid_mask, 2] = np.clip(b, 0, 255).astype(np.uint8)
        rgba[valid_mask, 3] = 220  # High opacity

    # NoData / invalid pixels remain alpha = 0 (100% transparent)
    rgba[~valid_mask, 3] = 0

    img = Image.fromarray(rgba, mode="RGBA")
    img.save(output_path, format="PNG")

    return output_path
