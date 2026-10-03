from datetime import date
from pathlib import Path
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB
from app.core.config import get_settings
from app.models.dataset import Dataset
from app.storage.dataset_inspection import inspect_dataset
from app.storage.dataset_validation import (
    validate_dataset_filename,
    validate_dataset_size,
)


class DatasetService:
    def __init__(
        self,
        db: Session,
        storage_root: Path | None = None,
        max_size_bytes: int | None = None,
    ) -> None:
        settings = get_settings()

        self.db = db
        self.storage_root = storage_root or Path(settings.dataset_storage_root)
        self.max_size_bytes = (
            max_size_bytes
            if max_size_bytes is not None
            else settings.max_dataset_size_bytes
        )

    def create_dataset(
        self,
        stream,
        original_name: str,
        display_name: str,
        metadata: dict,
    ) -> Dataset:
        suffix = validate_dataset_filename(original_name)

        dataset_id = uuid.uuid4()
        storage_path = self.storage_root / f"{dataset_id}{suffix}"

        self.storage_root.mkdir(parents=True, exist_ok=True)

        try:
            sha256, byte_size = self._store_stream(
                stream=stream,
                storage_path=storage_path,
            )

            validate_dataset_size(byte_size, self.max_size_bytes)

            inspection = inspect_dataset(storage_path)

            acquisition_date = self._resolve_acquisition_date(
                metadata=metadata,
            )

            if acquisition_date is None:
                raise ValueError(
                    "Acquisition date is required in metadata_json."
                )

            year = acquisition_date.year

            manifest = {
                **metadata,
                "original_filename": original_name,
                "byte_size": byte_size,
                "sha256": sha256,
            }

            dataset = Dataset(
                id=dataset_id,
                display_name=display_name,
                acquisition_date=acquisition_date,
                year=year,
                path=str(storage_path),
                sha256=sha256,
                crs=inspection.crs,
                transform=inspection.transform,
                resolution=inspection.resolution,
                bounds=inspection.bounds,
                bands=inspection.bands,
                scale=inspection.scale,
                offset=inspection.offset,
                quality_metadata=None,
                capabilities=metadata.get("capabilities", []),
                manifest=manifest,
            )

            self.db.add(dataset)
            self.db.flush()

            return dataset

        except Exception:
            if storage_path.exists():
                storage_path.unlink()
            raise

    def list_datasets(self, capability: str | None = None) -> list[Dataset]:
        query = self.db.query(Dataset)

        if capability:
            query = query.filter(
                Dataset.capabilities.cast(JSONB).contains([capability])
            )

        return query.order_by(
            Dataset.acquisition_date.desc(),
            Dataset.created_at.desc(),
        ).all()

    def _store_stream(self, stream, storage_path: Path) -> tuple[str, int]:
        import hashlib

        digest = hashlib.sha256()
        byte_size = 0

        with storage_path.open("wb") as destination:
            while chunk := stream.read(1024 * 1024):
                destination.write(chunk)
                digest.update(chunk)
                byte_size += len(chunk)

        return digest.hexdigest(), byte_size

    @staticmethod
    def _resolve_acquisition_date(metadata: dict) -> date | None:
        value = metadata.get("acquisition_date")

        if not value:
            return None

        if isinstance(value, date):
            return value

        return date.fromisoformat(str(value))