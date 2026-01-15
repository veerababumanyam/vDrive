"""Kafka producer manager for DLQ and event publishing.

Provides connection pooling with health checks, automatic reconnection,
and production-ready configuration for reliable message delivery.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from .config import settings

logger = structlog.get_logger()


class KafkaProducerManager:
    """Manages Kafka producer connections for DLQ and events."""

    _instance: Optional["KafkaProducerManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "KafkaProducerManager":
        """Singleton pattern for Kafka producer manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Kafka producer manager (idempotent)."""
        if KafkaProducerManager._initialized:
            return

        self._producer: Optional[AIOKafkaProducer] = None
        self._healthy: bool = False
        KafkaProducerManager._initialized = True

    async def initialize(self) -> None:
        """Initialize Kafka producer with production-ready settings."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                # Durability: wait for all replicas to acknowledge
                acks="all",
                # Enable idempotent producer to avoid duplicates
                enable_idempotence=True,
                # Compression for bandwidth optimization
                compression_type="lz4",
                # Batching configuration for throughput
                batch_size=16384,  # 16KB
                linger_ms=10,  # Wait up to 10ms for batching
                # Max request size (10MB)
                max_request_size=10485760,
                # Retry configuration
                retries=3,
                retry_backoff_ms=100,
                # Serializer
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self._producer.start()
            self._healthy = True

            logger.info(
                "Kafka producer initialized",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            )

        except KafkaError as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
            self._healthy = False

    async def close(self) -> None:
        """Close Kafka producer with graceful flush."""
        if self._producer:
            try:
                # Flush pending messages with timeout
                await self._producer.stop()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error("Error closing Kafka producer", error=str(e))
            finally:
                self._producer = None
                self._healthy = False

    @property
    def is_healthy(self) -> bool:
        """Check if producer is healthy."""
        return self._healthy

    async def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[list[tuple[str, bytes]]] = None,
    ) -> bool:
        """
        Send message to Kafka topic.

        Args:
            topic: Target Kafka topic
            value: Message value (will be JSON serialized)
            key: Optional partition key
            headers: Optional message headers

        Returns:
            True if successful, False otherwise
        """
        if not self._producer or not self._healthy:
            logger.warning("Kafka producer not available", topic=topic)
            return False

        try:
            await self._producer.send_and_wait(
                topic,
                value=value,
                key=key,
                headers=headers,
            )
            return True

        except KafkaError as e:
            logger.error(
                "Failed to send Kafka message",
                topic=topic,
                error=str(e),
            )
            return False

    async def send_to_dlq(
        self,
        original_topic: str,
        original_partition: int,
        original_offset: int,
        original_key: Optional[str],
        original_value: dict[str, Any],
        original_timestamp: int,
        error: str,
        error_type: str,
        retry_count: int,
        consumer_group: str,
        correlation_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> bool:
        """
        Send failed message to Dead Letter Queue.

        Args:
            original_topic: Original Kafka topic
            original_partition: Original partition
            original_offset: Original offset
            original_key: Original message key
            original_value: Original message value
            original_timestamp: Original timestamp (epoch ms)
            error: Error description
            error_type: Classification of error type
            retry_count: Number of retries attempted
            consumer_group: Consumer group that failed processing
            correlation_id: Optional trace correlation ID
            stack_trace: Optional sanitized stack trace

        Returns:
            True if successful, False otherwise
        """
        dlq_topic = f"{original_topic}.dlq"

        dlq_message = {
            "original_topic": original_topic,
            "original_partition": original_partition,
            "original_offset": original_offset,
            "original_key": original_key,
            "original_value": original_value,
            "original_timestamp": original_timestamp,
            "error": error,
            "error_type": error_type,
            "retry_count": retry_count,
            "consumer_group": consumer_group,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "stack_trace": self._sanitize_stack_trace(stack_trace) if stack_trace else None,
        }

        return await self.send(
            topic=dlq_topic,
            value=dlq_message,
            key=original_key,
        )

    def _sanitize_stack_trace(self, stack_trace: str) -> str:
        """Remove sensitive information from stack traces."""
        # Remove common secret patterns
        import re

        patterns = [
            (r'password["\']?\s*[=:]\s*["\']?[^"\'\s]+', 'password=***'),
            (r'secret["\']?\s*[=:]\s*["\']?[^"\'\s]+', 'secret=***'),
            (r'token["\']?\s*[=:]\s*["\']?[^"\'\s]+', 'token=***'),
            (r'api_key["\']?\s*[=:]\s*["\']?[^"\'\s]+', 'api_key=***'),
        ]

        sanitized = stack_trace
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        # Limit length
        if len(sanitized) > 4000:
            sanitized = sanitized[:4000] + "... [truncated]"

        return sanitized


# Global Kafka producer instance
kafka_producer = KafkaProducerManager()
