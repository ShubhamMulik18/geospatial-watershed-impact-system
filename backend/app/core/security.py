import hashlib
import re
import secrets

# Standard OWASP-recommended parameters for scrypt
SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 67108864  # 64 MB


def hash_password(password: str) -> str:
    """
    Securely hash a password using the memory-hard scrypt algorithm
    with a cryptographically random 16-byte salt.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
    )
    return f"$scrypt$n={SCRYPT_N},r={SCRYPT_R},p={SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored scrypt hash using
    constant-time comparison.
    """
    if not plain_password or not hashed_password:
        return False

    pattern = r"^\$scrypt\$n=(\d+),r=(\d+),p=(\d+)\$([0-9a-fA-F]+)\$([0-9a-fA-F]+)$"
    match = re.match(pattern, hashed_password)
    if not match:
        return False

    try:
        n = int(match.group(1))
        r = int(match.group(2))
        p = int(match.group(3))
        salt = bytes.fromhex(match.group(4))
        expected_hash = bytes.fromhex(match.group(5))

        derived = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=SCRYPT_MAXMEM,
        )
        return secrets.compare_digest(derived, expected_hash)
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate a high-entropy cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash a session token using SHA-256 for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

