import io

from app.utils.stream_hash import calculate_stream_sha256


def test_calculate_stream_sha256_returns_hash_and_size():
    data = b"watershed raster test data"

    digest, byte_size = calculate_stream_sha256(io.BytesIO(data))

    assert digest == "be9463ad98ae56a04fa70f4fa7c7946c87393a7e317fd550cc87b99de08deffd"
    assert byte_size == len(data)