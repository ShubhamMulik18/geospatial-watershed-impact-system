from app.utils.file_hash import calculate_sha256, calculate_file_sha256


def test_calculate_sha256_returns_expected_digest() -> None:
    assert (
        calculate_sha256(b"hello watershed")
        == "e2177bb51137d549e784802b0d7e3bd261f42d45870f96cc0c24e760f5511c9a"
    )


def test_calculate_file_sha256_returns_expected_digest(tmp_path) -> None:
    file_path = tmp_path / "sample.tif"
    content = b"hello watershed"
    file_path.write_bytes(content)

    assert calculate_file_sha256(file_path) == calculate_sha256(content)
