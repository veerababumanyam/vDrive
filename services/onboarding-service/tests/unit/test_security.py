"""
Unit tests for security utilities.
"""

import pytest
from freezegun import freeze_time

from src.app.core.security import (
    PasswordValidator,
    compare_tokens,
    create_access_token,
    generate_oauth_state,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for Argon2id password hashing."""

    def test_hash_password_creates_valid_hash(self):
        """Hash should be a valid Argon2id string."""
        password = "SecureP@ss123!"
        hashed = hash_password(password)

        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "SecureP@ss123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "SecureP@ss123!"
        hashed = hash_password(password)

        assert verify_password("WrongP@ss123!", hashed) is False

    def test_verify_password_empty_password(self):
        """Empty password should fail verification."""
        hashed = hash_password("SecureP@ss123!")

        assert verify_password("", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Different passwords should produce different hashes."""
        hash1 = hash_password("Password1!")
        hash2 = hash_password("Password2!")

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (salt)."""
        password = "SecureP@ss123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestTokenGeneration:
    """Tests for token generation and hashing."""

    def test_generate_verification_token_length(self):
        """Token should be 43 characters (32 bytes base64 URL-safe)."""
        token = generate_verification_token()

        assert len(token) == 43

    def test_generate_verification_token_unique(self):
        """Each token should be unique."""
        tokens = [generate_verification_token() for _ in range(100)]

        assert len(set(tokens)) == 100

    def test_generate_verification_token_url_safe(self):
        """Token should be URL-safe."""
        token = generate_verification_token()

        # URL-safe chars: a-z, A-Z, 0-9, -, _
        for char in token:
            assert char.isalnum() or char in "-_"

    def test_hash_token_produces_64_chars(self):
        """Token hash should be 64 characters (SHA-256 hex)."""
        token = generate_verification_token()
        hashed = hash_token(token)

        assert len(hashed) == 64

    def test_hash_token_deterministic(self):
        """Same token should produce same hash."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_hash_token_different_for_different_tokens(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")

        assert hash1 != hash2

    def test_compare_tokens_equal(self):
        """Equal tokens should compare as equal."""
        token = "test-token"

        assert compare_tokens(token, token) is True

    def test_compare_tokens_not_equal(self):
        """Different tokens should not compare as equal."""
        assert compare_tokens("token1", "token2") is False

    def test_generate_oauth_state_length(self):
        """OAuth state should be 43 characters."""
        state = generate_oauth_state()

        assert len(state) == 43

    def test_generate_oauth_state_unique(self):
        """OAuth states should be unique."""
        states = [generate_oauth_state() for _ in range(100)]

        assert len(set(states)) == 100


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Access token should be created successfully."""
        token = create_access_token({"sub": "user-123", "email": "test@example.com"})

        assert token is not None
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_create_access_token_contains_claims(self):
        """Token should contain provided claims."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    @freeze_time("2024-01-15 10:30:00")
    def test_verify_token_valid(self):
        """Valid token should verify successfully."""
        token = create_access_token({"sub": "user-123"})
        payload = verify_token(token, "access")

        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_verify_token_invalid(self):
        """Invalid token should return None."""
        payload = verify_token("invalid.token.here", "access")

        assert payload is None

    def test_verify_token_wrong_type(self):
        """Token with wrong type should return None."""
        token = create_access_token({"sub": "user-123"})
        payload = verify_token(token, "refresh")  # Wrong type

        assert payload is None


class TestPasswordValidator:
    """Tests for password strength validation."""

    def test_valid_password(self):
        """Strong password should pass validation."""
        result = PasswordValidator.validate("SecureP@ss123!")

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_password_too_short(self):
        """Password under 8 characters should fail."""
        result = PasswordValidator.validate("P@ss1")

        assert result["valid"] is False
        assert any("at least 8 characters" in e for e in result["errors"])

    def test_password_no_uppercase(self):
        """Password without uppercase should fail."""
        result = PasswordValidator.validate("securep@ss123!")

        assert result["valid"] is False
        assert any("uppercase" in e for e in result["errors"])

    def test_password_no_lowercase(self):
        """Password without lowercase should fail."""
        result = PasswordValidator.validate("SECUREP@SS123!")

        assert result["valid"] is False
        assert any("lowercase" in e for e in result["errors"])

    def test_password_no_number(self):
        """Password without number should fail."""
        result = PasswordValidator.validate("SecureP@ssword!")

        assert result["valid"] is False
        assert any("number" in e for e in result["errors"])

    def test_password_no_special(self):
        """Password without special character should fail."""
        result = PasswordValidator.validate("SecurePass123")

        assert result["valid"] is False
        assert any("special character" in e for e in result["errors"])

    def test_password_multiple_failures(self):
        """Password with multiple issues should report all."""
        result = PasswordValidator.validate("weak")

        assert result["valid"] is False
        assert len(result["errors"]) >= 3

    def test_is_valid_helper(self):
        """is_valid helper should return boolean."""
        assert PasswordValidator.is_valid("SecureP@ss123!") is True
        assert PasswordValidator.is_valid("weak") is False
