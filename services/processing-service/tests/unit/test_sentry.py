"""Unit tests for Sentry integration."""

import pytest
from unittest.mock import patch, MagicMock


class TestInitSentry:
    """Tests for init_sentry function."""

    def test_init_without_dsn(self):
        """Should skip initialization when no DSN configured."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            with patch("app.core.sentry.sentry_sdk") as mock_sentry:
                from app.core.sentry import init_sentry
                init_sentry()

                mock_sentry.init.assert_not_called()

    def test_init_with_dsn(self):
        """Should initialize Sentry with DSN."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
            mock_settings.APP_ENV = "test"
            mock_settings.APP_VERSION = "1.0.0"

            with patch("app.core.sentry.sentry_sdk") as mock_sentry:
                from app.core.sentry import init_sentry
                init_sentry()

                mock_sentry.init.assert_called_once()


class TestTracesSampleRate:
    """Tests for _get_traces_sample_rate function."""

    def test_production_rate(self):
        """Should return 10% for production."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.APP_ENV = "production"

            from app.core.sentry import _get_traces_sample_rate
            rate = _get_traces_sample_rate()

            assert rate == 0.1

    def test_staging_rate(self):
        """Should return 50% for staging."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.APP_ENV = "staging"

            from app.core.sentry import _get_traces_sample_rate
            rate = _get_traces_sample_rate()

            assert rate == 0.5

    def test_development_rate(self):
        """Should return 100% for development."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.APP_ENV = "development"

            from app.core.sentry import _get_traces_sample_rate
            rate = _get_traces_sample_rate()

            assert rate == 1.0

    def test_unknown_env_default(self):
        """Should return 10% for unknown environment."""
        with patch("app.core.sentry.settings") as mock_settings:
            mock_settings.APP_ENV = "unknown"

            from app.core.sentry import _get_traces_sample_rate
            rate = _get_traces_sample_rate()

            assert rate == 0.1


class TestScrubSensitiveData:
    """Tests for _scrub_sensitive_data function."""

    def test_scrubs_authorization_header(self):
        """Should scrub authorization header."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer secret-token",
                    "Content-Type": "application/json",
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["headers"]["Authorization"] == "[FILTERED]"
        assert result["request"]["headers"]["Content-Type"] == "application/json"

    def test_scrubs_cookie_header(self):
        """Should scrub cookie header."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "headers": {
                    "Cookie": "session=abc123",
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["headers"]["Cookie"] == "[FILTERED]"

    def test_scrubs_api_key_header(self):
        """Should scrub X-API-Key header."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "headers": {
                    "X-API-Key": "secret-key",
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["headers"]["X-API-Key"] == "[FILTERED]"

    def test_scrubs_query_string_with_token(self):
        """Should scrub query string containing token."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "query_string": "token=secret&page=1",
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["query_string"] == "[FILTERED]"

    def test_preserves_non_sensitive_data(self):
        """Should preserve non-sensitive data."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "headers": {
                    "Accept": "application/json",
                },
                "query_string": "page=1&limit=10",
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["headers"]["Accept"] == "application/json"
        assert result["request"]["query_string"] == "page=1&limit=10"

    def test_handles_empty_event(self):
        """Should handle empty event."""
        from app.core.sentry import _scrub_sensitive_data

        event = {}
        result = _scrub_sensitive_data(event, {})

        assert result == {}


class TestFilterTransaction:
    """Tests for _filter_transaction function."""

    def test_filters_health_endpoint(self):
        """Should filter out health check transactions."""
        from app.core.sentry import _filter_transaction

        event = {
            "transaction": "/health",
        }

        result = _filter_transaction(event, {})

        assert result is None

    def test_filters_ready_endpoint(self):
        """Should filter out readiness check transactions."""
        from app.core.sentry import _filter_transaction

        event = {
            "transaction": "/ready",
        }

        result = _filter_transaction(event, {})

        assert result is None

    def test_filters_metrics_endpoint(self):
        """Should filter out metrics transactions."""
        from app.core.sentry import _filter_transaction

        event = {
            "transaction": "/metrics",
        }

        result = _filter_transaction(event, {})

        assert result is None

    def test_keeps_other_transactions(self):
        """Should keep other transactions."""
        from app.core.sentry import _filter_transaction

        event = {
            "transaction": "/api/process",
        }

        result = _filter_transaction(event, {})

        assert result == event


class TestScrubExceptionValue:
    """Tests for _scrub_exception_value function."""

    def test_scrubs_password_in_message(self):
        """Should scrub password from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Connection failed: password=secret123 in config"
        result = _scrub_exception_value(value)

        assert "secret123" not in result
        assert "password=[FILTERED]" in result

    def test_scrubs_secret_in_message(self):
        """Should scrub secret from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Error: secret=mysecretvalue"
        result = _scrub_exception_value(value)

        assert "mysecretvalue" not in result
        assert "secret=[FILTERED]" in result

    def test_scrubs_api_key_in_message(self):
        """Should scrub api_key from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Auth failed: api_key=sk-12345"
        result = _scrub_exception_value(value)

        assert "sk-12345" not in result
        assert "api_key=[FILTERED]" in result

    def test_scrubs_api_key_with_hyphen(self):
        """Should scrub api-key format from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Auth failed: api-key=sk-12345"
        result = _scrub_exception_value(value)

        assert "sk-12345" not in result
        assert "api_key=[FILTERED]" in result

    def test_scrubs_token_in_message(self):
        """Should scrub token from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Invalid token=jwt.token.here"
        result = _scrub_exception_value(value)

        assert "jwt.token.here" not in result
        assert "token=[FILTERED]" in result

    def test_scrubs_bearer_token(self):
        """Should scrub Bearer token from exception message."""
        from app.core.sentry import _scrub_exception_value

        value = "Auth header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = _scrub_exception_value(value)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "Bearer [FILTERED]" in result

    def test_scrubs_email_addresses(self):
        """Should scrub email addresses (PII)."""
        from app.core.sentry import _scrub_exception_value

        value = "User not found: user@example.com"
        result = _scrub_exception_value(value)

        assert "user@example.com" not in result
        assert "[EMAIL]" in result

    def test_preserves_non_sensitive_message(self):
        """Should preserve non-sensitive exception messages."""
        from app.core.sentry import _scrub_exception_value

        value = "Connection timeout after 30 seconds"
        result = _scrub_exception_value(value)

        assert result == "Connection timeout after 30 seconds"

    def test_scrubs_multiple_patterns(self):
        """Should scrub multiple sensitive patterns in same message."""
        from app.core.sentry import _scrub_exception_value

        value = "Error: password=secret123, token=abc, email: test@test.com"
        result = _scrub_exception_value(value)

        assert "secret123" not in result
        assert "abc" not in result
        assert "test@test.com" not in result


class TestScrubDict:
    """Tests for _scrub_dict function."""

    def test_scrubs_password_key(self):
        """Should scrub password key."""
        from app.core.sentry import _scrub_dict

        data = {"password": "secret123", "username": "john"}
        result = _scrub_dict(data)

        assert result["password"] == "[FILTERED]"
        assert result["username"] == "john"

    def test_scrubs_secret_key(self):
        """Should scrub secret key."""
        from app.core.sentry import _scrub_dict

        data = {"secret": "mysecret", "name": "test"}
        result = _scrub_dict(data)

        assert result["secret"] == "[FILTERED]"
        assert result["name"] == "test"

    def test_scrubs_token_key(self):
        """Should scrub token key."""
        from app.core.sentry import _scrub_dict

        data = {"token": "jwt123", "id": "1"}
        result = _scrub_dict(data)

        assert result["token"] == "[FILTERED]"
        assert result["id"] == "1"

    def test_scrubs_api_key(self):
        """Should scrub api_key."""
        from app.core.sentry import _scrub_dict

        data = {"api_key": "sk-123", "version": "1.0"}
        result = _scrub_dict(data)

        assert result["api_key"] == "[FILTERED]"
        assert result["version"] == "1.0"

    def test_scrubs_authorization_key(self):
        """Should scrub authorization key."""
        from app.core.sentry import _scrub_dict

        data = {"authorization": "Bearer abc", "type": "jwt"}
        result = _scrub_dict(data)

        assert result["authorization"] == "[FILTERED]"
        assert result["type"] == "jwt"

    def test_scrubs_nested_dict(self):
        """Should scrub nested dictionaries recursively."""
        from app.core.sentry import _scrub_dict

        data = {
            "config": {
                "password": "secret",
                "host": "localhost"
            },
            "name": "test"
        }
        result = _scrub_dict(data)

        assert result["config"]["password"] == "[FILTERED]"
        assert result["config"]["host"] == "localhost"
        assert result["name"] == "test"

    def test_scrubs_dict_in_list(self):
        """Should scrub dicts inside lists."""
        from app.core.sentry import _scrub_dict

        data = {
            "items": [
                {"password": "secret1", "id": "1"},
                {"password": "secret2", "id": "2"}
            ]
        }
        result = _scrub_dict(data)

        assert result["items"][0]["password"] == "[FILTERED]"
        assert result["items"][0]["id"] == "1"
        assert result["items"][1]["password"] == "[FILTERED]"
        assert result["items"][1]["id"] == "2"

    def test_preserves_non_dict_list_items(self):
        """Should preserve non-dict items in lists."""
        from app.core.sentry import _scrub_dict

        data = {
            "tags": ["tag1", "tag2"],
            "password": "secret"
        }
        result = _scrub_dict(data)

        assert result["tags"] == ["tag1", "tag2"]
        assert result["password"] == "[FILTERED]"

    def test_scrubs_partial_key_match(self):
        """Should scrub keys containing sensitive keywords."""
        from app.core.sentry import _scrub_dict

        data = {
            "user_password": "secret",
            "api_token_v2": "abc123",
            "encryption_key_id": "key-1"
        }
        result = _scrub_dict(data)

        assert result["user_password"] == "[FILTERED]"
        assert result["api_token_v2"] == "[FILTERED]"
        assert result["encryption_key_id"] == "[FILTERED]"

    def test_handles_empty_dict(self):
        """Should handle empty dict."""
        from app.core.sentry import _scrub_dict

        result = _scrub_dict({})
        assert result == {}


class TestScrubSensitiveDataFull:
    """Additional tests for _scrub_sensitive_data covering exception and extra data."""

    def test_scrubs_exception_values(self):
        """Should scrub sensitive data in exception values."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "exception": {
                "values": [
                    {"value": "Connection error: password=secret123"},
                    {"value": "Normal error message"}
                ]
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert "secret123" not in result["exception"]["values"][0]["value"]
        assert result["exception"]["values"][1]["value"] == "Normal error message"

    def test_scrubs_extra_data(self):
        """Should scrub sensitive data in extra context."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "extra": {
                "password": "secret",
                "user_id": "123",
                "config": {
                    "api_key": "sk-123",
                    "host": "localhost"
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["extra"]["password"] == "[FILTERED]"
        assert result["extra"]["user_id"] == "123"
        assert result["extra"]["config"]["api_key"] == "[FILTERED]"
        assert result["extra"]["config"]["host"] == "localhost"

    def test_scrubs_contexts(self):
        """Should scrub sensitive data in contexts."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "contexts": {
                "app": {
                    "token": "secret-token",
                    "version": "1.0"
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["contexts"]["app"]["token"] == "[FILTERED]"
        assert result["contexts"]["app"]["version"] == "1.0"

    def test_scrubs_multiple_sections(self):
        """Should scrub all sections when present."""
        from app.core.sentry import _scrub_sensitive_data

        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer token"
                }
            },
            "exception": {
                "values": [
                    {"value": "Error with password=secret"}
                ]
            },
            "extra": {
                "api_key": "sk-123"
            },
            "contexts": {
                "app": {
                    "token": "jwt"
                }
            }
        }

        result = _scrub_sensitive_data(event, {})

        assert result["request"]["headers"]["Authorization"] == "[FILTERED]"
        assert "secret" not in result["exception"]["values"][0]["value"]
        assert result["extra"]["api_key"] == "[FILTERED]"
        assert result["contexts"]["app"]["token"] == "[FILTERED]"


class TestSetContext:
    """Tests for set_context function."""

    def test_set_context_with_asset_id(self):
        """Should set asset_id tag in scope."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.configure_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.configure_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import set_context
            set_context(asset_id="asset-123")

            mock_scope.set_tag.assert_called_with("asset_id", "asset-123")

    def test_set_context_with_workspace_id(self):
        """Should set workspace_id tag in scope."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.configure_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.configure_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import set_context
            set_context(workspace_id="ws-456")

            mock_scope.set_tag.assert_called_with("workspace_id", "ws-456")

    def test_set_context_with_both_ids(self):
        """Should set both tags in scope."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.configure_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.configure_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import set_context
            set_context(asset_id="asset-123", workspace_id="ws-456")

            calls = mock_scope.set_tag.call_args_list
            assert any(call[0] == ("asset_id", "asset-123") for call in calls)
            assert any(call[0] == ("workspace_id", "ws-456") for call in calls)

    def test_set_context_with_extra_kwargs(self):
        """Should set extra data in scope."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.configure_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.configure_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import set_context
            set_context(asset_id="asset-123", stage="thumbnail", progress=50)

            mock_scope.set_extra.assert_any_call("stage", "thumbnail")
            mock_scope.set_extra.assert_any_call("progress", 50)

    def test_set_context_without_ids(self):
        """Should handle call without ids, only kwargs."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.configure_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.configure_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import set_context
            set_context(custom_key="custom_value")

            mock_scope.set_tag.assert_not_called()
            mock_scope.set_extra.assert_called_with("custom_key", "custom_value")


class TestCaptureProcessingError:
    """Tests for capture_processing_error function."""

    def test_captures_error_with_context(self):
        """Should capture exception with proper context."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.push_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import capture_processing_error

            error = ValueError("Test error")
            capture_processing_error(
                error=error,
                asset_id="asset-123",
                workspace_id="ws-456",
                stage="thumbnail"
            )

            # Verify tags were set
            calls = mock_scope.set_tag.call_args_list
            assert any(call[0] == ("asset_id", "asset-123") for call in calls)
            assert any(call[0] == ("workspace_id", "ws-456") for call in calls)
            assert any(call[0] == ("processing_stage", "thumbnail") for call in calls)

            # Verify level was set
            mock_scope.set_level.assert_called_with("error")

            # Verify exception was captured
            mock_sentry.capture_exception.assert_called_once_with(error)

    def test_captures_error_with_extra_data(self):
        """Should set extra data from kwargs."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_scope = MagicMock()
            mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
            mock_sentry.push_scope.return_value.__exit__ = MagicMock(return_value=False)

            from app.core.sentry import capture_processing_error

            error = RuntimeError("Processing failed")
            capture_processing_error(
                error=error,
                asset_id="asset-123",
                workspace_id="ws-456",
                stage="exif",
                filename="test.jpg",
                file_size=1024
            )

            mock_scope.set_extra.assert_any_call("filename", "test.jpg")
            mock_scope.set_extra.assert_any_call("file_size", 1024)


class TestStartTransaction:
    """Tests for start_transaction function."""

    def test_starts_transaction_with_name(self):
        """Should start transaction with name and op."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            from app.core.sentry import start_transaction

            start_transaction(name="process_image", op="task")

            mock_sentry.start_transaction.assert_called_once_with(
                name="process_image",
                op="task"
            )

    def test_starts_transaction_with_default_op(self):
        """Should use default op='task' when not specified."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            from app.core.sentry import start_transaction

            start_transaction(name="thumbnail_generation")

            mock_sentry.start_transaction.assert_called_once_with(
                name="thumbnail_generation",
                op="task"
            )

    def test_starts_transaction_with_kwargs(self):
        """Should pass additional kwargs to start_transaction."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            from app.core.sentry import start_transaction

            start_transaction(
                name="face_detection",
                op="ml",
                description="Detect faces in image"
            )

            mock_sentry.start_transaction.assert_called_once_with(
                name="face_detection",
                op="ml",
                description="Detect faces in image"
            )

    def test_returns_transaction_object(self):
        """Should return the transaction object."""
        with patch("app.core.sentry.sentry_sdk") as mock_sentry:
            mock_transaction = MagicMock()
            mock_sentry.start_transaction.return_value = mock_transaction

            from app.core.sentry import start_transaction

            result = start_transaction(name="test")

            assert result == mock_transaction


class TestSentryHelpers:
    """Tests for Sentry helper functionality."""

    def test_filter_transaction_exists(self):
        """Should have _filter_transaction function."""
        from app.core.sentry import _filter_transaction

        # Verify function exists
        assert callable(_filter_transaction)

    def test_scrub_function_exists(self):
        """Should have _scrub_sensitive_data function."""
        from app.core.sentry import _scrub_sensitive_data

        # Verify function exists
        assert callable(_scrub_sensitive_data)
