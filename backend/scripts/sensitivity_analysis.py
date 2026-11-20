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
print("MNDWI THRESHOLD SENSITIVITY ANALYSIS")
print("=" * 80)

thresholds = [-0.20, -0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15, 0.20]

for year in years:
    ds_dir = Path(f"sample_data/satellite/{year}")
    b03 = list(ds_dir.glob("*B03*"))[0]
    b04 = list(ds_dir.glob("*B04*"))[0]
    b11 = list(ds_dir.glob("*B11*"))[0]
    scl = list(ds_dir.glob("*SCL*"))[0]

    with rasterio.open(b04) as src4:
        poly_geom = transform_geom("EPSG:4326", src4.crs, polygon)
        ref_clipped, ref_transform = mask(
            src4, [poly_geom], crop=True, filled=False, indexes=1
        )
        ref_shape = ref_clipped.shape
        ref_mask = np.ma.getmaskarray(ref_clipped)

    def read_clean_band(p, is_scl=False):
        with rasterio.open(p) as src:
            clipped, c_tf = mask(src, [poly_geom], crop=True, filled=False, indexes=1)
            raw = clipped.data if hasattr(clipped, "data") else np.asarray(clipped)
            if raw.shape != ref_shape or src.crs != src4.crs:
                dest = np.zeros(ref_shape, dtype=raw.dtype)
                reproject(
                    source=raw,
                    destination=dest,
                    src_transform=c_tf,
                    src_crs=src.crs,
                    dst_transform=ref_transform,
                    dst_crs=src4.crs,
                    resampling=Resampling.nearest if is_scl else Resampling.bilinear,
                )
                raw = dest
            return raw

    g = read_clean_band(b03).astype(float) * 0.0001
    swir = read_clean_band(b11).astype(float) * 0.0001
    scl_arr = read_clean_band(scl, is_scl=True)

    denom = g + swir
    mndwi = np.full_like(denom, np.nan)
    valid_denom = denom > 1e-6
    mndwi[valid_denom] = (g[valid_denom] - swir[valid_denom]) / denom[valid_denom]

    # Mask outside polygon
    mndwi[ref_mask] = np.nan

    # Valid SCL
    scl_valid = np.isin(scl_arr, [4, 5, 6, 7]) & (~ref_mask)

    mndwi_valid = mndwi[scl_valid]

    print(f"\n--- YEAR {year} (Total Valid Pixels = {mndwi_valid.size}) ---")
    print(f"MNDWI Distribution: min={np.min(mndwi_valid):.4f}, 5%={np.percentile(mndwi_valid, 5):.4f}, 50%={np.median(mndwi_valid):.4f}, mean={np.mean(mndwi_valid):.4f}, 95%={np.percentile(mndwi_valid, 95):.4f}, max={np.max(mndwi_valid):.4f}")

    print("Threshold Sensitivity:")
    for t in thresholds:
        px = np.count_nonzero(mndwi_valid > t)
        ha = px * 0.01
        pct = px / mndwi_valid.size * 100
        print(f"  MNDWI > {t:+5.2f} : {px:5d} px  ({ha:5.2f} ha)  ({pct:5.2f}% of valid AOI)")

