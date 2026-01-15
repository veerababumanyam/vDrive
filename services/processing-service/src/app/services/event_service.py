"""Event publishing service for Kafka."""

import json
from typing import Optional

import structlog
from aiokafka import AIOKafkaProducer

from ..core.config import settings

logger = structlog.get_logger()


class EventService:
    """Publish events to Kafka topics."""

    def __init__(self):
        """Initialize event service."""
        self.producer: Optional[AIOKafkaProducer] = None
        self.enabled = False

    async def start(self):
        """Start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                compression_type="gzip",
                acks="all",
                max_request_size=10485760,  # 10MB
            )
            await self.producer.start()
            self.enabled = True
            logger.info("Event service started", brokers=settings.KAFKA_BOOTSTRAP_SERVERS)

        except Exception as e:
            logger.warning("Failed to start event service", error=str(e))
            self.enabled = False
            self.producer = None

    async def stop(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Event service stopped")

    async def publish_event(
        self,
        topic: str,
        event: dict,
        key: Optional[str] = None,
    ) -> bool:
        """
        Publish event to Kafka topic.

        Args:
            topic: Kafka topic name
            event: Event data dictionary
            key: Optional partition key (typically workspace_id)

        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled or not self.producer:
            logger.debug("Event service not enabled, skipping publish", topic=topic)
            return False

        try:
            key_bytes = key.encode("utf-8") if key else None

            await self.producer.send(
                topic=topic,
                value=event,
                key=key_bytes,
            )

            logger.debug("Event published", topic=topic, event_type=event.get("event_type"))
            return True

        except Exception as e:
            logger.error("Failed to publish event", topic=topic, error=str(e))
            return False


# Singleton instance
_event_service: Optional[EventService] = None


def get_event_service() -> EventService:
    """Get event service instance."""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service


async def init_event_service():
    """Initialize event service on startup."""
    service = get_event_service()
    await service.start()


async def close_event_service():
    """Close event service on shutdown."""
    service = get_event_service()
    await service.stop()
