"""Base Kafka consumer with retry and DLQ logic."""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Optional

import structlog
from aiokafka import AIOKafkaConsumer, ConsumerRecord

from ..core.config import settings
from ..core.metrics import (
    kafka_messages_consumed_total,
    kafka_messages_failed_total,
)

logger = structlog.get_logger()


class BaseConsumer(ABC):
    """Base class for Kafka consumers with retry and DLQ support."""

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
        """Start the Kafka consumer."""
        try:
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
            )

        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise

    async def stop(self):
        """Stop the Kafka consumer."""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped", consumer_group=self.consumer_group)

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
                    logger.error(
                        "Fatal error processing message",
                        topic=message.topic,
                        offset=message.offset,
                        error=str(e),
                    )

                    kafka_messages_failed_total.labels(
                        topic=message.topic,
                        error_type="fatal",
                    ).inc()

                    # Send to DLQ
                    await self._send_to_dlq(message, error=str(e))

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

                logger.debug(
                    "Processing Kafka message",
                    topic=message.topic,
                    offset=message.offset,
                    event_type=event_type,
                    event_id=event_id,
                    retry_count=retry_count,
                )

                # Check idempotency (avoid duplicate processing)
                if await self._is_already_processed(event_id):
                    logger.info(
                        "Message already processed (idempotent skip)",
                        event_id=event_id,
                    )
                    return

                # Call abstract process_event method
                await self.process_event(event)

                # Mark as processed
                await self._mark_as_processed(event_id)

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

                # Exponential backoff
                backoff_seconds = 2 ** retry_count
                logger.warning(
                    "Retrying message after error",
                    topic=message.topic,
                    offset=message.offset,
                    retry_count=retry_count,
                    backoff_seconds=backoff_seconds,
                    error=str(e),
                )

                await asyncio.sleep(backoff_seconds)

    async def _is_already_processed(self, event_id: str) -> bool:
        """
        Check if event has already been processed (idempotency).

        Args:
            event_id: Unique event identifier

        Returns:
            True if already processed, False otherwise
        """
        # TODO: Implement with Redis or database
        # For now, return False (no idempotency check)
        return False

    async def _mark_as_processed(self, event_id: str):
        """
        Mark event as processed (idempotency tracking).

        Args:
            event_id: Unique event identifier
        """
        # TODO: Implement with Redis or database
        # Store event_id with TTL (e.g., 24 hours)
        pass

    async def _send_to_dlq(self, message: ConsumerRecord, error: str):
        """
        Send failed message to Dead Letter Queue.

        Args:
            message: Original Kafka message
            error: Error description
        """
        try:
            dlq_topic = f"{message.topic}.dlq"

            logger.error(
                "Sending message to DLQ",
                dlq_topic=dlq_topic,
                original_topic=message.topic,
                offset=message.offset,
                error=error,
            )

            # TODO: Implement DLQ producer
            # For now, just log
            # await dlq_producer.send(dlq_topic, message.value)

        except Exception as e:
            logger.error("Failed to send to DLQ", error=str(e))

    @abstractmethod
    async def process_event(self, event: dict):
        """
        Process a single event (must be implemented by subclasses).

        Args:
            event: Deserialized event data
        """
        pass
