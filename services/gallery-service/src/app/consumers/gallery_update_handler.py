"""Kafka consumer for gallery update events to WebSocket broadcasting."""

import asyncio
import json
from typing import Any, Optional

import structlog
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ..core.config import settings
from ..services.websocket_manager import (
    create_gallery_updated_message,
    create_photo_added_message,
    create_photo_removed_message,
    websocket_manager,
)

logger = structlog.get_logger()


class GalleryUpdateHandler:
    """
    Kafka consumer that handles gallery update events and broadcasts
    real-time updates to WebSocket connections.

    Listens to:
    - gallery.photo.added: When a photo is added to a gallery
    - gallery.photo.removed: When a photo is removed from a gallery
    - gallery.updated: When gallery metadata is updated
    - gallery.published: When gallery is published with magic link
    """

    def __init__(self):
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Initialize and start the consumer."""
        self._consumer = AIOKafkaConsumer(
            "gallery.photo.added",
            "gallery.photo.removed",
            "gallery.updated",
            "gallery.published",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"{settings.KAFKA_CONSUMER_GROUP_ID}-websocket",
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await self._consumer.start()
        self._running = True
        logger.info("Gallery update handler started")

    async def stop(self) -> None:
        """Stop the consumer gracefully."""
        self._running = False

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        logger.info("Gallery update handler stopped")

    async def run(self) -> None:
        """Main processing loop."""
        await self.start()

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                    await self._consumer.commit()
                except Exception as e:
                    logger.error(
                        "Error processing gallery event",
                        topic=message.topic,
                        offset=message.offset,
                        error=str(e),
                    )
                    await self._consumer.commit()

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        except KafkaError as e:
            logger.error("Kafka error in consumer", error=str(e))
        finally:
            await self.stop()

    async def _process_message(self, message: Any) -> None:
        """Process a single Kafka message."""
        topic = message.topic
        payload = message.value

        logger.debug(
            "Processing gallery event",
            topic=topic,
            offset=message.offset,
        )

        if topic == "gallery.photo.added":
            await self._handle_photo_added(payload)
        elif topic == "gallery.photo.removed":
            await self._handle_photo_removed(payload)
        elif topic == "gallery.updated":
            await self._handle_gallery_updated(payload)
        elif topic == "gallery.published":
            await self._handle_gallery_published(payload)

    async def _handle_photo_added(self, payload: dict) -> None:
        """
        Handle photo added event.

        Expected payload:
        {
            "gallery_id": "uuid",
            "asset_id": "uuid",
            "thumbnail_url": "url",
            "position": 0
        }
        """
        gallery_id = payload.get("gallery_id")
        asset_id = payload.get("asset_id")
        thumbnail_url = payload.get("thumbnail_url", "")
        position = payload.get("position")

        if not gallery_id or not asset_id:
            logger.warning("Invalid photo_added payload", payload=payload)
            return

        # Check if anyone is connected to this gallery
        connection_count = websocket_manager.get_connection_count(gallery_id)
        if connection_count == 0:
            logger.debug(
                "No WebSocket connections for gallery",
                gallery_id=gallery_id,
            )
            return

        message = create_photo_added_message(
            asset_id=asset_id,
            thumbnail_url=thumbnail_url,
            position=position,
        )

        sent_count = await websocket_manager.broadcast_to_gallery(
            gallery_id=gallery_id,
            message=message,
        )

        logger.info(
            "Photo added broadcast sent",
            gallery_id=gallery_id,
            asset_id=asset_id,
            connections_notified=sent_count,
        )

    async def _handle_photo_removed(self, payload: dict) -> None:
        """
        Handle photo removed event.

        Expected payload:
        {
            "gallery_id": "uuid",
            "asset_id": "uuid"
        }
        """
        gallery_id = payload.get("gallery_id")
        asset_id = payload.get("asset_id")

        if not gallery_id or not asset_id:
            logger.warning("Invalid photo_removed payload", payload=payload)
            return

        connection_count = websocket_manager.get_connection_count(gallery_id)
        if connection_count == 0:
            return

        message = create_photo_removed_message(asset_id=asset_id)

        sent_count = await websocket_manager.broadcast_to_gallery(
            gallery_id=gallery_id,
            message=message,
        )

        logger.info(
            "Photo removed broadcast sent",
            gallery_id=gallery_id,
            asset_id=asset_id,
            connections_notified=sent_count,
        )

    async def _handle_gallery_updated(self, payload: dict) -> None:
        """
        Handle gallery metadata update event.

        Expected payload:
        {
            "gallery_id": "uuid",
            "update_type": "name|cover|settings",
            "data": {...}
        }
        """
        gallery_id = payload.get("gallery_id")
        update_type = payload.get("update_type", "metadata")
        data = payload.get("data", {})

        if not gallery_id:
            return

        connection_count = websocket_manager.get_connection_count(gallery_id)
        if connection_count == 0:
            return

        message = create_gallery_updated_message(
            update_type=update_type,
            data=data,
        )

        sent_count = await websocket_manager.broadcast_to_gallery(
            gallery_id=gallery_id,
            message=message,
        )

        logger.info(
            "Gallery update broadcast sent",
            gallery_id=gallery_id,
            update_type=update_type,
            connections_notified=sent_count,
        )

    async def _handle_gallery_published(self, payload: dict) -> None:
        """
        Handle gallery published event.

        Expected payload:
        {
            "gallery_id": "uuid",
            "magic_link": "url",
            "published_at": "timestamp"
        }
        """
        gallery_id = payload.get("gallery_id")
        published_at = payload.get("published_at")

        if not gallery_id:
            return

        connection_count = websocket_manager.get_connection_count(gallery_id)
        if connection_count == 0:
            return

        message = create_gallery_updated_message(
            update_type="published",
            data={
                "published_at": published_at,
            },
        )

        await websocket_manager.broadcast_to_gallery(
            gallery_id=gallery_id,
            message=message,
        )

        logger.info(
            "Gallery published broadcast sent",
            gallery_id=gallery_id,
        )


# Create handler instance
gallery_update_handler = GalleryUpdateHandler()
