"""
Kafka producer for publishing domain events.

Provides async event publishing with Pydantic event schemas.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
    source: str = "onboarding-service"
    version: str = "1.0"


class UserRegisteredEvent(BaseEvent):
    """Event published when a new user registers."""

    event_type: str = "user.registered"
    user_id: str
    email: str
    first_name: str
    last_name: str
    registration_method: str  # "email" or "google_oauth"
    email_verified: bool = False


class EmailVerifiedEvent(BaseEvent):
    """Event published when user verifies their email."""

    event_type: str = "user.email.verified"
    user_id: str
    email: str
    verification_method: str  # "token" or "oauth"


class WorkspaceCreatedEvent(BaseEvent):
    """Event published when a workspace is created."""

    event_type: str = "workspace.created"
    workspace_id: str
    workspace_name: str
    workspace_slug: str
    owner_id: str
    business_type: str
    trial_config: Dict[str, Any]


class OnboardingCompletedEvent(BaseEvent):
    """Event published when onboarding is completed."""

    event_type: str = "onboarding.completed"
    user_id: str
    workspace_id: str
    completed_steps: List[str]
    duration_seconds: Optional[int] = None


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
            print(f"Failed to send event to {topic}: {e}")
            return False

    async def publish_user_registered(self, event: UserRegisteredEvent) -> bool:
        """Publish user registered event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_USER_REGISTERED,
            event=event,
            key=event.user_id,
        )

    async def publish_email_verified(self, event: EmailVerifiedEvent) -> bool:
        """Publish email verified event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_EMAIL_VERIFIED,
            event=event,
            key=event.user_id,
        )

    async def publish_workspace_created(self, event: WorkspaceCreatedEvent) -> bool:
        """Publish workspace created event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_WORKSPACE_CREATED,
            event=event,
            key=event.workspace_id,
        )

    async def publish_onboarding_completed(
        self,
        event: OnboardingCompletedEvent,
    ) -> bool:
        """Publish onboarding completed event."""
        return await self.send_event(
            topic=settings.KAFKA_TOPIC_ONBOARDING_COMPLETED,
            event=event,
            key=event.user_id,
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
