"""Unit tests for Dead Letter Queue (DLQ) producer.

Tests Kafka producer for DLQ messages including message format,
error handling, and sanitization.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.core.kafka_producer import KafkaProducerManager


class TestKafkaProducerManager:
    """Test Kafka producer manager."""

    @pytest.fixture
    def reset_singleton(self):
        """Reset singleton for each test."""
        KafkaProducerManager._instance = None
        KafkaProducerManager._initialized = False
        yield
        KafkaProducerManager._instance = None
        KafkaProducerManager._initialized = False

    @pytest.fixture
    def producer_manager(self, reset_singleton):
        """Create a fresh producer manager instance."""
        return KafkaProducerManager()

    def test_singleton_pattern(self, reset_singleton):
        """Test that KafkaProducerManager follows singleton pattern."""
        manager1 = KafkaProducerManager()
        manager2 = KafkaProducerManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_initialize_success(self, producer_manager):
        """Test successful Kafka producer initialization."""
        mock_producer = AsyncMock()

        with patch("src.app.core.kafka_producer.AIOKafkaProducer") as mock_class:
            mock_class.return_value = mock_producer

            await producer_manager.initialize()

            assert producer_manager.is_healthy is True
            mock_producer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, producer_manager):
        """Test Kafka producer initialization failure."""
        from aiokafka.errors import KafkaError

        with patch("src.app.core.kafka_producer.AIOKafkaProducer") as mock_class:
            mock_class.return_value.start = AsyncMock(side_effect=KafkaError("Connection failed"))

            await producer_manager.initialize()

            assert producer_manager.is_healthy is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, producer_manager):
        """Test successful message sending."""
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        producer_manager._producer = mock_producer
        producer_manager._healthy = True

        result = await producer_manager.send(
            topic="test-topic",
            value={"key": "value"},
            key="partition-key",
        )

        assert result is True
        mock_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_returns_false_when_unhealthy(self, producer_manager):
        """Test send returns False when producer is unhealthy."""
        producer_manager._healthy = False

        result = await producer_manager.send(
            topic="test-topic",
            value={"key": "value"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_handles_kafka_error(self, producer_manager):
        """Test send handles Kafka errors gracefully."""
        from aiokafka.errors import KafkaError

        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(side_effect=KafkaError("Send failed"))
        producer_manager._producer = mock_producer
        producer_manager._healthy = True

        result = await producer_manager.send(
            topic="test-topic",
            value={"key": "value"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_dlq_creates_correct_message(self, producer_manager):
        """Test DLQ message format matches specification."""
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        producer_manager._producer = mock_producer
        producer_manager._healthy = True

        captured_message = None

        async def capture_message(topic, value, key, headers=None):
            nonlocal captured_message
            captured_message = {"topic": topic, "value": value, "key": key}

        mock_producer.send_and_wait = capture_message

        await producer_manager.send_to_dlq(
            original_topic="upload.completed",
            original_partition=0,
            original_offset=12345,
            original_key="workspace-123",
            original_value={"event_id": "evt-456", "asset_id": "asset-789"},
            original_timestamp=1705312345000,
            error="Processing failed: image corrupted",
            error_type="processing",
            retry_count=3,
            consumer_group="asset-processor",
            correlation_id="corr-001",
            stack_trace="Traceback...",
        )

        assert captured_message is not None
        assert captured_message["topic"] == "upload.completed.dlq"
        assert captured_message["key"] == "workspace-123"

        dlq_value = captured_message["value"]
        assert dlq_value["original_topic"] == "upload.completed"
        assert dlq_value["original_partition"] == 0
        assert dlq_value["original_offset"] == 12345
        assert dlq_value["original_key"] == "workspace-123"
        assert dlq_value["original_value"]["event_id"] == "evt-456"
        assert dlq_value["original_timestamp"] == 1705312345000
        assert dlq_value["error"] == "Processing failed: image corrupted"
        assert dlq_value["error_type"] == "processing"
        assert dlq_value["retry_count"] == 3
        assert dlq_value["consumer_group"] == "asset-processor"
        assert dlq_value["correlation_id"] == "corr-001"
        assert "failed_at" in dlq_value

    @pytest.mark.asyncio
    async def test_send_to_dlq_sanitizes_stack_trace(self, producer_manager):
        """Test DLQ sanitizes sensitive information from stack traces."""
        mock_producer = AsyncMock()
        producer_manager._producer = mock_producer
        producer_manager._healthy = True

        captured_message = None

        async def capture_message(topic, value, key, headers=None):
            nonlocal captured_message
            captured_message = value

        mock_producer.send_and_wait = capture_message

        sensitive_stack = """
        File "config.py", line 42
            password='super_secret_password'
            api_key="my_api_key_12345"
            token = 'bearer_token_xyz'
        """

        await producer_manager.send_to_dlq(
            original_topic="test.topic",
            original_partition=0,
            original_offset=0,
            original_key=None,
            original_value={},
            original_timestamp=0,
            error="Error",
            error_type="test",
            retry_count=0,
            consumer_group="test",
            stack_trace=sensitive_stack,
        )

        sanitized = captured_message["stack_trace"]
        assert "super_secret_password" not in sanitized
        assert "my_api_key_12345" not in sanitized
        assert "bearer_token_xyz" not in sanitized
        assert "***" in sanitized

    def test_sanitize_stack_trace_removes_passwords(self, producer_manager):
        """Test stack trace sanitization removes password patterns."""
        stack = 'password="secret123"'
        sanitized = producer_manager._sanitize_stack_trace(stack)
        assert "secret123" not in sanitized

    def test_sanitize_stack_trace_removes_secrets(self, producer_manager):
        """Test stack trace sanitization removes secret patterns."""
        stack = "secret='my_secret_value'"
        sanitized = producer_manager._sanitize_stack_trace(stack)
        assert "my_secret_value" not in sanitized

    def test_sanitize_stack_trace_removes_tokens(self, producer_manager):
        """Test stack trace sanitization removes token patterns."""
        stack = 'token: "jwt_token_here"'
        sanitized = producer_manager._sanitize_stack_trace(stack)
        assert "jwt_token_here" not in sanitized

    def test_sanitize_stack_trace_removes_api_keys(self, producer_manager):
        """Test stack trace sanitization removes API key patterns."""
        stack = "api_key=sk-1234567890abcdef"
        sanitized = producer_manager._sanitize_stack_trace(stack)
        assert "sk-1234567890abcdef" not in sanitized

    def test_sanitize_stack_trace_truncates_long_traces(self, producer_manager):
        """Test stack trace is truncated when too long."""
        long_stack = "x" * 5000
        sanitized = producer_manager._sanitize_stack_trace(long_stack)
        assert len(sanitized) <= 4020  # 4000 + "... [truncated]"
        assert "[truncated]" in sanitized

    @pytest.mark.asyncio
    async def test_close_flushes_and_stops(self, producer_manager):
        """Test close properly flushes and stops producer."""
        mock_producer = AsyncMock()
        producer_manager._producer = mock_producer
        producer_manager._healthy = True

        await producer_manager.close()

        mock_producer.stop.assert_called_once()
        assert producer_manager._healthy is False


class TestBaseConsumerDLQ:
    """Test BaseConsumer DLQ methods."""

    @pytest.fixture
    def mock_consumer(self):
        """Create a mock consumer for testing DLQ."""
        from src.app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event: dict):
                pass

        return TestConsumer(
            topics=["test-topic"],
            consumer_group="test-group",
        )

    def test_classify_error_connection(self, mock_consumer):
        """Test connection errors are classified correctly."""
        error = ConnectionError("Connection refused")
        assert mock_consumer._classify_error(error) == "connection"

    def test_classify_error_timeout(self, mock_consumer):
        """Test timeout errors are classified correctly."""
        error = TimeoutError("Request timed out")
        assert mock_consumer._classify_error(error) == "timeout"

    def test_classify_error_validation(self, mock_consumer):
        """Test validation errors are classified correctly."""
        error = ValueError("Invalid value")
        assert mock_consumer._classify_error(error) == "validation"

    def test_classify_error_data_format(self, mock_consumer):
        """Test data format errors are classified correctly."""
        error = KeyError("Missing key")
        assert mock_consumer._classify_error(error) == "data_format"

    def test_classify_error_storage(self, mock_consumer):
        """Test storage errors are classified correctly."""
        error = FileNotFoundError("File not found")
        assert mock_consumer._classify_error(error) == "storage"

    def test_classify_error_unknown(self, mock_consumer):
        """Test unknown errors default to processing."""
        error = RuntimeError("Unknown error")
        assert mock_consumer._classify_error(error) == "processing"

    @pytest.mark.asyncio
    async def test_send_to_dlq_calls_producer(self, mock_consumer):
        """Test _send_to_dlq calls Kafka producer."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = b"test-key"
        mock_message.value = {"event_id": "evt-123", "workspace_id": "ws-456"}
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(return_value=True)

            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )

            mock_producer.send_to_dlq.assert_called_once()
            call_kwargs = mock_producer.send_to_dlq.call_args.kwargs
            assert call_kwargs["original_topic"] == "test-topic"
            assert call_kwargs["error"] == "Test error"
            assert call_kwargs["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_send_to_dlq_handles_none_key(self, mock_consumer):
        """Test _send_to_dlq handles None message key."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = None
        mock_message.value = {"event_id": "evt-123"}
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(return_value=True)

            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )

            call_kwargs = mock_producer.send_to_dlq.call_args.kwargs
            assert call_kwargs["original_key"] is None

    @pytest.mark.asyncio
    async def test_send_to_dlq_extracts_correlation_id(self, mock_consumer):
        """Test _send_to_dlq extracts correlation_id from event."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = None
        mock_message.value = {
            "event_id": "evt-123",
            "correlation_id": "corr-456",
        }
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(return_value=True)

            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )

            call_kwargs = mock_producer.send_to_dlq.call_args.kwargs
            assert call_kwargs["correlation_id"] == "corr-456"

    @pytest.mark.asyncio
    async def test_send_to_dlq_falls_back_to_event_id(self, mock_consumer):
        """Test _send_to_dlq uses event_id as fallback correlation_id."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = None
        mock_message.value = {"event_id": "evt-123"}
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(return_value=True)

            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )

            call_kwargs = mock_producer.send_to_dlq.call_args.kwargs
            assert call_kwargs["correlation_id"] == "evt-123"

    @pytest.mark.asyncio
    async def test_send_to_dlq_handles_producer_failure(self, mock_consumer):
        """Test _send_to_dlq handles producer failure gracefully."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = None
        mock_message.value = {}
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(return_value=False)

            # Should not raise
            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )

    @pytest.mark.asyncio
    async def test_send_to_dlq_handles_exception(self, mock_consumer):
        """Test _send_to_dlq handles exceptions gracefully."""
        mock_message = MagicMock()
        mock_message.topic = "test-topic"
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.key = None
        mock_message.value = {}
        mock_message.timestamp = 1705312345000

        with patch("src.app.consumers.base_consumer.kafka_producer") as mock_producer:
            mock_producer.send_to_dlq = AsyncMock(side_effect=Exception("Producer error"))

            # Should not raise
            await mock_consumer._send_to_dlq(
                message=mock_message,
                error="Test error",
                error_type="processing",
                retry_count=3,
            )
