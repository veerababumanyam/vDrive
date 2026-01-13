"""
Event publishing for domain events via Kafka.
"""

from src.app.events.kafka_producer import (
    EmailVerifiedEvent,
    KafkaProducer,
    OnboardingCompletedEvent,
    UserRegisteredEvent,
    WorkspaceCreatedEvent,
    get_kafka_producer,
)

__all__ = [
    "KafkaProducer",
    "get_kafka_producer",
    "UserRegisteredEvent",
    "EmailVerifiedEvent",
    "WorkspaceCreatedEvent",
    "OnboardingCompletedEvent",
]
