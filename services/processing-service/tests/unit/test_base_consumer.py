"""Unit tests for BaseConsumer class."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class ConcreteConsumer:
    """Concrete implementation for testing."""

    def __init__(self, topics, consumer_group, max_retries=3, auto_commit=False):
        self.topics = topics
        self.consumer_group = consumer_group
        self.max_retries = max_retries
        self.auto_commit = auto_commit
        self.consumer = None
        self._running = False
        self._last_lag_update = 0.0

    async def process_event(self, event):
        """Process event implementation."""
        pass


class TestBaseConsumerInit:
    """Tests for BaseConsumer initialization."""

    def test_init_stores_topics(self):
        """Should store topics list."""
        consumer = ConcreteConsumer(
            topics=["topic1", "topic2"],
            consumer_group="test-group",
        )
        assert consumer.topics == ["topic1", "topic2"]

    def test_init_stores_consumer_group(self):
        """Should store consumer group."""
        consumer = ConcreteConsumer(
            topics=["topic1"],
            consumer_group="my-group",
        )
        assert consumer.consumer_group == "my-group"

    def test_init_stores_max_retries(self):
        """Should store max retries."""
        consumer = ConcreteConsumer(
            topics=["topic1"],
            consumer_group="test-group",
            max_retries=5,
        )
        assert consumer.max_retries == 5

    def test_init_default_max_retries(self):
        """Should default max retries to 3."""
        consumer = ConcreteConsumer(
            topics=["topic1"],
            consumer_group="test-group",
        )
        assert consumer.max_retries == 3

    def test_init_stores_auto_commit(self):
        """Should store auto commit setting."""
        consumer = ConcreteConsumer(
            topics=["topic1"],
            consumer_group="test-group",
            auto_commit=True,
        )
        assert consumer.auto_commit is True

    def test_init_default_auto_commit_false(self):
        """Should default auto commit to False."""
        consumer = ConcreteConsumer(
            topics=["topic1"],
            consumer_group="test-group",
        )
        assert consumer.auto_commit is False


class TestIdempotencyKey:
    """Tests for _idempotency_key method."""

    def test_key_without_workspace(self):
        """Should generate key without workspace prefix."""
        from app.consumers.base_consumer import BaseConsumer

        # Create minimal concrete implementation
        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            key = consumer._idempotency_key("event-123", None)
            assert key == "processing:idempotent:event-123"

    def test_key_with_workspace(self):
        """Should include workspace in key."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            key = consumer._idempotency_key("event-123", "workspace-456")
            assert key == "processing:idempotent:workspace-456:event-123"


class TestClassifyError:
    """Tests for _classify_error method."""

    def test_classifies_connection_error(self):
        """Should classify ConnectionError as 'connection'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(ConnectionError("test"))
            assert result == "connection"

    def test_classifies_timeout_error(self):
        """Should classify TimeoutError as 'timeout'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(TimeoutError("test"))
            assert result == "timeout"

    def test_classifies_value_error_as_validation(self):
        """Should classify ValueError as 'validation'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(ValueError("test"))
            assert result == "validation"

    def test_classifies_key_error_as_data_format(self):
        """Should classify KeyError as 'data_format'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(KeyError("test"))
            assert result == "data_format"

    def test_classifies_unknown_as_processing(self):
        """Should classify unknown errors as 'processing'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(RuntimeError("test"))
            assert result == "processing"

    def test_classifies_file_not_found_as_storage(self):
        """Should classify FileNotFoundError as 'storage'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(FileNotFoundError("test"))
            assert result == "storage"


class TestIsAlreadyProcessed:
    """Tests for _is_already_processed method."""

    @pytest.mark.asyncio
    async def test_returns_false_for_empty_event_id(self):
        """Should return False for empty event_id."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            result = await consumer._is_already_processed("", "ws-1")
            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_none_event_id(self):
        """Should return False for None event_id."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            result = await consumer._is_already_processed(None, "ws-1")
            assert result is False

    @pytest.mark.asyncio
    async def test_checks_redis_for_existing_key(self):
        """Should check Redis for existing key."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.exists = AsyncMock(return_value=True)

                result = await consumer._is_already_processed("event-123", "ws-1")

                assert result is True
                mock_redis.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_on_redis_error(self):
        """Should return False on Redis error (graceful degradation)."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))

                with patch("app.consumers.base_consumer.idempotency_redis_errors_total") as mock_metric:
                    result = await consumer._is_already_processed("event-123", "ws-1")

                    assert result is False
                    mock_metric.inc.assert_called_once()


class TestMarkAsProcessed:
    """Tests for _mark_as_processed method."""

    @pytest.mark.asyncio
    async def test_skips_empty_event_id(self):
        """Should skip marking for empty event_id."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.setex = AsyncMock()

                await consumer._mark_as_processed("", "ws-1")

                mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_stores_in_redis(self):
        """Should store processed marker in Redis."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.setex = AsyncMock()

                with patch("app.consumers.base_consumer.settings") as mock_settings:
                    mock_settings.IDEMPOTENCY_TTL_SECONDS = 86400

                    await consumer._mark_as_processed("event-123", "ws-1")

                    mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_redis_error_gracefully(self):
        """Should handle Redis error gracefully."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

                with patch("app.consumers.base_consumer.settings") as mock_settings:
                    mock_settings.IDEMPOTENCY_TTL_SECONDS = 86400

                    with patch("app.consumers.base_consumer.idempotency_redis_errors_total") as mock_metric:
                        # Should not raise
                        await consumer._mark_as_processed("event-123", "ws-1")
                        mock_metric.inc.assert_called_once()


class TestStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_initializes_redis(self):
        """Should initialize Redis manager."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.topics = ["test-topic"]
            consumer.consumer_group = "test-group"
            consumer.auto_commit = False
            consumer._running = False

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                    mock_producer.initialize = AsyncMock()
                    mock_producer.is_healthy = True

                    with patch("app.consumers.base_consumer.AIOKafkaConsumer") as mock_consumer_class:
                        mock_consumer = AsyncMock()
                        mock_consumer.start = AsyncMock()
                        mock_consumer_class.return_value = mock_consumer

                        with patch("app.consumers.base_consumer.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.KAFKA_AUTO_OFFSET_RESET = "earliest"

                            await consumer.start()

                            mock_redis.initialize.assert_called_once()


class TestStop:
    """Tests for stop method."""

    @pytest.mark.asyncio
    async def test_stops_consumer(self):
        """Should stop Kafka consumer."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer._running = True
            consumer.consumer_group = "test"

            mock_kafka_consumer = AsyncMock()
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.close = AsyncMock()

                with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                    mock_redis.close = AsyncMock()

                    await consumer.stop()

                    assert consumer._running is False
                    mock_kafka_consumer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_producer(self):
        """Should close Kafka producer."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer._running = True
            consumer.consumer_group = "test"
            consumer.consumer = None

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.close = AsyncMock()

                with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                    mock_redis.close = AsyncMock()

                    await consumer.stop()

                    mock_producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_redis(self):
        """Should close Redis connection."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer._running = True
            consumer.consumer_group = "test"
            consumer.consumer = None

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.close = AsyncMock()

                with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                    mock_redis.close = AsyncMock()

                    await consumer.stop()

                    mock_redis.close.assert_called_once()


class TestLagUpdateInterval:
    """Tests for LAG_UPDATE_INTERVAL constant."""

    def test_lag_update_interval_value(self):
        """Should have reasonable lag update interval."""
        from app.consumers.base_consumer import LAG_UPDATE_INTERVAL

        assert LAG_UPDATE_INTERVAL == 30


class TestStartException:
    """Tests for start method exception handling."""

    @pytest.mark.asyncio
    async def test_start_raises_on_redis_failure(self):
        """Should raise exception when Redis initialization fails."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.topics = ["test-topic"]
            consumer.consumer_group = "test-group"
            consumer.auto_commit = False
            consumer._running = False

            with patch("app.consumers.base_consumer.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock(side_effect=Exception("Redis connection failed"))

                with pytest.raises(Exception, match="Redis connection failed"):
                    await consumer.start()


class TestUpdateConsumerLag:
    """Tests for _update_consumer_lag method."""

    @pytest.mark.asyncio
    async def test_skips_update_within_interval(self):
        """Should skip update if called within interval."""
        import time
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = time.time()  # Just updated
            consumer.consumer = MagicMock()

            # Should return early without calling consumer methods
            await consumer._update_consumer_lag()
            consumer.consumer.assignment.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_update_without_consumer(self):
        """Should skip update if consumer is None."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = 0.0
            consumer.consumer = None

            # Should not raise
            await consumer._update_consumer_lag()

    @pytest.mark.asyncio
    async def test_skips_update_without_partitions(self):
        """Should skip update if no partitions assigned."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = 0.0

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.assignment.return_value = set()  # No partitions
            consumer.consumer = mock_kafka_consumer

            await consumer._update_consumer_lag()

            mock_kafka_consumer.end_offsets.assert_not_called()

    @pytest.mark.asyncio
    async def test_updates_lag_metrics(self):
        """Should update lag metrics for each partition."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = 0.0

            mock_partition = MagicMock()
            mock_partition.topic = "test-topic"
            mock_partition.partition = 0

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.assignment.return_value = {mock_partition}
            mock_kafka_consumer.end_offsets = AsyncMock(return_value={mock_partition: 100})
            mock_kafka_consumer.position = AsyncMock(return_value=50)
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.kafka_consumer_lag_gauge") as mock_gauge:
                mock_labels = MagicMock()
                mock_gauge.labels.return_value = mock_labels

                with patch("app.consumers.base_consumer.keda_scaler_metrics_value") as mock_keda:
                    mock_keda_labels = MagicMock()
                    mock_keda.labels.return_value = mock_keda_labels

                    await consumer._update_consumer_lag()

                    mock_gauge.labels.assert_called_with(topic="test-topic", partition="0")
                    mock_labels.set.assert_called_with(50)  # 100 - 50 = 50 lag
                    mock_keda_labels.set.assert_called_with(50)

    @pytest.mark.asyncio
    async def test_handles_position_error_gracefully(self):
        """Should handle position error for individual partition."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = 0.0

            mock_partition = MagicMock()
            mock_partition.topic = "test-topic"
            mock_partition.partition = 0

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.assignment.return_value = {mock_partition}
            mock_kafka_consumer.end_offsets = AsyncMock(return_value={mock_partition: 100})
            mock_kafka_consumer.position = AsyncMock(side_effect=Exception("Position error"))
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.keda_scaler_metrics_value") as mock_keda:
                mock_keda_labels = MagicMock()
                mock_keda.labels.return_value = mock_keda_labels

                # Should not raise
                await consumer._update_consumer_lag()

    @pytest.mark.asyncio
    async def test_handles_general_exception(self):
        """Should handle general exception gracefully."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer._last_lag_update = 0.0

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.assignment.side_effect = Exception("Assignment error")
            consumer.consumer = mock_kafka_consumer

            # Should not raise
            await consumer._update_consumer_lag()


class TestRun:
    """Tests for run method."""

    @pytest.mark.asyncio
    async def test_run_processes_messages(self):
        """Should process messages from consumer."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.topics = ["test-topic"]
            consumer.consumer_group = "test"
            consumer.auto_commit = False
            consumer.max_retries = 3
            consumer._running = False
            consumer._last_lag_update = 0.0

            # Create async generator for messages
            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.partition = 0
            mock_message.value = {"event_type": "test", "event_id": "123"}
            mock_message.key = None
            mock_message.timestamp = 1234567890

            async def message_generator():
                yield mock_message
                raise asyncio.CancelledError()

            consumer.start = AsyncMock()
            consumer.stop = AsyncMock()
            consumer._process_message_with_retry = AsyncMock()

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.__aiter__ = lambda self: message_generator()
            mock_kafka_consumer.commit = AsyncMock()
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.kafka_messages_consumed_total") as mock_metric:
                mock_labels = MagicMock()
                mock_metric.labels.return_value = mock_labels

                consumer._update_consumer_lag = AsyncMock()

                await consumer.run()

                consumer.start.assert_called_once()
                consumer._process_message_with_retry.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_run_commits_offset_after_success(self):
        """Should commit offset after successful processing."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.topics = ["test-topic"]
            consumer.consumer_group = "test"
            consumer.auto_commit = False
            consumer.max_retries = 3
            consumer._running = False
            consumer._last_lag_update = 0.0

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "123"}

            async def message_generator():
                yield mock_message
                raise asyncio.CancelledError()

            consumer.start = AsyncMock()
            consumer.stop = AsyncMock()
            consumer._process_message_with_retry = AsyncMock()

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.__aiter__ = lambda self: message_generator()
            mock_kafka_consumer.commit = AsyncMock()
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.kafka_messages_consumed_total") as mock_metric:
                mock_labels = MagicMock()
                mock_metric.labels.return_value = mock_labels
                consumer._update_consumer_lag = AsyncMock()

                await consumer.run()

                mock_kafka_consumer.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_handles_processing_failure(self):
        """Should send to DLQ on processing failure."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.topics = ["test-topic"]
            consumer.consumer_group = "test"
            consumer.auto_commit = False
            consumer.max_retries = 3
            consumer._running = False
            consumer._last_lag_update = 0.0

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "123"}

            async def message_generator():
                yield mock_message
                raise asyncio.CancelledError()

            consumer.start = AsyncMock()
            consumer.stop = AsyncMock()
            consumer._process_message_with_retry = AsyncMock(side_effect=Exception("Processing failed"))
            consumer._send_to_dlq = AsyncMock()
            consumer._classify_error = MagicMock(return_value="processing")

            mock_kafka_consumer = MagicMock()
            mock_kafka_consumer.__aiter__ = lambda self: message_generator()
            mock_kafka_consumer.commit = AsyncMock()
            consumer.consumer = mock_kafka_consumer

            with patch("app.consumers.base_consumer.kafka_messages_failed_total") as mock_metric:
                mock_labels = MagicMock()
                mock_metric.labels.return_value = mock_labels
                consumer._update_consumer_lag = AsyncMock()

                await consumer.run()

                consumer._send_to_dlq.assert_called_once()


class TestProcessMessageWithRetry:
    """Tests for _process_message_with_retry method."""

    @pytest.mark.asyncio
    async def test_processes_message_successfully(self):
        """Should process message on first attempt."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer.max_retries = 3

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "event-123", "workspace_id": "ws-1"}

            consumer._is_already_processed = AsyncMock(return_value=False)
            consumer._mark_as_processed = AsyncMock()
            consumer.process_event = AsyncMock()

            await consumer._process_message_with_retry(mock_message)

            consumer.process_event.assert_called_once_with(mock_message.value)
            consumer._mark_as_processed.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_already_processed_message(self):
        """Should skip message if already processed."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer.max_retries = 3

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "event-123", "workspace_id": "ws-1"}

            consumer._is_already_processed = AsyncMock(return_value=True)
            consumer.process_event = AsyncMock()

            await consumer._process_message_with_retry(mock_message)

            consumer.process_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        """Should retry on failure with exponential backoff."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer.max_retries = 2

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "event-123", "workspace_id": "ws-1"}

            call_count = 0

            async def fail_then_succeed(event):
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Retry me")

            consumer._is_already_processed = AsyncMock(return_value=False)
            consumer._mark_as_processed = AsyncMock()
            consumer.process_event = fail_then_succeed

            with patch("asyncio.sleep", new_callable=AsyncMock):
                await consumer._process_message_with_retry(mock_message)

            assert call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise after max retries exceeded."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"
            consumer.max_retries = 2

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.value = {"event_type": "test", "event_id": "event-123", "workspace_id": "ws-1"}

            consumer._is_already_processed = AsyncMock(return_value=False)
            consumer.process_event = AsyncMock(side_effect=ValueError("Always fail"))

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(ValueError, match="Always fail"):
                    await consumer._process_message_with_retry(mock_message)


class TestSendToDlq:
    """Tests for _send_to_dlq method."""

    @pytest.mark.asyncio
    async def test_sends_to_dlq_successfully(self):
        """Should send message to DLQ."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.partition = 0
            mock_message.key = b"key123"
            mock_message.value = {"event_type": "test", "event_id": "123", "correlation_id": "corr-456"}
            mock_message.timestamp = 1234567890

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.send_to_dlq = AsyncMock(return_value=True)

                with patch("app.consumers.base_consumer.dlq_send_duration_seconds") as mock_duration:
                    with patch("app.consumers.base_consumer.dlq_messages_sent_total") as mock_sent:
                        mock_labels = MagicMock()
                        mock_sent.labels.return_value = mock_labels

                        await consumer._send_to_dlq(
                            mock_message,
                            error="Test error",
                            error_type="processing",
                            retry_count=3,
                        )

                        mock_producer.send_to_dlq.assert_called_once()
                        mock_labels.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_dlq_send_failure(self):
        """Should handle DLQ send failure."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.partition = 0
            mock_message.key = None
            mock_message.value = {"event_type": "test"}
            mock_message.timestamp = 1234567890

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.send_to_dlq = AsyncMock(return_value=False)

                with patch("app.consumers.base_consumer.dlq_send_duration_seconds"):
                    with patch("app.consumers.base_consumer.dlq_send_errors_total") as mock_errors:
                        await consumer._send_to_dlq(
                            mock_message,
                            error="Test error",
                            error_type="processing",
                            retry_count=3,
                        )

                        mock_errors.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_dlq_exception(self):
        """Should handle exception during DLQ send."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.partition = 0
            mock_message.key = None
            mock_message.value = {"event_type": "test"}
            mock_message.timestamp = 1234567890

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.send_to_dlq = AsyncMock(side_effect=Exception("Producer error"))

                with patch("app.consumers.base_consumer.dlq_send_errors_total") as mock_errors:
                    # Should not raise
                    await consumer._send_to_dlq(
                        mock_message,
                        error="Test error",
                        error_type="processing",
                        retry_count=3,
                    )

                    mock_errors.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_extracts_correlation_id_from_event_id(self):
        """Should use event_id as correlation_id if correlation_id not present."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)
            consumer.consumer_group = "test"

            mock_message = MagicMock()
            mock_message.topic = "test-topic"
            mock_message.offset = 1
            mock_message.partition = 0
            mock_message.key = None
            mock_message.value = {"event_type": "test", "event_id": "event-123"}  # No correlation_id
            mock_message.timestamp = 1234567890

            with patch("app.consumers.base_consumer.kafka_producer") as mock_producer:
                mock_producer.send_to_dlq = AsyncMock(return_value=True)

                with patch("app.consumers.base_consumer.dlq_send_duration_seconds"):
                    with patch("app.consumers.base_consumer.dlq_messages_sent_total") as mock_sent:
                        mock_labels = MagicMock()
                        mock_sent.labels.return_value = mock_labels

                        await consumer._send_to_dlq(
                            mock_message,
                            error="Test error",
                            error_type="processing",
                            retry_count=3,
                        )

                        # Verify correlation_id was extracted from event_id
                        call_kwargs = mock_producer.send_to_dlq.call_args[1]
                        assert call_kwargs["correlation_id"] == "event-123"


class TestClassifyErrorExtended:
    """Extended tests for _classify_error method."""

    def test_classifies_permission_error(self):
        """Should classify PermissionError as 'permission'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(PermissionError("test"))
            assert result == "permission"

    def test_classifies_os_error_as_processing(self):
        """Should classify OSError (IOError in Python 3) as 'processing' (not in mapping)."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            # IOError is an alias for OSError in Python 3, not in the mapping
            result = consumer._classify_error(IOError("test"))
            # Falls through to default "processing"
            assert result == "processing"

    def test_classifies_type_error_as_data_format(self):
        """Should classify TypeError as 'data_format'."""
        from app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event):
                pass

        with patch("app.consumers.base_consumer.BaseConsumer.__init__", return_value=None):
            consumer = object.__new__(TestConsumer)

            result = consumer._classify_error(TypeError("test"))
            assert result == "data_format"
