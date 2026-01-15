"""Base Kafka consumer with retry, idempotency, and DLQ logic."""

import asyncio
import json
import time
import traceback
from abc import ABC, abstractmethod
from typing import Optional

import structlog
from aiokafka import AIOKafkaConsumer, ConsumerRecord

from ..core.config import settings
from ..core.kafka_producer import kafka_producer
from ..core.metrics import (
    dlq_messages_sent_total,
    dlq_send_duration_seconds,
    dlq_send_errors_total,
    idempotency_check_duration_seconds,
    idempotency_check_total,
    idempotency_redis_errors_total,
    kafka_messages_consumed_total,
    kafka_messages_failed_total,
)
from ..core.redis import redis_manager

logger = structlog.get_logger()


class BaseConsumer(ABC):
    """Base class for Kafka consumers with retry, idempotency, and DLQ support."""

    def __init__(
        self,
        topics: list[str],
        consumer_group: str,
        max_retries: int = 3,
        auto_commit: bool = False,
    ):
        """
        Initialize base consumer.

        Args:
            topics: List of Kafka topics to consume from
            consumer_group: Consumer group ID
            max_retries: Maximum number of retry attempts
            auto_commit: Whether to auto-commit offsets (default: manual)
        """
        self.topics = topics
        self.consumer_group = consumer_group
        self.max_retries = max_retries
        self.auto_commit = auto_commit
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self):
        """Start the Kafka consumer and initialize dependencies."""
        try:
            # Initialize Redis for idempotency
            await redis_manager.initialize()

            # Initialize Kafka producer for DLQ
            await kafka_producer.initialize()

            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.consumer_group,
                enable_auto_commit=self.auto_commit,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
            await self.consumer.start()
            self._running = True

            logger.info(
                "Kafka consumer started",
                topics=self.topics,
                consumer_group=self.consumer_group,
                redis_healthy=redis_manager.is_healthy,
                producer_healthy=kafka_producer.is_healthy,
            )

        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise

    async def stop(self):
        """Stop the Kafka consumer and cleanup resources."""
        self._running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped", consumer_group=self.consumer_group)

        # Cleanup Kafka producer
        await kafka_producer.close()

        # Cleanup Redis
        await redis_manager.close()

    async def run(self):
        """Main consumer loop."""
        await self.start()

        try:
            async for message in self.consumer:
                try:
                    await self._process_message_with_retry(message)

                    # Manually commit offset after successful processing
                    if not self.auto_commit:
                        await self.consumer.commit()

                    kafka_messages_consumed_total.labels(
                        topic=message.topic,
                        consumer_group=self.consumer_group,
                    ).inc()

                except Exception as e:
                    error_type = self._classify_error(e)

                    logger.error(
                        "Fatal error processing message",
                        topic=message.topic,
                        offset=message.offset,
                        error=str(e),
                        error_type=error_type,
                    )

                    kafka_messages_failed_total.labels(
                        topic=message.topic,
                        error_type=error_type,
                    ).inc()

                    # Send to DLQ
                    await self._send_to_dlq(
                        message,
                        error=str(e),
                        error_type=error_type,
                        retry_count=self.max_retries,
                    )

                    # Commit offset to avoid reprocessing
                    if not self.auto_commit:
                        await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("Consumer cancelled", consumer_group=self.consumer_group)
        finally:
            await self.stop()

    async def _process_message_with_retry(self, message: ConsumerRecord):
        """
        Process message with exponential backoff retry.

        Args:
            message: Kafka message record
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # Extract event data
                event = message.value
                event_type = event.get("event_type")
                event_id = event.get("event_id")
                workspace_id = event.get("workspace_id")

                logger.debug(
                    "Processing Kafka message",
                    topic=message.topic,
                    offset=message.offset,
                    event_type=event_type,
                    event_id=event_id,
                    workspace_id=workspace_id,
                    retry_count=retry_count,
                )

                # Check idempotency (avoid duplicate processing)
                if await self._is_already_processed(event_id, workspace_id):
                    logger.info(
                        "Message already processed (idempotent skip)",
                        event_id=event_id,
                        workspace_id=workspace_id,
                    )
                    return

                # Call abstract process_event method
                await self.process_event(event)

                # Mark as processed
                await self._mark_as_processed(event_id, workspace_id)

                logger.info(
                    "Message processed successfully",
                    topic=message.topic,
                    event_type=event_type,
                    event_id=event_id,
                )

                return  # Success - exit retry loop

            except Exception as e:
                retry_count += 1

                if retry_count > self.max_retries:
                    logger.error(
                        "Max retries exceeded",
                        topic=message.topic,
                        offset=message.offset,
                        retry_count=retry_count,
                        error=str(e),
                    )
                    raise  # Bubble up to send to DLQ

                # Exponential backoff with jitter
                backoff_seconds = (2**retry_count) + (asyncio.get_event_loop().time() % 1)
                logger.warning(
                    "Retrying message after error",
                    topic=message.topic,
                    offset=message.offset,
                    retry_count=retry_count,
                    backoff_seconds=round(backoff_seconds, 2),
                    error=str(e),
                )

                await asyncio.sleep(backoff_seconds)

    async def _is_already_processed(
        self, event_id: str, workspace_id: Optional[str] = None
    ) -> bool:
        """
        Check if event has already been processed (idempotency).

        Uses Redis with workspace-scoped keys for tenant isolation.

        Args:
            event_id: Unique event identifier
            workspace_id: Optional workspace ID for tenant isolation

        Returns:
            True if already processed, False otherwise
        """
        if not event_id:
            return False

        start_time = time.time()
        key = self._idempotency_key(event_id, workspace_id)

        try:
            exists = await redis_manager.exists(key)
            duration = time.time() - start_time

            idempotency_check_duration_seconds.observe(duration)
            idempotency_check_total.labels(result="hit" if exists else "miss").inc()

            return exists

        except Exception as e:
            logger.warning(
                "Idempotency check failed, allowing processing",
                event_id=event_id,
                error=str(e),
            )
            idempotency_redis_errors_total.inc()
            # Graceful degradation: allow processing if Redis fails
            return False

    async def _mark_as_processed(
        self, event_id: str, workspace_id: Optional[str] = None
    ) -> None:
        """
        Mark event as processed (idempotency tracking).

        Stores event_id in Redis with configurable TTL (default 24 hours).

        Args:
            event_id: Unique event identifier
            workspace_id: Optional workspace ID for tenant isolation
        """
        if not event_id:
            return

        key = self._idempotency_key(event_id, workspace_id)
        value = json.dumps({
            "processed_at": time.time(),
            "consumer_group": self.consumer_group,
        })

        try:
            await redis_manager.setex(
                key=key,
                ttl=settings.IDEMPOTENCY_TTL_SECONDS,
                value=value,
            )
        except Exception as e:
            logger.warning(
                "Failed to mark as processed, continuing",
                event_id=event_id,
                error=str(e),
            )
            idempotency_redis_errors_total.inc()

    def _idempotency_key(
        self, event_id: str, workspace_id: Optional[str] = None
    ) -> str:
        """
        Generate idempotency Redis key.

        Args:
            event_id: Unique event identifier
            workspace_id: Optional workspace ID for tenant isolation

        Returns:
            Redis key string
        """
        if workspace_id:
            return f"processing:idempotent:{workspace_id}:{event_id}"
        return f"processing:idempotent:{event_id}"

    async def _send_to_dlq(
        self,
        message: ConsumerRecord,
        error: str,
        error_type: str,
        retry_count: int,
    ) -> None:
        """
        Send failed message to Dead Letter Queue.

        Args:
            message: Original Kafka message
            error: Error description
            error_type: Classification of error type
            retry_count: Number of retries attempted
        """
        start_time = time.time()

        try:
            # Extract correlation_id if available
            event = message.value if isinstance(message.value, dict) else {}
            correlation_id = event.get("correlation_id") or event.get("event_id")

            # Get stack trace
            stack_trace = traceback.format_exc()

            success = await kafka_producer.send_to_dlq(
                original_topic=message.topic,
                original_partition=message.partition,
                original_offset=message.offset,
                original_key=message.key.decode("utf-8") if message.key else None,
                original_value=message.value,
                original_timestamp=message.timestamp,
                error=error,
                error_type=error_type,
                retry_count=retry_count,
                consumer_group=self.consumer_group,
                correlation_id=correlation_id,
                stack_trace=stack_trace,
            )

            duration = time.time() - start_time
            dlq_send_duration_seconds.observe(duration)

            if success:
                dlq_messages_sent_total.labels(
                    topic=message.topic,
                    error_type=error_type,
                ).inc()

                logger.info(
                    "Message sent to DLQ",
                    dlq_topic=f"{message.topic}.dlq",
                    original_topic=message.topic,
                    offset=message.offset,
                    error_type=error_type,
                )
            else:
                dlq_send_errors_total.inc()
                logger.error(
                    "Failed to send to DLQ",
                    topic=message.topic,
                    offset=message.offset,
                )

        except Exception as e:
            dlq_send_errors_total.inc()
            logger.error(
                "Exception sending to DLQ",
                topic=message.topic,
                offset=message.offset,
                error=str(e),
            )

    def _classify_error(self, error: Exception) -> str:
        """
        Classify error type for metrics and DLQ.

        Args:
            error: The exception that occurred

        Returns:
            Error type classification string
        """
        error_name = type(error).__name__

        # Classification mapping
        classifications = {
            "ConnectionError": "connection",
            "TimeoutError": "timeout",
            "ValidationError": "validation",
            "ValueError": "validation",
            "KeyError": "data_format",
            "TypeError": "data_format",
            "PermissionError": "permission",
            "FileNotFoundError": "storage",
            "IOError": "storage",
        }

        return classifications.get(error_name, "processing")

    @abstractmethod
    async def process_event(self, event: dict):
        """
        Process a single event (must be implemented by subclasses).

        Args:
            event: Deserialized event data
        """
        pass
