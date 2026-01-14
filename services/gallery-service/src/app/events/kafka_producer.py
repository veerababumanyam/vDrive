"""Kafka producer for publishing domain events"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel, Field

from src.app.core.config import settings

# Global Kafka producer
_kafka_producer: Optional[AIOKafkaProducer] = None


class BaseEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "gallery-service"
    version: str = "1.0"


class GalleryPublishedEvent(BaseEvent):
    """Event emitted when gallery is published."""

    event_type: str = "gallery.published"
    gallery_id: str
    workspace_id: str
    title: str


class GalleryArchivedEvent(BaseEvent):
    """Event emitted when gallery is archived."""

    event_type: str = "gallery.archived"
    gallery_id: str
    workspace_id: str


class VisitorRegisteredEvent(BaseEvent):
    """Event emitted when visitor registers via email."""

    event_type: str = "visitor.registered"
    visitor_id: str
    workspace_id: str
    email: str
    gallery_id: str


async def init_kafka_producer() -> AIOKafkaProducer:
    """Initialize Kafka producer."""
    global _kafka_producer
    _kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",  # Wait for all replicas
    )
    await _kafka_producer.start()
    return _kafka_producer


async def get_kafka_producer() -> Optional[AIOKafkaProducer]:
    """Get Kafka producer (creates if not exists)."""
    global _kafka_producer
    if _kafka_producer is None:
        try:
            await init_kafka_producer()
        except Exception:
            # Kafka is optional - service should work without it
            pass
    return _kafka_producer


async def close_kafka_producer() -> None:
    """Close Kafka producer."""
    global _kafka_producer
    if _kafka_producer is not None:
        await _kafka_producer.stop()
        _kafka_producer = None


async def send_event(topic: str, event: BaseEvent, key: str) -> None:
    """
    Send event to Kafka topic.

    Args:
        topic: Kafka topic name
        event: Domain event to send
        key: Partition key (typically entity ID)
    """
    producer = await get_kafka_producer()
    if producer is None:
        # Kafka unavailable - log warning but don't fail request
        return

    try:
        await producer.send_and_wait(
            topic=topic,
            value=event.model_dump(mode="json"),
            key=key.encode("utf-8"),
        )
    except Exception:
        # Best-effort delivery - don't fail requests if Kafka is down
        pass
