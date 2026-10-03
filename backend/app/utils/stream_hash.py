import hashlib
from typing import BinaryIO


DEFAULT_CHUNK_SIZE = 1024 * 1024


def calculate_stream_sha256(
    stream: BinaryIO,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[str, int]:
    """Calculate SHA-256 and byte size while reading a binary stream."""
    digest = hashlib.sha256()
    byte_size = 0

    while chunk := stream.read(chunk_size):
        digest.update(chunk)
        byte_size += len(chunk)

    return digest.hexdigest(), byte_size