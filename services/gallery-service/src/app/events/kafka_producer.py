"""
Kafka producer for publishing domain events.

Provides async event publishing with Pydantic event schemas.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel, Field

from src.app.core.config import settings


# ===========================================
# Event Schemas
# ===========================================
class BaseEvent(BaseModel):
    """Base event schema with common fields."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "gallery-service"
    version: str = "1.0"


class GalleryCreatedEvent(BaseEvent):
    """Event published when a gallery is created."""

    event_type: str = "gallery.created"
    gallery_id: str
    gallery_name: str
    workspace_id: str
    owner_id: str
    visibility: str  # "private" or "public"


class GalleryUpdatedEvent(BaseEvent):
    """Event published when a gallery is updated."""

    event_type: str = "gallery.updated"
    gallery_id: str
    workspace_id: str
    updated_fields: Dict[str, Any]


class GalleryDeletedEvent(BaseEvent):
    """Event published when a gallery is deleted."""

    event_type: str = "gallery.deleted"
    gallery_id: str
    workspace_id: str
    photo_count: int


class PhotoUploadedEvent(BaseEvent):
    """Event published when a photo is uploaded."""

    event_type: str = "photo.uploaded"
    photo_id: str
    gallery_id: str
    workspace_id: str
    file_size_bytes: int
    file_format: str
    storage_key: str


class PhotoDeletedEvent(BaseEvent):
    """Event published when a photo is deleted."""

    event_type: str = "photo.deleted"
    photo_id: str
    gallery_id: str
    workspace_id: str


class WatermarkAppliedEvent(BaseEvent):
    """Event published when watermark is applied."""

    event_type: str = "watermark.applied"
    batch_id: str
    gallery_id: str
    workspace_id: str
    photo_count: int
    watermark_type: str  # "text", "image", or "logo"
    watermark_config: Dict[str, Any]


# ===========================================
# Kafka Producer
# ===========================================
class KafkaProducer:
    """
    Async Kafka producer for event publishing.

    Handles connection lifecycle and event serialization.
    """

    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None
        self._started = False

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._started:
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",  # Wait for all replicas
            request_timeout_ms=settings.KAFKA_PRODUCER_TIMEOUT_MS,
            retry_backoff_ms=100,
            max_batch_size=16384,
            linger_ms=10,
        )
        await self._producer.start()
        self._started = True

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer and self._started:
            await self._producer.stop()
            self._started = False

    async def send_event(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None,
    ) -> bool:
        """
        Send event to Kafka topic.

        Args:
            topic: Kafka topic name
            event: Event to publish
            key: Optional partition key

        Returns:
            True if successful, False otherwise
        """
        if not self._started:
            await self.start()

        import logging

        logger = logging.getLogger(__name__)

        try:
            # Use event_id as key if not provided
            key = key or event.event_id

            await self._producer.send_and_wait(
                topic=topic,
                value=event.model_dump(mode="json"),
                key=key,
            )
            return True
        except Exception as e:
            # Log error but don't raise - events are best-effort
            logger.error(
                "Failed to send event to Kafka",
                extra={"topic": topic, "event_type": event.event_type, "error": str(e)},
            )
            return False

    async def publish_gallery_created(self, event: GalleryCreatedEvent) -> bool:
        """Publish gallery created event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_GALLERY_CREATED,
            event=event,
            key=event.gallery_id,
        )

    async def publish_gallery_updated(self, event: GalleryUpdatedEvent) -> bool:
        """Publish gallery updated event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_GALLERY_UPDATED,
            event=event,
            key=event.gallery_id,
        )

    async def publish_gallery_deleted(self, event: GalleryDeletedEvent) -> bool:
        """Publish gallery deleted event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_GALLERY_DELETED,
            event=event,
            key=event.gallery_id,
        )

    async def publish_photo_uploaded(self, event: PhotoUploadedEvent) -> bool:
        """Publish photo uploaded event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_PHOTO_UPLOADED,
            event=event,
            key=event.photo_id,
        )

    async def publish_photo_deleted(self, event: PhotoDeletedEvent) -> bool:
        """Publish photo deleted event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_PHOTO_DELETED,
            event=event,
            key=event.photo_id,
        )

    async def publish_watermark_applied(self, event: WatermarkAppliedEvent) -> bool:
        """Publish watermark applied event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_WATERMARK_APPLIED,
            event=event,
            key=event.batch_id,
        )


# Global producer instance
_kafka_producer: Optional[KafkaProducer] = None


async def get_kafka_producer() -> KafkaProducer:
    """Get or create Kafka producer instance."""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()
        await _kafka_producer.start()
    return _kafka_producer


async def close_kafka_producer() -> None:
    """Close Kafka producer on shutdown."""
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None
