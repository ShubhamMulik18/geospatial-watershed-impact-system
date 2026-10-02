import hashlib


def calculate_sha256(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest for file bytes."""
    return hashlib.sha256(data).hexdigest()
