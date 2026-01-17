"""Unit tests for main.py FastAPI application."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_function_exists(self):
        """Health function should exist."""
        from app.main import health

        assert asyncio.iscoroutinefunction(health)

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self):
        """Should return healthy status."""
        with patch("app.main._startup_time", 1000.0):
            with patch("app.main.time") as mock_time:
                mock_time.time.return_value = 1100.0

                with patch("app.main.service_uptime_seconds") as mock_metric:
                    from app.main import health

                    result = await health()

                    assert result["status"] == "healthy"
                    assert "uptime_seconds" in result
                    mock_metric.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_handles_zero_startup_time(self):
        """Should handle zero startup time."""
        with patch("app.main._startup_time", 0.0):
            with patch("app.main.time") as mock_time:
                mock_time.time.return_value = 1000.0

                with patch("app.main.service_uptime_seconds"):
                    from app.main import health

                    result = await health()

                    assert result["uptime_seconds"] == 0


class TestHealthCheckHelpers:
    """Tests for health check helper functions."""

    @pytest.mark.asyncio
    async def test_check_with_timeout_success(self):
        """Should return result on success."""
        from app.main import _check_with_timeout

        async def success_check():
            return "ok"

        name, result = await _check_with_timeout("test", success_check(), 5.0)
        assert name == "test"
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_check_with_timeout_timeout(self):
        """Should return timeout on timeout."""
        from app.main import _check_with_timeout

        async def slow_check():
            await asyncio.sleep(10)
            return "ok"

        name, result = await _check_with_timeout("test", slow_check(), 0.01)
        assert name == "test"
        assert result == "timeout"

    @pytest.mark.asyncio
    async def test_check_with_timeout_error(self):
        """Should return error message on exception."""
        from app.main import _check_with_timeout

        async def error_check():
            raise ValueError("test error message")

        name, result = await _check_with_timeout("test", error_check(), 5.0)
        assert name == "test"
        assert "error:" in result
        assert "test error" in result


class TestDatabaseCheck:
    """Tests for database health check."""

    def test_check_database_function_exists(self):
        """Database check function should exist."""
        from app.main import _check_database

        assert asyncio.iscoroutinefunction(_check_database)

    @pytest.mark.asyncio
    async def test_check_database_success(self):
        """Should return ok when database is healthy."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            from app.main import _check_database

            result = await _check_database()

            assert result == "ok"
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_raises_on_error(self):
        """Should raise on database error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            from app.main import _check_database

            with pytest.raises(Exception, match="Connection failed"):
                await _check_database()


class TestRedisCheck:
    """Tests for Redis health check."""

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self):
        """Should return ok when Redis is healthy."""
        with patch("app.main.redis_manager") as mock_redis:
            mock_redis.health_check = AsyncMock(return_value=True)

            from app.main import _check_redis
            result = await _check_redis()
            assert result == "ok"

    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self):
        """Should return unhealthy when Redis check fails."""
        with patch("app.main.redis_manager") as mock_redis:
            mock_redis.health_check = AsyncMock(return_value=False)

            from app.main import _check_redis
            result = await _check_redis()
            assert result == "unhealthy"


class TestKafkaCheck:
    """Tests for Kafka health check."""

    def test_check_kafka_function_exists(self):
        """Kafka check function should exist."""
        from app.main import _check_kafka

        assert asyncio.iscoroutinefunction(_check_kafka)

    @pytest.mark.asyncio
    async def test_check_kafka_success(self):
        """Should return ok when Kafka is healthy."""
        mock_consumer = AsyncMock()

        with patch("aiokafka.AIOKafkaConsumer", return_value=mock_consumer):
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

                from app.main import _check_kafka

                result = await _check_kafka()

                assert result == "ok"
                mock_consumer.start.assert_called_once()
                mock_consumer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_kafka_raises_on_error(self):
        """Should raise on Kafka error."""
        mock_consumer = AsyncMock()
        mock_consumer.start.side_effect = Exception("Kafka unreachable")

        with patch("aiokafka.AIOKafkaConsumer", return_value=mock_consumer):
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

                from app.main import _check_kafka

                with pytest.raises(Exception, match="Kafka unreachable"):
                    await _check_kafka()


class TestR2Check:
    """Tests for R2 storage health check."""

    @pytest.mark.asyncio
    async def test_check_r2_success(self):
        """Should return ok when R2 is healthy."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("botocore.config.Config"):
                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.R2_ENDPOINT = "https://r2.example.com"
                    mock_settings.R2_ACCESS_KEY_ID = "test-key"
                    mock_settings.R2_SECRET_ACCESS_KEY = "test-secret"
                    mock_settings.R2_BUCKET_NAME = "test-bucket"

                    from app.main import _check_r2

                    result = await _check_r2()

                    assert result == "ok"
                    mock_client.head_bucket.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_r2_raises_on_error(self):
        """Should raise on R2 error."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = Exception("Bucket not found")

        with patch("boto3.client", return_value=mock_client):
            with patch("botocore.config.Config"):
                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.R2_ENDPOINT = "https://r2.example.com"
                    mock_settings.R2_ACCESS_KEY_ID = "test-key"
                    mock_settings.R2_SECRET_ACCESS_KEY = "test-secret"
                    mock_settings.R2_BUCKET_NAME = "test-bucket"

                    from app.main import _check_r2

                    with pytest.raises(Exception, match="Bucket not found"):
                        await _check_r2()


class TestGCVCheck:
    """Tests for Google Cloud Vision check."""

    @pytest.mark.asyncio
    async def test_check_gcv_disabled(self):
        """Should return disabled when GCV is disabled."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

            from app.main import _check_gcv
            result = await _check_gcv()
            assert result == "disabled"

    @pytest.mark.asyncio
    async def test_check_gcv_enabled_success(self):
        """Should return ok when GCV client initializes."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = True

            with patch("google.cloud.vision.ImageAnnotatorClient"):
                from app.main import _check_gcv
                result = await _check_gcv()
                assert result == "ok"


class TestSignalHandlers:
    """Tests for signal handlers."""

    def test_setup_signal_handlers(self):
        """Should register signal handlers."""
        from app.main import _setup_signal_handlers, _consumer_tasks

        loop = MagicMock()
        _setup_signal_handlers(loop)

        # Should have registered handlers for SIGTERM and SIGINT
        assert loop.add_signal_handler.call_count == 2


class TestValidateDependencies:
    """Tests for dependency validation."""

    def test_validate_dependencies_function_exists(self):
        """Validate dependencies function should exist."""
        from app.main import _validate_dependencies

        assert asyncio.iscoroutinefunction(_validate_dependencies)


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_function_exists(self):
        """Metrics function should exist."""
        from app.main import metrics

        assert asyncio.iscoroutinefunction(metrics)

    @pytest.mark.asyncio
    async def test_metrics_returns_prometheus_format(self):
        """Should return Prometheus metrics."""
        with patch("app.main.generate_latest") as mock_generate:
            mock_generate.return_value = b"# HELP test_metric Test\n"

            from app.main import metrics

            result = await metrics()

            assert result.body == b"# HELP test_metric Test\n"
            mock_generate.assert_called_once()


class TestReadyEndpoint:
    """Tests for /ready endpoint."""

    @pytest.mark.asyncio
    async def test_ready_returns_ready_when_all_ok(self):
        """Should return ready when all dependencies healthy."""
        with patch("app.main._check_with_timeout") as mock_check:
            mock_check.side_effect = [
                ("database", "ok"),
                ("redis", "ok"),
                ("kafka", "ok"),
                ("r2_storage", "ok"),
                ("gcv", "ok"),
            ]

            with patch("app.main._consumer_tasks", []):
                with patch("app.main.settings") as mock_settings:
                    mock_settings.SERVICE_NAME = "processing-service"

                    from app.main import ready

                    result = await ready()

                    assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_database_unhealthy(self):
        """Should return 503 when database is unhealthy."""
        with patch("app.main._check_with_timeout") as mock_check:
            mock_check.side_effect = [
                ("database", "error: connection refused"),
                ("redis", "ok"),
                ("kafka", "ok"),
                ("r2_storage", "ok"),
                ("gcv", "ok"),
            ]

            with patch("app.main._consumer_tasks", []):
                with patch("app.main.settings") as mock_settings:
                    mock_settings.SERVICE_NAME = "processing-service"

                    from app.main import ready

                    result = await ready()

                    assert result.status_code == 503

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_kafka_unhealthy(self):
        """Should return 503 when Kafka is unhealthy."""
        with patch("app.main._check_with_timeout") as mock_check:
            mock_check.side_effect = [
                ("database", "ok"),
                ("redis", "ok"),
                ("kafka", "timeout"),
                ("r2_storage", "ok"),
                ("gcv", "ok"),
            ]

            with patch("app.main._consumer_tasks", []):
                with patch("app.main.settings") as mock_settings:
                    mock_settings.SERVICE_NAME = "processing-service"

                    from app.main import ready

                    result = await ready()

                    assert result.status_code == 503

    @pytest.mark.asyncio
    async def test_ready_checks_consumer_status(self):
        """Should check consumer task status."""
        mock_task = MagicMock()
        mock_task.done.return_value = False

        with patch("app.main._check_with_timeout") as mock_check:
            mock_check.side_effect = [
                ("database", "ok"),
                ("redis", "ok"),
                ("kafka", "ok"),
                ("r2_storage", "ok"),
                ("gcv", "ok"),
            ]

            with patch("app.main._consumer_tasks", [mock_task]):
                with patch("app.main.settings") as mock_settings:
                    mock_settings.SERVICE_NAME = "processing-service"

                    from app.main import ready

                    result = await ready()

                    assert result.status_code == 200


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_exists(self):
        """FastAPI app should exist."""
        from app.main import app

        assert app is not None
        assert app.title == "vDrive Processing Service"

    def test_lifespan_function_exists(self):
        """Lifespan function should exist."""
        from app.main import lifespan

        # Should be an async context manager
        assert callable(lifespan)


class TestValidateDependenciesFull:
    """Full tests for _validate_dependencies function."""

    @pytest.mark.asyncio
    async def test_validate_dependencies_postgresql_success(self):
        """Should return ok for postgresql when healthy."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("app.main.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.R2_ENDPOINT = "https://r2.example.com"
                            mock_settings.R2_ACCESS_KEY_ID = "key"
                            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                            mock_settings.R2_BUCKET_NAME = "bucket"
                            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                            from app.main import _validate_dependencies
                            result = await _validate_dependencies()

                            assert result["postgresql"] == "ok"

    @pytest.mark.asyncio
    async def test_validate_dependencies_postgresql_error(self):
        """Should return error for postgresql when unhealthy."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("app.main.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.R2_ENDPOINT = "https://r2.example.com"
                            mock_settings.R2_ACCESS_KEY_ID = "key"
                            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                            mock_settings.R2_BUCKET_NAME = "bucket"
                            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                            from app.main import _validate_dependencies
                            result = await _validate_dependencies()

                            assert "error" in result["postgresql"]

    @pytest.mark.asyncio
    async def test_validate_dependencies_redis_unhealthy(self):
        """Should return unhealthy for redis when not healthy."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = False

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("app.main.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.R2_ENDPOINT = "https://r2.example.com"
                            mock_settings.R2_ACCESS_KEY_ID = "key"
                            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                            mock_settings.R2_BUCKET_NAME = "bucket"
                            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                            from app.main import _validate_dependencies
                            result = await _validate_dependencies()

                            assert result["redis"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_validate_dependencies_redis_error(self):
        """Should return error for redis on exception."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock(side_effect=Exception("Redis error"))

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("app.main.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.R2_ENDPOINT = "https://r2.example.com"
                            mock_settings.R2_ACCESS_KEY_ID = "key"
                            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                            mock_settings.R2_BUCKET_NAME = "bucket"
                            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                            from app.main import _validate_dependencies
                            result = await _validate_dependencies()

                            assert "error" in result["redis"]

    @pytest.mark.asyncio
    async def test_validate_dependencies_kafka_timeout(self):
        """Should return timeout for kafka on timeout."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer.start = AsyncMock(side_effect=asyncio.TimeoutError())
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                        with patch("boto3.client") as mock_boto:
                            mock_s3 = MagicMock()
                            mock_boto.return_value = mock_s3

                            with patch("app.main.settings") as mock_settings:
                                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                                mock_settings.R2_ENDPOINT = "https://r2.example.com"
                                mock_settings.R2_ACCESS_KEY_ID = "key"
                                mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                                mock_settings.R2_BUCKET_NAME = "bucket"
                                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                                from app.main import _validate_dependencies
                                result = await _validate_dependencies()

                                assert result["kafka"] == "timeout"

    @pytest.mark.asyncio
    async def test_validate_dependencies_kafka_error(self):
        """Should return error for kafka on exception."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer.start.side_effect = Exception("Kafka error")
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("asyncio.wait_for", side_effect=Exception("Kafka error")):
                        with patch("boto3.client") as mock_boto:
                            mock_s3 = MagicMock()
                            mock_boto.return_value = mock_s3

                            with patch("app.main.settings") as mock_settings:
                                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                                mock_settings.R2_ENDPOINT = "https://r2.example.com"
                                mock_settings.R2_ACCESS_KEY_ID = "key"
                                mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                                mock_settings.R2_BUCKET_NAME = "bucket"
                                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                                from app.main import _validate_dependencies
                                result = await _validate_dependencies()

                                assert "error" in result["kafka"]

    @pytest.mark.asyncio
    async def test_validate_dependencies_r2_error(self):
        """Should return error for r2 on exception."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_s3.head_bucket.side_effect = Exception("Bucket error")
                        mock_boto.return_value = mock_s3

                        with patch("app.main.settings") as mock_settings:
                            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                            mock_settings.R2_ENDPOINT = "https://r2.example.com"
                            mock_settings.R2_ACCESS_KEY_ID = "key"
                            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                            mock_settings.R2_BUCKET_NAME = "bucket"
                            mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False

                            from app.main import _validate_dependencies
                            result = await _validate_dependencies()

                            assert "error" in result["r2_storage"]

    @pytest.mark.asyncio
    async def test_validate_dependencies_gcv_enabled_success(self):
        """Should return ok for gcv when enabled and successful."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("google.cloud.vision.ImageAnnotatorClient"):
                            with patch("app.main.settings") as mock_settings:
                                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                                mock_settings.R2_ENDPOINT = "https://r2.example.com"
                                mock_settings.R2_ACCESS_KEY_ID = "key"
                                mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                                mock_settings.R2_BUCKET_NAME = "bucket"
                                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = True

                                from app.main import _validate_dependencies
                                result = await _validate_dependencies()

                                assert result["gcv"] == "ok"

    @pytest.mark.asyncio
    async def test_validate_dependencies_gcv_error(self):
        """Should return error for gcv on exception."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_connect():
            yield mock_conn

        mock_engine.connect = mock_connect

        with patch("app.core.database.engine", mock_engine):
            with patch("app.main.redis_manager") as mock_redis:
                mock_redis.initialize = AsyncMock()
                mock_redis.is_healthy = True

                with patch("aiokafka.AIOKafkaConsumer") as mock_consumer_cls:
                    mock_consumer = AsyncMock()
                    mock_consumer_cls.return_value = mock_consumer

                    with patch("boto3.client") as mock_boto:
                        mock_s3 = MagicMock()
                        mock_boto.return_value = mock_s3

                        with patch("google.cloud.vision.ImageAnnotatorClient", side_effect=Exception("GCV error")):
                            with patch("app.main.settings") as mock_settings:
                                mock_settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
                                mock_settings.R2_ENDPOINT = "https://r2.example.com"
                                mock_settings.R2_ACCESS_KEY_ID = "key"
                                mock_settings.R2_SECRET_ACCESS_KEY = "secret"
                                mock_settings.R2_BUCKET_NAME = "bucket"
                                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = True

                                from app.main import _validate_dependencies
                                result = await _validate_dependencies()

                                assert "error" in result["gcv"]


class TestSignalHandlerInvocation:
    """Tests for signal handler invocation."""

    def test_signal_handler_cancels_tasks(self):
        """Signal handler should cancel consumer tasks."""
        import app.main as main_module

        # Reset state
        main_module._shutdown_in_progress = False
        main_module._consumer_tasks = []

        # Create mock task
        mock_task = MagicMock()
        mock_task.done.return_value = False
        main_module._consumer_tasks.append(mock_task)

        # Setup signal handlers
        mock_loop = MagicMock()
        main_module._setup_signal_handlers(mock_loop)

        # Get the handler function that was registered
        handler_call = mock_loop.add_signal_handler.call_args_list[0]
        handler_fn = handler_call[0][1]

        # Invoke the handler
        handler_fn()

        # Task should be cancelled
        mock_task.cancel.assert_called_once()
        assert main_module._shutdown_in_progress is True

    def test_signal_handler_ignores_second_signal(self):
        """Second signal should be ignored during shutdown."""
        import app.main as main_module

        # Set shutdown in progress
        main_module._shutdown_in_progress = True

        mock_task = MagicMock()
        mock_task.done.return_value = False
        main_module._consumer_tasks = [mock_task]

        # Setup signal handlers
        mock_loop = MagicMock()
        main_module._setup_signal_handlers(mock_loop)

        # Get the handler function
        handler_call = mock_loop.add_signal_handler.call_args_list[0]
        handler_fn = handler_call[0][1]

        # Reset mock to check no cancel is called
        mock_task.reset_mock()

        # Invoke the handler again
        handler_fn()

        # Task should NOT be cancelled again
        mock_task.cancel.assert_not_called()

    def test_signal_handler_skips_done_tasks(self):
        """Signal handler should skip already done tasks."""
        import app.main as main_module

        main_module._shutdown_in_progress = False
        main_module._consumer_tasks = []

        mock_task = MagicMock()
        mock_task.done.return_value = True  # Task already done
        main_module._consumer_tasks.append(mock_task)

        mock_loop = MagicMock()
        main_module._setup_signal_handlers(mock_loop)

        handler_call = mock_loop.add_signal_handler.call_args_list[0]
        handler_fn = handler_call[0][1]

        handler_fn()

        # Should not cancel already done task
        mock_task.cancel.assert_not_called()


class TestReadyEndpointWithFailedConsumers:
    """Test ready endpoint with consumer failures."""

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_all_consumers_done(self):
        """Should return 503 when all consumer tasks are done/failed."""
        mock_task = MagicMock()
        mock_task.done.return_value = True  # Consumer has crashed

        with patch("app.main._check_with_timeout") as mock_check:
            mock_check.side_effect = [
                ("database", "ok"),
                ("redis", "ok"),
                ("kafka", "ok"),
                ("r2_storage", "ok"),
                ("gcv", "ok"),
            ]

            with patch("app.main._consumer_tasks", [mock_task]):
                with patch("app.main.settings") as mock_settings:
                    mock_settings.SERVICE_NAME = "processing-service"

                    from app.main import ready

                    result = await ready()

                    # Should be 503 because no active consumers
                    assert result.status_code == 503
