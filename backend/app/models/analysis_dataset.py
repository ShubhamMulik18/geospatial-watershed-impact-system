import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.dataset import Dataset

class AnalysisDataset(Base):
    __tablename__ = "analysis_datasets"

    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "dataset_id",
            name="uq_analysis_datasets_analysis_dataset",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Immutable snapshot of the dataset metadata/hash used by this analysis.
    dataset_metadata_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    dataset_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analysis: Mapped["Analysis"] = relationship(
        back_populates="dataset_links",
    )

    dataset: Mapped["Dataset"] = relationship(
        back_populates="analysis_links",
    )