"""Kafka consumer for processing assets and generating CLIP embeddings."""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from ..core.config import settings
from ..core.database import get_db_session
from ..services.embedding_service import embedding_service

logger = structlog.get_logger()


class AssetEmbeddingProcessor:
    """
    Kafka consumer that generates CLIP embeddings for processed assets.

    Listens to:
    - asset.processed: When an asset has been processed by the processing service

    Publishes:
    - asset.embedding.generated: When embedding is successfully created
    - asset.embedding.failed: When embedding generation fails
    """

    def __init__(self):
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False

    async def start(self) -> None:
        """Initialize and start the consumer."""
        self._consumer = AIOKafkaConsumer(
            "asset.processed",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"{settings.KAFKA_CONSUMER_GROUP_ID}-embedding",
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        await self._consumer.start()
        await self._producer.start()

        self._running = True
        logger.info("Asset embedding processor started")

    async def stop(self) -> None:
        """Stop the consumer gracefully."""
        self._running = False

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        if self._producer:
            await self._producer.stop()
            self._producer = None

        logger.info("Asset embedding processor stopped")

    async def run(self) -> None:
        """Main processing loop."""
        await self.start()

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)

                    # Manual commit after successful processing
                    await self._consumer.commit()

                except Exception as e:
                    logger.error(
                        "Error processing message",
                        topic=message.topic,
                        offset=message.offset,
                        error=str(e),
                    )
                    # Continue processing next message
                    await self._consumer.commit()

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        except KafkaError as e:
            logger.error("Kafka error in consumer", error=str(e))
        finally:
            await self.stop()

    async def _process_message(self, message: Any) -> None:
        """Process a single Kafka message."""
        payload = message.value
        event_type = payload.get("event_type")

        logger.info(
            "Processing message",
            topic=message.topic,
            event_type=event_type,
            offset=message.offset,
        )

        if event_type == "asset.processed":
            await self._handle_asset_processed(payload)

    async def _handle_asset_processed(self, payload: dict) -> None:
        """
        Handle asset.processed event - generate CLIP embedding.

        Expected payload:
        {
            "event_type": "asset.processed",
            "asset_id": "uuid",
            "workspace_id": "uuid",
            "storage_path": "path/to/file",
            "content_type": "image/jpeg",
            "thumbnail_url": "optional-url"
        }
        """
        asset_id = payload.get("asset_id")
        workspace_id = payload.get("workspace_id")
        storage_path = payload.get("storage_path")
        content_type = payload.get("content_type", "")

        if not all([asset_id, workspace_id, storage_path]):
            logger.warning("Invalid asset.processed payload", payload=payload)
            return

        # Only process images
        if not content_type.startswith("image/"):
            logger.debug(
                "Skipping non-image asset",
                asset_id=asset_id,
                content_type=content_type,
            )
            return

        logger.info(
            "Generating embedding for asset",
            asset_id=asset_id,
            workspace_id=workspace_id,
        )

        try:
            # Fetch image from storage
            image_bytes = await self._fetch_image(storage_path)

            if not image_bytes:
                await self._publish_failure(
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    error="Failed to fetch image",
                )
                return

            # Generate CLIP embedding
            embedding = await embedding_service.generate_image_embedding(image_bytes)

            if embedding is None:
                await self._publish_failure(
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    error="Embedding generation failed",
                )
                return

            # Store embedding in database
            async with get_db_session() as db:
                # Check if embedding already exists
                existing = await embedding_service.get_embedding(
                    db=db,
                    asset_id=UUID(asset_id),
                    workspace_id=UUID(workspace_id),
                )

                if existing:
                    # Delete old embedding and create new one
                    await embedding_service.delete_embedding(
                        db=db,
                        asset_id=UUID(asset_id),
                        workspace_id=UUID(workspace_id),
                    )

                await embedding_service.store_embedding(
                    db=db,
                    asset_id=UUID(asset_id),
                    workspace_id=UUID(workspace_id),
                    embedding=embedding,
                )

            # Publish success event
            await self._publish_success(
                asset_id=asset_id,
                workspace_id=workspace_id,
            )

            logger.info(
                "Embedding generated and stored",
                asset_id=asset_id,
            )

        except Exception as e:
            logger.error(
                "Embedding processing failed",
                asset_id=asset_id,
                error=str(e),
            )
            await self._publish_failure(
                asset_id=asset_id,
                workspace_id=workspace_id,
                error=str(e),
            )

    async def _fetch_image(self, storage_path: str) -> Optional[bytes]:
        """
        Fetch image from storage.

        This should integrate with R2/BYOS storage.
        For now, returns None to indicate storage fetch needed.
        """
        try:
            # TODO: Integrate with R2 storage service
            # This would typically call the upload-service or storage client
            # For now, log and return None

            logger.warning(
                "Storage fetch not implemented",
                storage_path=storage_path,
            )

            # Placeholder - in production, fetch from R2:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(storage_url)
            #     return response.content

            return None

        except Exception as e:
            logger.error("Failed to fetch image", path=storage_path, error=str(e))
            return None

    async def _publish_success(
        self,
        asset_id: str,
        workspace_id: str,
    ) -> None:
        """Publish asset.embedding.generated event."""
        if not self._producer:
            return

        event = {
            "event_type": "asset.embedding.generated",
            "asset_id": asset_id,
            "workspace_id": workspace_id,
            "model": settings.CLIP_MODEL,
            "dimension": settings.CLIP_EMBEDDING_DIMENSION,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._producer.send("asset.embedding.generated", event)
        logger.debug("Published embedding success event", asset_id=asset_id)

    async def _publish_failure(
        self,
        asset_id: str,
        workspace_id: str,
        error: str,
    ) -> None:
        """Publish asset.embedding.failed event."""
        if not self._producer:
            return

        event = {
            "event_type": "asset.embedding.failed",
            "asset_id": asset_id,
            "workspace_id": workspace_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._producer.send("asset.embedding.failed", event)
        logger.debug("Published embedding failure event", asset_id=asset_id)


# Create processor instance
asset_embedding_processor = AssetEmbeddingProcessor()
