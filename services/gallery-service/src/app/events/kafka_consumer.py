"""
Kafka consumer for consuming domain events.

Listens for gallery.published events and triggers watermark processing.
"""

import asyncio
import json
import logging
from typing import Optional
from uuid import uuid4

from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel, Field

from src.app.core.config import settings
from src.app.core.database import get_db_session
from src.app.repositories.gallery_repository import GalleryRepository
from src.app.repositories.asset_repository import AssetRepository
from src.app.schemas.watermark import TextWatermark, ImageWatermark, WatermarkType
from src.app.workers.watermark_worker import WatermarkWorker

logger = logging.getLogger(__name__)


# ===========================================
# Event Schemas
# ===========================================
class GalleryPublishedEvent(BaseModel):
    """Event received when a gallery is published."""

    event_id: str
    event_type: str
    gallery_id: str
    workspace_id: str
    published_by: str
    watermark_enabled: bool = False


# ===========================================
# Kafka Consumer
# ===========================================
class KafkaConsumer:
    """
    Async Kafka consumer for event consumption.

    Handles connection lifecycle, event deserialization, and processing.
    """

    def __init__(
        self,
        group_id: str = "gallery-service-watermark-consumer",
        worker: Optional[WatermarkWorker] = None,
    ):
        """
        Initialize Kafka consumer.

        Args:
            group_id: Consumer group ID for offset management
            worker: WatermarkWorker instance (created if not provided)
        """
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._started = False
        self._running = False
        self.group_id = group_id
        self.worker = worker or WatermarkWorker()

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._started:
            return

        self._consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_GALLERY_PUBLISHED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",  # Start from beginning if no offset
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            session_timeout_ms=30000,
            max_poll_records=10,
        )
        await self._consumer.start()
        self._started = True
        logger.info(
            f"Kafka consumer started for topic: {settings.KAFKA_TOPIC_GALLERY_PUBLISHED}"
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self._consumer and self._started:
            self._running = False
            await self._consumer.stop()
            self._started = False
            logger.info("Kafka consumer stopped")

    async def consume_events(self) -> None:
        """
        Consume events from Kafka topics.

        Runs continuously until stopped, processing events as they arrive.
        """
        if not self._started:
            await self.start()

        self._running = True
        logger.info("Starting event consumption loop")

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        f"Error processing message from topic {message.topic}: {e}",
                        exc_info=True,
                    )
                    # Continue processing other messages
                    continue

        except asyncio.CancelledError:
            logger.info("Event consumption cancelled")
        except Exception as e:
            logger.error(f"Error in event consumption loop: {e}", exc_info=True)
        finally:
            await self.stop()

    async def _process_message(self, message) -> None:
        """
        Process a single Kafka message.

        Args:
            message: Kafka message object
        """
        logger.debug(
            f"Received message from topic {message.topic}, partition {message.partition}, offset {message.offset}"
        )

        event_data = message.value
        event_type = event_data.get("event_type")

        if event_type == "gallery.published":
            await self._handle_gallery_published(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    async def _handle_gallery_published(self, event_data: dict) -> None:
        """
        Handle gallery.published event.

        Triggers watermark processing if watermark is enabled for the gallery.

        Args:
            event_data: Event payload
        """
        try:
            event = GalleryPublishedEvent(**event_data)
            logger.info(
                f"Processing gallery.published event for gallery {event.gallery_id}"
            )

            # Get gallery from database to check watermark configuration
            async with get_db_session() as db:
                gallery_repo = GalleryRepository(db)
                gallery = await gallery_repo.get_by_id(event.gallery_id)

                if not gallery:
                    logger.error(f"Gallery not found: {event.gallery_id}")
                    return

                # Verify workspace isolation
                if gallery.workspace_id != event.workspace_id:
                    logger.error(
                        f"Workspace mismatch for gallery {event.gallery_id}: "
                        f"expected {event.workspace_id}, got {gallery.workspace_id}"
                    )
                    return

                # Check if watermarking is enabled
                if not gallery.watermark_enabled:
                    logger.info(
                        f"Watermark not enabled for gallery {event.gallery_id}, skipping"
                    )
                    return

                # Get all assets in the gallery
                asset_repo = AssetRepository(db)
                assets = await asset_repo.get_by_gallery_id(event.gallery_id)

                if not assets:
                    logger.info(
                        f"No assets found in gallery {event.gallery_id}, skipping watermark"
                    )
                    return

                asset_ids = [str(asset.id) for asset in assets]

                logger.info(
                    f"Found {len(asset_ids)} assets to watermark in gallery {event.gallery_id}"
                )

                # Parse watermark configuration from gallery
                # TODO: Once watermark_config JSONB field is added to Gallery model,
                # use gallery.watermark_config instead of watermark_url
                watermark_config = self._parse_watermark_config(gallery)

                if not watermark_config:
                    logger.warning(
                        f"No watermark configuration found for gallery {event.gallery_id}"
                    )
                    return

                watermark_type = watermark_config.get("type", WatermarkType.TEXT)
                text_config = None
                image_config = None

                if watermark_type == WatermarkType.TEXT:
                    text_config = TextWatermark(**watermark_config.get("text", {}))
                elif watermark_type == WatermarkType.IMAGE:
                    image_config = ImageWatermark(**watermark_config.get("image", {}))

                # Enqueue batch watermark task
                batch_id = str(uuid4())
                await self.worker.enqueue_batch(
                    batch_id=batch_id,
                    gallery_id=str(gallery.id),
                    workspace_id=str(gallery.workspace_id),
                    asset_ids=asset_ids,
                    watermark_type=watermark_type,
                    text_config=text_config,
                    image_config=image_config,
                )

                logger.info(
                    f"Enqueued watermark batch {batch_id} for gallery {event.gallery_id} "
                    f"with {len(asset_ids)} assets"
                )

        except Exception as e:
            logger.error(
                f"Error handling gallery.published event: {e}", exc_info=True
            )

    def _parse_watermark_config(self, gallery) -> Optional[dict]:
        """
        Parse watermark configuration from gallery model.

        Args:
            gallery: Gallery model instance

        Returns:
            Watermark configuration dict or None
        """
        # For now, parse from watermark_url field (JSON string)
        # TODO: Use dedicated watermark_config JSONB field once added
        if not gallery.watermark_url:
            return None

        try:
            # If watermark_url contains JSON config, parse it
            if gallery.watermark_url.startswith("{"):
                return json.loads(gallery.watermark_url)

            # Otherwise, create default text watermark config
            return {
                "type": WatermarkType.TEXT,
                "text": {
                    "text": "© vDrive",
                    "font_size": 48,
                    "color": "#FFFFFF",
                    "opacity": 0.5,
                    "position": "bottom_right",
                },
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse watermark config: {e}")
            return None


# Global consumer instance
_kafka_consumer: Optional[KafkaConsumer] = None


async def get_kafka_consumer() -> KafkaConsumer:
    """Get or create Kafka consumer instance."""
    global _kafka_consumer
    if _kafka_consumer is None:
        _kafka_consumer = KafkaConsumer()
        await _kafka_consumer.start()
    return _kafka_consumer


async def close_kafka_consumer() -> None:
    """Close Kafka consumer on shutdown."""
    global _kafka_consumer
    if _kafka_consumer:
        await _kafka_consumer.stop()
        _kafka_consumer = None


async def start_consumer() -> None:
    """
    Start the Kafka consumer as a standalone process.

    This function is the entry point for running the consumer.
    """
    consumer = KafkaConsumer()

    try:
        logger.info("Starting Kafka consumer for gallery.published events")
        await consumer.consume_events()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await consumer.stop()
    except Exception as e:
        logger.error(f"Consumer crashed: {e}", exc_info=True)
        await consumer.stop()
        raise


if __name__ == "__main__":
    # Run consumer directly
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(start_consumer())
