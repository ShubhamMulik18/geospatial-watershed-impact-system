import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.photo import Photo


class Prediction(Base):
    __tablename__ = "predictions"

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

    model_version: Mapped[str] = mapped_column(String(128), nullable=False)
    model_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    class_id: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top_candidate_class_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    review_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
        back_populates="predictions",
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="prediction",
    )