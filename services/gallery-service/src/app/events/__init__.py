"""
Gallery Service events package.

Provides Kafka event publishing and consuming functionality.
"""

from src.app.events.kafka_producer import (
    GalleryCreatedEvent,
    GalleryDeletedEvent,
    GalleryUpdatedEvent,
    KafkaProducer,
    PhotoDeletedEvent,
    PhotoUploadedEvent,
    WatermarkAppliedEvent,
    get_kafka_producer,
    close_kafka_producer,
)
from src.app.events.kafka_consumer import (
    GalleryPublishedEvent,
    KafkaConsumer,
    get_kafka_consumer,
    close_kafka_consumer,
    start_consumer,
)

__all__ = [
    # Producer
    "KafkaProducer",
    "get_kafka_producer",
    "close_kafka_producer",
    "GalleryCreatedEvent",
    "GalleryUpdatedEvent",
    "GalleryDeletedEvent",
    "PhotoUploadedEvent",
    "PhotoDeletedEvent",
    "WatermarkAppliedEvent",
    # Consumer
    "KafkaConsumer",
    "get_kafka_consumer",
    "close_kafka_consumer",
    "GalleryPublishedEvent",
    "start_consumer",
]
