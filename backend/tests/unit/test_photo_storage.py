from pathlib import Path
import uuid

from app.storage.photo_storage import generate_photo_path


def test_generate_photo_path_uses_photo_id_and_safe_suffix() -> None:
    photo_id = uuid.UUID("12345678-1234-5678-1234-567812345678")

    path = generate_photo_path(Path("uploads/photos"), photo_id, ".JPG")

    assert path == Path("uploads/photos/12345678-1234-5678-1234-567812345678.jpg")
    assert path.name != "original.jpg"