import math

from rasterio.transform import from_origin


def create_grid_transform(
    min_x: float,
    max_y: float,
    resolution: float,
):
    """
    Create an affine transform for a regular raster grid.
    """
    return from_origin(
        min_x,
        max_y,
        resolution,
        resolution,
    )


def calculate_grid_shape(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    resolution: float,
) -> tuple[int, int]:
    """
    Calculate the number of rows and columns for a regular grid.
    """
    if resolution <= 0:
        raise ValueError("Resolution must be greater than zero.")

    width = math.ceil((max_x - min_x) / resolution)
    height = math.ceil((max_y - min_y) / resolution)

    return height, width
def calculate_grid_bounds(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
) -> tuple[float, float, float, float]:
    """
    Return grid bounds as (min_x, min_y, max_x, max_y).
    """
    return min_x, min_y, max_x, max_y
def validate_resolution(resolution: float) -> float:
    """
    Validate and return a positive grid resolution.
    """
    if resolution <= 0:
        raise ValueError("Resolution must be greater than zero.")

    return resolution
def build_grid(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    resolution: float,
) -> dict:
    """
    Build basic information for a regular raster grid.
    """
    resolution = validate_resolution(resolution)

    height, width = calculate_grid_shape(
        min_x,
        min_y,
        max_x,
        max_y,
        resolution,
    )

    transform = create_grid_transform(
        min_x,
        max_y,
        resolution,
    )

    bounds = calculate_grid_bounds(
        min_x,
        min_y,
        max_x,
        max_y,
    )

    return {
        "width": width,
        "height": height,
        "resolution": resolution,
        "bounds": bounds,
        "transform": transform,
    }
