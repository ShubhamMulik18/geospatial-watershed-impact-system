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
    bands: dict[str, int]

    # Per-band reflectance scaling.
    # Sentinel-2 L2A:
    # Reflectance = DN * 0.0001 - 0.1
    band_scaling: dict[str, dict[str, float]]

    nodata: Optional[float] = None

    # Quality-mask reference and decoding information.
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

        # MNDWI requires SWIR.
        if "swir" in self.bands:
            if "swir" not in self.band_scaling:
                raise ValueError(
                    "Missing scaling information for band: swir"
                )

            scaling = self.band_scaling["swir"]

            if "scale" not in scaling or "offset" not in scaling:
                raise ValueError(
                    "Scaling must contain scale and offset for band: swir"
                )

        # Validate quality-mask definition when provided.
        if self.quality_mask is not None:
            valid_classes = self.quality_mask.get("valid_classes")

            if valid_classes is not None:
                if not isinstance(valid_classes, list):
                    raise ValueError(
                        "quality_mask valid_classes must be a list."
                    )

                if not all(
                    isinstance(value, int) and value >= 0
                    for value in valid_classes
                ):
                    raise ValueError(
                        "quality_mask valid_classes must contain "
                        "non-negative integers."
                    )

    def to_dict(self) -> dict:
        """
        Convert the manifest into a dictionary.
        """
        return asdict(self)