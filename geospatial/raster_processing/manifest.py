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

    def validate(self) -> None:
        """
        Validate the minimum information required for
        NDVI and water-index processing.
        """

        required_bands = {"red", "nir", "green"}

        missing_bands = required_bands - set(self.bands)

        if missing_bands:
            raise ValueError(
                f"Missing required bands: {sorted(missing_bands)}"
            )

        for band_name in required_bands:
            band_number = self.bands[band_name]

            if not isinstance(band_number, int) or band_number < 1:
                raise ValueError(
                    f"Invalid raster band number for {band_name}: {band_number}"
                )

            if band_name not in self.band_scaling:
                raise ValueError(
                    f"Missing scaling information for band: {band_name}"
                )

            scaling = self.band_scaling[band_name]

            if "scale" not in scaling or "offset" not in scaling:
                raise ValueError(
                    f"Scaling must contain scale and offset for band: {band_name}"
                )

    def to_dict(self) -> dict:
        """
        Convert the manifest into a dictionary.
        """
        return asdict(self)