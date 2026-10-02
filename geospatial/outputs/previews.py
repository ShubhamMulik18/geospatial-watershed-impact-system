from pathlib import Path

import matplotlib.pyplot as plt
import rasterio


def create_raster_preview(
    raster_path,
    output_path,
    title="Raster Preview",
):
    """
    Create a PNG preview image from a single-band raster.
    """

    raster_path = Path(raster_path)
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with rasterio.open(raster_path) as src:
        data = src.read(1)

    plt.figure(figsize=(8, 6))
    plt.imshow(data)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    return output_path