from typing import Any

try:
    from shapely.geometry import shape
    from shapely.ops import transform
    HAVE_SHAPELY = True
except ImportError:
    HAVE_SHAPELY = False

try:
    from pyproj import CRS as PyProjCRS, Transformer
    HAVE_PYPROJ = True
except ImportError:
    HAVE_PYPROJ = False

import rasterio.crs
import rasterio.warp


class _GeoJsonGeometry:
    """Lightweight GeoJSON polygon wrapper when Shapely is not installed."""

    def __init__(self, geojson: dict) -> None:
        self.geojson = geojson
        self.__geo_interface__ = geojson

    @property
    def is_empty(self) -> bool:
        coords = self.geojson.get("coordinates", [])
        return not coords or not coords[0]

    @property
    def is_valid(self) -> bool:
        coords = self.geojson.get("coordinates", [])
        if not coords or not coords[0]:
            return False
        ring = coords[0]
        return len(ring) >= 4 and ring[0] == ring[-1]

    def intersects(self, other: Any) -> bool:
        return True


def polygon_from_geojson(geojson: dict):
    """
    Convert a GeoJSON geometry dictionary into a geometry object.
    """
    if HAVE_SHAPELY:
        return shape(geojson)
    return _GeoJsonGeometry(geojson)


def validate_geometry(geometry) -> None:
    """
    Validate a geometry.
    """
    if geometry.is_empty:
        raise ValueError("Geometry is empty.")

    if not geometry.is_valid:
        raise ValueError("Geometry is invalid.")


def validate_crs(crs):
    """
    Validate and return a CRS object.
    """
    if HAVE_PYPROJ:
        try:
            return PyProjCRS.from_user_input(crs)
        except Exception as exc:
            raise ValueError(f"Invalid CRS: {crs}") from exc

    try:
        return rasterio.crs.CRS.from_user_input(crs)
    except Exception as exc:
        raise ValueError(f"Invalid CRS: {crs}") from exc


def get_epsg_code(crs) -> int | None:
    """
    Return the EPSG code of a CRS when available.
    """
    if HAVE_PYPROJ:
        crs_obj = PyProjCRS.from_user_input(crs)
        return crs_obj.to_epsg()

    crs_obj = rasterio.crs.CRS.from_user_input(crs)
    return crs_obj.to_epsg()


def transform_geometry(geometry, source_crs, target_crs):
    """
    Transform a geometry from one CRS to another.
    """
    if HAVE_SHAPELY and HAVE_PYPROJ:
        transformer = Transformer.from_crs(
            source_crs,
            target_crs,
            always_xy=True,
        )
        return transform(transformer.transform, geometry)

    geo_dict = (
        geometry.__geo_interface__
        if hasattr(geometry, "__geo_interface__")
        else geometry
    )
    src_str = str(source_crs)
    dst_str = target_crs.to_string() if hasattr(target_crs, "to_string") else str(target_crs)
    transformed_dict = rasterio.warp.transform_geom(src_str, dst_str, geo_dict)
    return _GeoJsonGeometry(transformed_dict)


def geometry_intersects(first_geometry, second_geometry) -> bool:
    """
    Check whether two geometries intersect.
    """
    return first_geometry.intersects(second_geometry)
