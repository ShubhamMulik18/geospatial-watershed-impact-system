import os
import sys
from pathlib import Path

proj_data = Path(__file__).resolve().parent.parent / ".venv" / "Lib" / "site-packages" / "rasterio" / "proj_data"
os.environ["PROJ_LIB"] = str(proj_data)
os.environ["PROJ_DATA"] = str(proj_data)

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import Resampling, reproject, transform_geom

polygon = {
    "type": "Polygon",
    "coordinates": [
        [
            [74.24, 16.70],
            [74.25, 16.70],
            [74.25, 16.71],
            [74.24, 16.71],
            [74.24, 16.70],
        ]
    ],
}

years = [2020, 2023, 2026]

print("=" * 80)
print("SCL CLASS BREAKDOWN INSIDE STUDY AREA POLYGON")
print("=" * 80)

class_names = {
    0: "NO_DATA",
    1: "SATURATED_OR_DEFECTIVE",
    2: "DARK_AREA_PIXELS",
    3: "CLOUD_SHADOWS",
    4: "VEGETATION",
    5: "NOT_VEGETATED",
    6: "WATER",
    7: "UNCLASSIFIED",
    8: "CLOUD_MEDIUM_PROB",
    9: "CLOUD_HIGH_PROB",
    10: "THIN_CIRRUS",
    11: "SNOW",
}

for year in years:
    ds_dir = Path(f"sample_data/satellite/{year}")
    b04 = list(ds_dir.glob("*B04*"))[0]
    scl = list(ds_dir.glob("*SCL*"))[0]

    with rasterio.open(b04) as src4:
        poly_geom = transform_geom("EPSG:4326", src4.crs, polygon)
        ref_clipped, ref_transform = mask(
            src4, [poly_geom], crop=True, filled=False, indexes=1
        )
        ref_shape = ref_clipped.shape
        ref_mask = np.ma.getmaskarray(ref_clipped)

    with rasterio.open(scl) as src_scl:
        clipped_scl, c_tf = mask(
            src_scl, [poly_geom], crop=True, filled=False, indexes=1
        )
        scl_source = (
            clipped_scl.data
            if hasattr(clipped_scl, "data")
            else np.asarray(clipped_scl)
        )
        dest_scl = np.zeros(ref_shape, dtype=clipped_scl.dtype)
        reproject(
            source=scl_source,
            destination=dest_scl,
            src_transform=c_tf,
            src_crs=src_scl.crs,
            dst_transform=ref_transform,
            dst_crs=src4.crs,
            resampling=Resampling.nearest,
        )

    inside_scl = dest_scl[~ref_mask]
    print(f"\n--- YEAR {year} ---")
    print(f"BBox total pixels: {dest_scl.size} (Shape: {dest_scl.shape[1]}W x {dest_scl.shape[0]}H)")
    print(f"Inside polygon:    {inside_scl.size} pixels ({inside_scl.size * 0.01:.2f} ha)")
    print(f"Outside polygon:   {np.count_nonzero(ref_mask)} pixels ({np.count_nonzero(ref_mask) * 0.01:.2f} ha)")

    classes, counts = np.unique(inside_scl, return_counts=True)
    for c, cnt in zip(classes, counts):
        pct = cnt / inside_scl.size * 100
        print(f"  Class {c:2d} ({class_names.get(c, 'UNKNOWN'):22s}): {cnt:5d} px ({pct:5.2f}%)")

