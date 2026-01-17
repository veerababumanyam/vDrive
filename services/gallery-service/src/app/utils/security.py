"""Security utilities - password and PIN hashing with Argon2id"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.app.core.config import settings

# Argon2id password hasher with OWASP recommended parameters
password_hasher = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64 MB memory
    parallelism=4,  # 4 parallel threads
    hash_len=32,  # 32-byte hash
    salt_len=16,  # 16-byte salt
)


def hash_password(password: str) -> str:
    """
    Hash password using Argon2id.

    Args:
        password: Plain text password or PIN

    Returns:
        Argon2id hash string
    """
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify password against Argon2id hash.

    Args:
        password_hash: Argon2id hash from database
        password: Plain text password to verify

    Returns:
        True if password matches hash, False otherwise
    """
    try:
        password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def hash_pin(pin: str) -> str:
    """
    Hash PIN using Argon2id (same as password).

    Args:
        pin: 4-6 digit PIN

    Returns:
        Argon2id hash string
    """
    return hash_password(pin)


def verify_pin(pin_hash: str, pin: str) -> bool:
    """
    Verify PIN against Argon2id hash.

    Args:
        pin_hash: Argon2id hash from database
        pin: Plain text PIN to verify

    Returns:
        True if PIN matches hash, False otherwise
    """
    return verify_password(pin_hash, pin)
