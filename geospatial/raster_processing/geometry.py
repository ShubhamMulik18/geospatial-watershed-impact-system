from shapely.geometry import shape
from shapely.ops import transform
from pyproj import CRS, Transformer


def polygon_from_geojson(geojson: dict):
    """
    Convert a GeoJSON geometry dictionary into a Shapely geometry.
    """
    return shape(geojson)


def validate_geometry(geometry) -> None:
    """
    Validate a Shapely geometry.
    """
    if geometry.is_empty:
        raise ValueError("Geometry is empty.")

    if not geometry.is_valid:
        raise ValueError("Geometry is invalid.")


def validate_crs(crs) -> CRS:
    """
    Validate and return a CRS object.
    """
    try:
        return CRS.from_user_input(crs)
    except Exception as exc:
        raise ValueError(f"Invalid CRS: {crs}") from exc


def get_epsg_code(crs) -> int | None:
    """
    Return the EPSG code of a CRS when available.
    """
    crs_obj = CRS.from_user_input(crs)
    return crs_obj.to_epsg()


def transform_geometry(geometry, source_crs, target_crs):
    """
    Transform a geometry from one CRS to another.
    """
    transformer = Transformer.from_crs(
        source_crs,
        target_crs,
        always_xy=True,
    )

    return transform(transformer.transform, geometry)


def geometry_intersects(first_geometry, second_geometry) -> bool:
    """
    Check whether two geometries intersect.
    """
    return first_geometry.intersects(second_geometry)