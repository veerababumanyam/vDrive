"""Kafka consumer for processing face detection on uploaded assets."""

import asyncio
import json
import time
from typing import Optional
from uuid import UUID

import structlog
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import async_session_factory
from ..core.redis import redis_manager
from ..models import Face, FaceEmbedding
from ..services.face_detection_service import face_detection_service
from ..services.embedding_service import embedding_service
from ..services.clustering_service import clustering_service
from ..services.event_service import publish_face_detected

logger = structlog.get_logger()


class AssetFaceProcessor:
    """
    Processes asset.processed events to detect faces, generate embeddings,
    and cluster them into groups.

    Pipeline:
    1. Receive asset.processed event
    2. Download asset image
    3. Detect faces using Google Cloud Vision
    4. Generate embeddings using DeepFace/ArcFace
    5. Assign faces to groups using DBSCAN clustering
    6. Publish face.detected event
    """

    def __init__(self):
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Initialize and start the Kafka consumer."""
        self._consumer = AIOKafkaConsumer(
            "asset.processed",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self._consumer.start()
        self._running = True
        logger.info("AssetFaceProcessor consumer started")

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("AssetFaceProcessor consumer stopped")

    async def run(self) -> None:
        """Main consumer loop."""
        await self.start()

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message.value)
                    await self._consumer.commit()
                except Exception as e:
                    logger.error(
                        "Failed to process message",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        error=str(e),
                    )
        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        finally:
            await self.stop()

    async def _process_message(self, event: dict) -> None:
        """Process a single asset.processed event."""
        start_time = time.time()

        data = event.get("data", {})
        asset_id = data.get("asset_id")
        workspace_id = data.get("workspace_id")
        storage_path = data.get("storage_path")
        mime_type = data.get("mime_type", "")

        if not all([asset_id, workspace_id, storage_path]):
            logger.warning("Missing required fields in event", event=event)
            return

        # Only process images
        if not mime_type.startswith("image/"):
            logger.debug("Skipping non-image asset", mime_type=mime_type)
            return

        # Check idempotency
        idempotency_key = f"face_processed:{asset_id}"
        if await redis_manager.get(idempotency_key):
            logger.debug("Asset already processed", asset_id=asset_id)
            return

        logger.info(
            "Processing asset for faces",
            asset_id=asset_id,
            workspace_id=workspace_id,
        )

        try:
            # Download image from storage
            image_bytes = await self._download_asset(storage_path)

            if not image_bytes:
                logger.warning("Failed to download asset", asset_id=asset_id)
                return

            # Detect faces
            detected_faces = await face_detection_service.detect_faces(image_bytes)

            if not detected_faces:
                logger.debug("No faces detected", asset_id=asset_id)
                # Mark as processed even if no faces
                await redis_manager.set(idempotency_key, "1", expire=86400)
                return

            # Process each face
            async with async_session_factory() as db:
                faces_data = []

                for detected in detected_faces:
                    # Create face record
                    face = Face(
                        asset_id=UUID(asset_id),
                        workspace_id=UUID(workspace_id),
                        bounding_box=detected.bounding_box,
                        confidence=detected.confidence,
                        landmarks=detected.landmarks,
                        detection_metadata=detected.metadata,
                    )
                    db.add(face)
                    await db.flush()

                    # Generate embedding
                    embedding_vector = await embedding_service.generate_embedding(
                        image_bytes,
                        detected.bounding_box,
                    )

                    if embedding_vector is not None:
                        # Store embedding
                        face_embedding = FaceEmbedding(
                            face_id=face.id,
                            embedding=embedding_vector.tolist(),
                        )
                        db.add(face_embedding)
                        await db.flush()

                        face.embedding_id = face_embedding.id

                        # Assign to group
                        group_id = await clustering_service.assign_to_group(
                            db=db,
                            face=face,
                            embedding=embedding_vector,
                            workspace_id=UUID(workspace_id),
                        )

                        faces_data.append({
                            "id": str(face.id),
                            "bounding_box": detected.bounding_box,
                            "confidence": detected.confidence,
                            "group_id": str(group_id) if group_id else None,
                        })

                await db.commit()

            # Mark as processed
            await redis_manager.set(idempotency_key, "1", expire=86400)

            # Publish event
            processing_time_ms = (time.time() - start_time) * 1000
            await publish_face_detected(
                asset_id=asset_id,
                workspace_id=workspace_id,
                faces=faces_data,
                processing_time_ms=processing_time_ms,
            )

            logger.info(
                "Face processing complete",
                asset_id=asset_id,
                faces_detected=len(faces_data),
                processing_time_ms=round(processing_time_ms, 2),
            )

        except Exception as e:
            logger.error(
                "Face processing failed",
                asset_id=asset_id,
                error=str(e),
            )
            raise

    async def _download_asset(self, storage_path: str) -> Optional[bytes]:
        """Download asset from R2 storage."""
        try:
            import boto3
            from botocore.config import Config

            # This would use actual R2 credentials in production
            # For now, returning None to indicate storage integration needed
            logger.warning("Storage download not implemented", path=storage_path)
            return None

        except Exception as e:
            logger.error("Asset download failed", error=str(e))
            return None
