"""Kafka event publishing service."""

from typing import Optional
from aiokafka import AIOKafkaProducer
import structlog
from ..core.config import settings
from ..schemas.events import BaseEvent

logger = structlog.get_logger()
_producer: Optional[AIOKafkaProducer] = None


async def init_kafka_producer():
    """Initialize Kafka producer (called in lifespan)."""
    global _producer
    try:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: v.encode("utf-8"),
            compression_type="gzip",
        )
        await _producer.start()
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.warning("Kafka producer initialization failed", error=str(e))
        _producer = None


async def close_kafka_producer():
    """Close Kafka producer (called in lifespan)."""
    global _producer
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer closed")


class EventService:
    """Kafka event publishing."""

    @staticmethod
    async def publish_event(topic: str, event: BaseEvent, key: str) -> bool:
        """Publish event to Kafka topic."""
        if not _producer:
            logger.warning("Kafka producer unavailable", topic=topic)
            return False

        try:
            await _producer.send_and_wait(
                topic=topic,
                value=event.model_dump_json(),
                key=key.encode("utf-8"),
            )
            logger.debug("Event published", topic=topic, event_type=event.event_type)
            return True
        except Exception as e:
            logger.error("Failed to publish event", topic=topic, error=str(e))
            return False


def get_event_service() -> EventService:
    """Get event service instance."""
    return EventService()
