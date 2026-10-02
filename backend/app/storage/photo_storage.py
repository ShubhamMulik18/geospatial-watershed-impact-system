from pathlib import Path
import uuid


def generate_photo_path(storage_root: Path, photo_id: uuid.UUID, suffix: str) -> Path:
    """Return a safe generated path for a stored photo."""
    safe_suffix = suffix.lower()

    if not safe_suffix.startswith("."):
        safe_suffix = f".{safe_suffix}"

    filename = f"{photo_id}{safe_suffix}"
    return storage_root / filename