"""Kafka event publishing service for AI search events."""

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
        event_type: Type of event
        payload: Event data
        key: Optional partition key

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


async def publish_embedding_generated(
    asset_id: str,
    workspace_id: str,
    embedding_dimension: int,
    processing_time_ms: float,
) -> bool:
    """
    Publish asset.embedding.generated event after creating CLIP embedding.

    Args:
        asset_id: ID of the processed asset
        workspace_id: Workspace ID for multi-tenancy
        embedding_dimension: Dimension of the generated embedding
        processing_time_ms: Processing time in milliseconds

    Returns:
        True if published successfully
    """
    payload = {
        "asset_id": asset_id,
        "workspace_id": workspace_id,
        "embedding_dimension": embedding_dimension,
        "processing_time_ms": processing_time_ms,
    }

    return await publish_event(
        topic="asset.embedding.generated",
        event_type="asset.embedding.generated",
        payload=payload,
        key=workspace_id,
    )


async def publish_search_query(
    workspace_id: str,
    query: str,
    result_count: int,
    latency_ms: float,
) -> bool:
    """
    Publish search.query.logged event for analytics.

    Args:
        workspace_id: Workspace ID
        query: Search query text
        result_count: Number of results returned
        latency_ms: Query latency in milliseconds

    Returns:
        True if published successfully
    """
    payload = {
        "workspace_id": workspace_id,
        "query": query,
        "result_count": result_count,
        "latency_ms": latency_ms,
    }

    return await publish_event(
        topic="search.query.logged",
        event_type="search.query.logged",
        payload=payload,
        key=workspace_id,
    )
