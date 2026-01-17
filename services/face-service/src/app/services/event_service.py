"""Kafka event publishing service for face detection events."""

from typing import Any, Optional
import json
from datetime import datetime, timezone

import structlog
from aiokafka import AIOKafkaProducer

from ..core.config import settings

logger = structlog.get_logger()

# Global producer instance
_producer: Optional[AIOKafkaProducer] = None


async def init_event_service() -> None:
    """Initialize Kafka producer for publishing events."""
    global _producer

    try:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            compression_type="lz4",
            acks="all",
            enable_idempotence=True,
        )
        await _producer.start()
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.error("Failed to initialize Kafka producer", error=str(e))
        raise


async def close_event_service() -> None:
    """Close Kafka producer."""
    global _producer

    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer closed")


async def publish_event(
    topic: str,
    event_type: str,
    payload: dict[str, Any],
    key: Optional[str] = None,
) -> bool:
    """
    Publish an event to Kafka.

    Args:
        topic: Kafka topic name
        event_type: Type of event (e.g., 'face.detected')
        payload: Event data
        key: Optional partition key (e.g., workspace_id)

    Returns:
        True if published successfully, False otherwise
    """
    if not _producer:
        logger.error("Kafka producer not initialized")
        return False

    event = {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": settings.SERVICE_NAME,
        "version": "1.0",
        "data": payload,
    }

    try:
        await _producer.send_and_wait(topic, value=event, key=key)
        logger.debug(
            "Event published",
            topic=topic,
            event_type=event_type,
            key=key,
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to publish event",
            topic=topic,
            event_type=event_type,
            error=str(e),
        )
        return False


async def publish_face_detected(
    asset_id: str,
    workspace_id: str,
    faces: list[dict[str, Any]],
    processing_time_ms: float,
) -> bool:
    """
    Publish face.detected event after processing an asset.

    Args:
        asset_id: ID of the processed asset
        workspace_id: Workspace ID for multi-tenancy
        faces: List of detected faces with bounding boxes and embeddings
        processing_time_ms: Processing time in milliseconds

    Returns:
        True if published successfully
    """
    payload = {
        "asset_id": asset_id,
        "workspace_id": workspace_id,
        "face_count": len(faces),
        "faces": [
            {
                "face_id": face.get("id"),
                "bounding_box": face.get("bounding_box"),
                "confidence": face.get("confidence"),
                "group_id": face.get("group_id"),
            }
            for face in faces
        ],
        "processing_time_ms": processing_time_ms,
    }

    return await publish_event(
        topic="face.detected",
        event_type="face.detected",
        payload=payload,
        key=workspace_id,
    )
