"""Geospatial processing package for watershed impact analysis."""

import os
from pathlib import Path

try:
    import rasterio

    _proj_data = Path(rasterio.__file__).parent / "proj_data"
    if _proj_data.is_dir():
        _current = os.environ.get("PROJ_LIB", "")
        if not _current or "PostgreSQL" in _current or not Path(_current).is_dir():
            os.environ["PROJ_LIB"] = str(_proj_data)
except Exception:
    pass

__version__ = "0.1.0"

