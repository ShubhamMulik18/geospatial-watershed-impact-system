import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
if TYPE_CHECKING:
    from app.models.analysis_dataset import AnalysisDataset
    from app.models.analysis_result import AnalysisResult
    from app.models.analysis_warning import AnalysisWarning
    from app.models.artifact import Artifact
    from app.models.photo import Photo
    from app.models.prediction import Prediction

class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Immutable snapshot of the prediction used for this analysis.
    prediction_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    polygon: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="POLYGON",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )

    indicators: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    client_request_key: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        unique=True,
    )

    worker_lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    worker_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    photo: Mapped["Photo"] = relationship(
        back_populates="analyses",
    )

    prediction: Mapped["Prediction"] = relationship(
        back_populates="analyses",
    )

    dataset_links: Mapped[list["AnalysisDataset"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    result: Mapped["AnalysisResult | None"] = relationship(
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )

    warnings: Mapped[list["AnalysisWarning"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )