"""
Unit tests for registration schema validation.
"""

import pytest
from pydantic import ValidationError

from src.app.schemas.registration import RegistrationRequest


class TestRegistrationRequest:
    """Tests for registration request validation."""

    def test_valid_registration(self):
        """Valid registration data should pass validation."""
        data = {
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }
        request = RegistrationRequest(**data)

        assert request.email == "test@example.com"
        assert request.first_name == "John"

    def test_invalid_email(self):
        """Invalid email should fail validation."""
        data = {
            "email": "not-an-email",
            "password": "SecureP@ss123!",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "email" in str(exc_info.value)

    def test_password_too_short(self):
        """Password under 8 characters should fail."""
        data = {
            "email": "test@example.com",
            "password": "Short1!",  # 7 characters
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "8 characters" in str(exc_info.value).lower()

    def test_password_no_uppercase(self):
        """Password without uppercase should fail."""
        data = {
            "email": "test@example.com",
            "password": "securepass123!",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "uppercase" in str(exc_info.value).lower()

    def test_password_no_special_char(self):
        """Password without special character should fail."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "special character" in str(exc_info.value).lower()

    def test_terms_not_accepted(self):
        """Terms must be accepted."""
        data = {
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": False,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "agree_to_terms" in str(exc_info.value).lower()

    def test_privacy_not_accepted(self):
        """Privacy policy must be accepted."""
        data = {
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "first_name": "John",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": False,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "agree_to_privacy" in str(exc_info.value).lower()

    def test_whitespace_stripped_from_names(self):
        """Whitespace should be stripped from names."""
        data = {
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "first_name": "  John  ",
            "last_name": "  Doe  ",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }
        request = RegistrationRequest(**data)

        assert request.first_name == "John"
        assert request.last_name == "Doe"

    def test_empty_first_name(self):
        """Empty first name should fail."""
        data = {
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "first_name": "",
            "last_name": "Doe",
            "business_name": "Test Studio",
            "turnstile_token": "valid-token",
            "agree_to_terms": True,
            "agree_to_privacy": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            RegistrationRequest(**data)

        assert "first_name" in str(exc_info.value).lower()

    def test_password_with_all_requirements(self):
        """Password with all requirements should pass."""
        valid_passwords = [
            "SecureP@ss1",
            "Test123!abc",
            "Aa1!aaaa",
            "MyP@ssword123",
            "Complex!Password1",
        ]

        for password in valid_passwords:
            data = {
                "email": "test@example.com",
                "password": password,
                "first_name": "John",
                "last_name": "Doe",
                "business_name": "Test Studio",
                "turnstile_token": "valid-token",
                "agree_to_terms": True,
                "agree_to_privacy": True,
            }
            request = RegistrationRequest(**data)
            assert request.password == password
