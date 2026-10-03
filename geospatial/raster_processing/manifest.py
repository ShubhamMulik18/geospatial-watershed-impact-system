from dataclasses import dataclass, asdict
from typing import Optional, Any


@dataclass
class DatasetManifest:
    """
    Metadata describing a verified satellite raster dataset.
    """

    acquisition_date: str
    sensor: str
    product: str

    # Semantic band names mapped to one-based raster band indexes.
    # Example: {"red": 4, "nir": 5, "green": 3, "swir": 6}
    bands: dict[str, int]

    # Per-band reflectance scaling.
    # Example: {"red": {"scale": 0.0001, "offset": 0.0}, ...}
    band_scaling: dict[str, dict[str, float]]

    nodata: Optional[float] = None

    # Reference/path plus decoding information for the quality mask.
    quality_mask: Optional[dict[str, Any]] = None

    land_cover_legend: Optional[dict] = None

    source: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert the manifest into a dictionary.
        """
        return asdict(self)