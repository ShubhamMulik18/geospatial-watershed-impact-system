import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
if TYPE_CHECKING:
    from app.models.analysis_dataset import AnalysisDataset

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    crs: Mapped[str] = mapped_column(String(128), nullable=False)
    transform: Mapped[dict] = mapped_column(JSON, nullable=False)
    resolution: Mapped[dict] = mapped_column(JSON, nullable=False)
    bounds: Mapped[dict] = mapped_column(JSON, nullable=False)
    bands: Mapped[list] = mapped_column(JSON, nullable=False)
    scale: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    offset: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    quality_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    capabilities: Mapped[list] = mapped_column(JSON, nullable=False)
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False)

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

    analysis_links: Mapped[list["AnalysisDataset"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )