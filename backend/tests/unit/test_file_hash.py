from app.utils.file_hash import calculate_sha256


def test_calculate_sha256_returns_expected_digest() -> None:
    assert (
        calculate_sha256(b"hello watershed")
        == "e2177bb51137d549e784802b0d7e3bd261f42d45870f96cc0c24e760f5511c9a"
    )
