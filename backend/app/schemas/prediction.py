from pydantic import Field

from .common import Confidence, SchemaBase


class PredictionResponse(SchemaBase):
    """Canonical public prediction response."""

    prediction_id: str = Field(min_length=1)
    photo_id: str = Field(min_length=1)
    class_id: str = Field(min_length=1)
    predicted_class: str = Field(min_length=1)
    confidence: Confidence
    requires_verification: bool
    model_version: str = Field(min_length=1)