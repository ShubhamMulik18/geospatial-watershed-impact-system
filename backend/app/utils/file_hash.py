import hashlib
from pathlib import Path


def calculate_sha256(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest for file bytes."""
    return hashlib.sha256(data).hexdigest()


def calculate_file_sha256(path: str | Path) -> str:
    """Return the lowercase SHA-256 digest of a file using bounded memory."""
    digest = hashlib.sha256()

    with Path(path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()
