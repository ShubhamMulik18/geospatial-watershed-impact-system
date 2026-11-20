import pytest

from starlette.requests import Request

from app.core.auth import get_token_from_request
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)


def test_hash_password_generates_valid_scrypt_format() -> None:
    password = "SuperSecretPassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Scrypt format: $scrypt$n=...,r=...,p=...$<salt>$<hash>
    assert hash1.startswith("$scrypt$n=16384,r=8,p=1$")
    assert hash2.startswith("$scrypt$n=16384,r=8,p=1$")
    # Different salts must yield different hashes
    assert hash1 != hash2


def test_verify_password_matches_correct_password() -> None:
    password = "CorrectHorseBatteryStaple"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_verify_password_handles_corrupted_hash_safely() -> None:
    assert verify_password("test", "not_a_valid_hash") is False
    assert verify_password("test", "$scrypt$n=invalid$salt$hash") is False
    assert verify_password("test", "$scrypt$n=16384,r=8,p=1$deadbeef$1234") is False


def test_hash_password_rejects_empty_password() -> None:
    with pytest.raises(ValueError):
        hash_password("")


def test_session_token_generation_and_hashing() -> None:
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert isinstance(token1, str)
    assert len(token1) >= 32
    assert token1 != token2

    # Hashing should be deterministic
    h1 = hash_session_token(token1)
    h2 = hash_session_token(token1)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex length


def test_get_token_from_request_bearer() -> None:
    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer test-bearer-token")],
        "query_string": b"",
    }
    req = Request(scope)
    assert get_token_from_request(req) == "test-bearer-token"


def test_get_token_from_request_cookie() -> None:
    scope = {
        "type": "http",
        "headers": [(b"cookie", b"watershed_session=test-cookie-token")],
        "query_string": b"",
    }
    req = Request(scope)
    assert get_token_from_request(req) == "test-cookie-token"


def test_get_token_from_request_query_param() -> None:
    scope = {
        "type": "http",
        "headers": [],
        "query_string": b"token=test-query-token",
    }
    req = Request(scope)
    assert get_token_from_request(req) == "test-query-token"


def test_get_token_from_request_empty_returns_none() -> None:
    scope = {
        "type": "http",
        "headers": [],
        "query_string": b"",
    }
    req = Request(scope)
    assert get_token_from_request(req) is None

    # Empty token param
    scope_empty = {
        "type": "http",
        "headers": [],
        "query_string": b"token=",
    }
    assert get_token_from_request(Request(scope_empty)) is None


