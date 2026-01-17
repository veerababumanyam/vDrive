"""Unit tests for structured logging with PII scrubbing."""

import pytest
from unittest.mock import patch, MagicMock


class TestScrubPiiValue:
    """Tests for _scrub_pii_value function."""

    def test_scrubs_email(self):
        """Should redact email addresses."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Contact: user@example.com")
        assert "[EMAIL]" in result
        assert "user@example.com" not in result

    def test_scrubs_phone_number(self):
        """Should redact phone numbers."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Call me at 123-456-7890")
        assert "[PHONE]" in result
        assert "123-456-7890" not in result

    def test_scrubs_phone_number_dotted(self):
        """Should redact phone numbers with dots."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Phone: 123.456.7890")
        assert "[PHONE]" in result

    def test_scrubs_ssn(self):
        """Should redact SSN."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("SSN: 123-45-6789")
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_scrubs_credit_card(self):
        """Should redact credit card numbers."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Card: 1234-5678-9012-3456")
        assert "[CREDIT_CARD]" in result

    def test_scrubs_bearer_token(self):
        """Should redact bearer tokens."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Authorization: Bearer abc123def456")
        assert "Bearer [REDACTED]" in result
        assert "abc123def456" not in result

    def test_preserves_non_pii_text(self):
        """Should preserve non-PII text."""
        from app.core.logging import _scrub_pii_value

        result = _scrub_pii_value("Processing asset id: asset-123")
        assert result == "Processing asset id: asset-123"


class TestScrubPiiDict:
    """Tests for _scrub_pii_dict function."""

    def test_scrubs_sensitive_keys(self):
        """Should redact values for sensitive keys."""
        from app.core.logging import _scrub_pii_dict

        data = {
            "email": "user@example.com",
            "password": "secret123",
            "username": "john",
        }

        result = _scrub_pii_dict(data)

        assert result["email"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["username"] == "john"

    def test_scrubs_nested_dict(self):
        """Should recursively scrub nested dictionaries."""
        from app.core.logging import _scrub_pii_dict

        data = {
            "user": {
                "email": "user@example.com",
                "name": "John",
            }
        }

        result = _scrub_pii_dict(data)

        assert result["user"]["email"] == "[REDACTED]"
        assert result["user"]["name"] == "John"

    def test_scrubs_list_values(self):
        """Should scrub PII in list values."""
        from app.core.logging import _scrub_pii_dict

        data = {
            "messages": ["Contact me at user@example.com", "Hello world"]
        }

        result = _scrub_pii_dict(data)

        assert "[EMAIL]" in result["messages"][0]
        assert result["messages"][1] == "Hello world"

    def test_scrubs_api_key(self):
        """Should redact API key values."""
        from app.core.logging import _scrub_pii_dict

        data = {
            "api_key": "sk-abc123",
            "apikey": "key-456",
            "api_Key": "key-789",
        }

        result = _scrub_pii_dict(data)

        assert result["api_key"] == "[REDACTED]"
        assert result["apikey"] == "[REDACTED]"
        assert result["api_Key"] == "[REDACTED]"

    def test_scrubs_authorization(self):
        """Should redact authorization values."""
        from app.core.logging import _scrub_pii_dict

        data = {
            "authorization": "Bearer token123",
            "auth_token": "token456",
        }

        result = _scrub_pii_dict(data)

        assert result["authorization"] == "[REDACTED]"
        assert result["auth_token"] == "[REDACTED]"


class TestPiiScrubber:
    """Tests for pii_scrubber processor."""

    def test_scrubs_log_event(self):
        """Should scrub PII from log event dict."""
        from app.core.logging import pii_scrubber

        event_dict = {
            "event": "User login",
            "email": "user@example.com",
            "ip_address": "192.168.1.1",
        }

        result = pii_scrubber(None, None, event_dict)

        assert result["event"] == "User login"
        assert result["email"] == "[REDACTED]"
        assert result["ip_address"] == "[REDACTED]"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_info_level(self):
        """Should configure logging with INFO level."""
        with patch("app.core.logging.structlog") as mock_structlog:
            with patch("app.core.logging.logging") as mock_logging:
                from app.core.logging import configure_logging
                configure_logging(log_level="INFO")

                mock_structlog.configure.assert_called_once()

    def test_configure_debug_level(self):
        """Should configure logging with DEBUG level."""
        with patch("app.core.logging.structlog") as mock_structlog:
            with patch("app.core.logging.logging") as mock_logging:
                from app.core.logging import configure_logging
                configure_logging(log_level="DEBUG")

                mock_structlog.configure.assert_called_once()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Should return a logger instance."""
        from app.core.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_default_name(self):
        """Should use module name as default."""
        from app.core.logging import get_logger

        logger = get_logger()
        assert logger is not None


class TestPiiKeys:
    """Tests for PII_KEYS constant."""

    def test_contains_common_pii_keys(self):
        """Should contain common PII key names."""
        from app.core.logging import PII_KEYS

        assert "email" in PII_KEYS
        assert "password" in PII_KEYS
        assert "token" in PII_KEYS
        assert "api_key" in PII_KEYS
        assert "credit_card" in PII_KEYS
