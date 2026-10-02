from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DatasetManifest:
    """
    Metadata describing a satellite raster dataset.
    """

    acquisition_date: str
    sensor: str
    product: str

    bands: dict

    scale: float = 1.0
    offset: float = 0.0

    nodata: Optional[float] = None
    quality_mask: Optional[str] = None

    land_cover_legend: Optional[dict] = None

    source: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert the manifest into a dictionary.
        """
        return asdict(self)