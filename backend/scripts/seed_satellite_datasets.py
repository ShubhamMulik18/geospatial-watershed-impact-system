import hashlib
import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rasterio

from app.db.session import SessionLocal
from app.models.dataset import Dataset

DATASET_CONFIGS = [
    {
        "id": uuid.UUID("20200000-0000-0000-0000-000000002020"),
        "year": 2020,
        "date": date(2020, 10, 31),
        "name": "Sentinel-2 Tile T43QDU (Oct 2020)",
        "dir": Path("sample_data/satellite/2020"),
    },
    {
        "id": uuid.UUID("20230000-0000-0000-0000-000000002023"),
        "year": 2023,
        "date": date(2023, 10, 26),
        "name": "Sentinel-2 Tile T43QDU (Oct 2023)",
        "dir": Path("sample_data/satellite/2023"),
    },
    {
        "id": uuid.UUID("20260000-0000-0000-0000-000000002026"),
        "year": 2026,
        "date": date(2026, 10, 20),
        "name": "Sentinel-2 Tile T43QDU (Oct 2026)",
        "dir": Path("sample_data/satellite/2026"),
    },
]


def seed_satellite_datasets():
    db = SessionLocal()
    try:
        for cfg in DATASET_CONFIGS:
            existing = db.get(Dataset, cfg["id"])
            if existing:
                existing.capabilities = ["ndvi", "water", "mndwi"]
                db.commit()
                print(f"Dataset {cfg['year']} updated capabilities ({existing.id})")
                continue

            ds_dir = cfg["dir"]
            b04_files = list(ds_dir.glob("*B04*10m*.jp2"))
            if not b04_files:
                raise FileNotFoundError(f"No B04 10m band found in {ds_dir}")
            b04_path = b04_files[0]

            with rasterio.open(b04_path) as src:
                crs = src.crs.to_string() if src.crs else "EPSG:32643"
                transform = {
                    "a": src.transform.a,
                    "b": src.transform.b,
                    "c": src.transform.c,
                    "d": src.transform.d,
                    "e": src.transform.e,
                    "f": src.transform.f,
                }
                res = {"x": float(src.res[0]), "y": float(src.res[1])}
                bounds = {
                    "left": float(src.bounds.left),
                    "bottom": float(src.bounds.bottom),
                    "right": float(src.bounds.right),
                    "top": float(src.bounds.top),
                }

            # Stable SHA256 from folder name and date
            h = hashlib.sha256(f"sentinel2-{cfg['year']}-{cfg['date'].isoformat()}".encode()).hexdigest()

            bands_info = [
                {"name": "B03", "resolution": 10, "description": "Green"},
                {"name": "B04", "resolution": 10, "description": "Red"},
                {"name": "B08", "resolution": 10, "description": "NIR"},
                {"name": "B11", "resolution": 20, "description": "SWIR"},
                {"name": "SCL", "resolution": 20, "description": "Scene Classification"},
            ]

            dataset = Dataset(
                id=cfg["id"],
                display_name=cfg["name"],
                acquisition_date=cfg["date"],
                year=cfg["year"],
                path=str(ds_dir.as_posix()),
                sha256=h,
                crs=crs,
                transform=transform,
                resolution=res,
                bounds=bounds,
                bands=bands_info,
                scale={"B03": 0.0001, "B04": 0.0001, "B08": 0.0001, "B11": 0.0001},
                offset={"B03": 0.0, "B04": 0.0, "B08": 0.0, "B11": 0.0},
                quality_metadata={"source": "Copernicus Sentinel-2 L2A", "cloud_mask": "SCL"},
                capabilities=["ndvi", "water", "mndwi"],
                manifest={
                    "tile": "T43QDU",
                    "source": "Copernicus Open Access Hub",
                    "storage_type": "directory",
                    "bands": ["B03", "B04", "B08", "B11", "SCL"],
                },
            )

            db.add(dataset)
            db.commit()
            print(f"Catalogued dataset {cfg['year']}: {dataset.id} - {dataset.display_name}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_satellite_datasets()
