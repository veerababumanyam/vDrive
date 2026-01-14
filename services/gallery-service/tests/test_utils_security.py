"""Tests for security utilities (password/PIN hashing)."""

from src.app.utils.security import hash_password, hash_pin, verify_password, verify_pin


class TestPasswordHashing:
    """Test password hashing with Argon2id."""

    def test_hash_and_verify_password(self):
        """Test hashing and verifying a password."""
        password = "my-secure-password-123"

        # Hash password
        password_hash = hash_password(password)

        # Verify correct password
        assert verify_password(password_hash, password) is True

        # Verify incorrect password
        assert verify_password(password_hash, "wrong-password") is False

    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "test-password"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to random salt
        assert hash1 != hash2

        # But both verify correctly
        assert verify_password(hash1, password) is True
        assert verify_password(hash2, password) is True


class TestPinHashing:
    """Test PIN hashing with Argon2id."""

    def test_hash_and_verify_pin(self):
        """Test hashing and verifying a PIN."""
        pin = "1234"

        # Hash PIN
        pin_hash = hash_pin(pin)

        # Verify correct PIN
        assert verify_pin(pin_hash, pin) is True

        # Verify incorrect PIN
        assert verify_pin(pin_hash, "9999") is False

    def test_different_pins_different_hashes(self):
        """Test that same PIN produces different hashes (salt)."""
        pin = "5678"

        hash1 = hash_pin(pin)
        hash2 = hash_pin(pin)

        # Different hashes due to random salt
        assert hash1 != hash2

        # But both verify correctly
        assert verify_pin(hash1, pin) is True
        assert verify_pin(hash2, pin) is True

    def test_pin_uses_same_algorithm_as_password(self):
        """Test that PIN hashing uses same Argon2id algorithm."""
        pin = "1234"

        # Hash using both methods
        pin_hash = hash_pin(pin)
        password_hash = hash_password(pin)

        # Both should verify with either function (same algorithm)
        assert verify_pin(pin_hash, pin) is True
        assert verify_password(pin_hash, pin) is True
        assert verify_pin(password_hash, pin) is True
        assert verify_password(password_hash, pin) is True
