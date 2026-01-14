"""Tests for validation utilities."""

import pytest

from src.app.utils.validation import validate_email, validate_hex_color, validate_pin


class TestValidateEmail:
    """Test email validation."""

    def test_valid_emails(self):
        """Test valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@test-domain.com",
            "a@b.c",
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"Failed for: {email}"

    def test_invalid_emails(self):
        """Test invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "",
            "user@@example.com",
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"Should fail for: {email}"


class TestValidatePin:
    """Test PIN validation."""

    def test_valid_pins(self):
        """Test valid PIN formats (4-6 digits)."""
        valid_pins = ["1234", "12345", "123456", "0000", "9999"]
        for pin in valid_pins:
            is_valid, error = validate_pin(pin)
            assert is_valid is True, f"Failed for: {pin}"
            assert error is None

    def test_empty_pin(self):
        """Test empty PIN."""
        is_valid, error = validate_pin("")
        assert is_valid is False
        assert error == "PIN is required"

    def test_non_digit_pin(self):
        """Test PIN with non-digit characters."""
        invalid_pins = ["abcd", "12a4", "12-34", "12 34"]
        for pin in invalid_pins:
            is_valid, error = validate_pin(pin)
            assert is_valid is False
            assert error == "PIN must contain only digits"

    def test_pin_too_short(self):
        """Test PIN shorter than 4 digits."""
        is_valid, error = validate_pin("123")
        assert is_valid is False
        assert error == "PIN must be at least 4 digits"

    def test_pin_too_long(self):
        """Test PIN longer than 6 digits."""
        is_valid, error = validate_pin("1234567")
        assert is_valid is False
        assert error == "PIN must be at most 6 digits"


class TestValidateHexColor:
    """Test hex color validation."""

    def test_valid_hex_colors(self):
        """Test valid hex color formats."""
        valid_colors = [
            "#000000",
            "#FFFFFF",
            "#ff0000",
            "#00FF00",
            "#0000ff",
            "#abc",
            "#ABC",
            "#123",
        ]
        for color in valid_colors:
            assert validate_hex_color(color) is True, f"Failed for: {color}"

    def test_invalid_hex_colors(self):
        """Test invalid hex color formats."""
        invalid_colors = [
            "",
            "000000",
            "#0000",
            "#00",
            "#gggggg",
            "#12345",
            "#1234567",
            "red",
        ]
        for color in invalid_colors:
            assert validate_hex_color(color) is False, f"Should fail for: {color}"
