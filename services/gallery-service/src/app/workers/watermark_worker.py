"""
Async watermark worker with Redis task queue.

Processes watermark tasks from Redis queue, applies watermarks to images,
uploads to R2, and updates asset records.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from redis.asyncio import Redis

from src.app.core.config import settings
from src.app.core.database import get_db_session
from src.app.core.redis import get_redis, RedisKeys
from src.app.models.asset import ProcessingStatus
from src.app.repositories.asset_repository import AssetRepository
from src.app.schemas.watermark import (
    ImageWatermark,
    TextWatermark,
    WatermarkType,
)
from src.app.services.storage_service import StorageService, StorageError
from src.app.workers.image_processor import (
    apply_image_watermark,
    apply_text_watermark,
)

logger = logging.getLogger(__name__)


class WatermarkTaskStatus:
    """Watermark task status constants."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WatermarkWorker:
    """
    Async watermark worker that processes tasks from Redis queue.

    Pulls watermark tasks from Redis, processes images using Pillow,
    uploads to R2 storage, and updates database records.
    """

    # Redis queue keys
    TASK_QUEUE = "watermark:task_queue"
    TASK_DATA = "watermark:task:{task_id}"
    BATCH_STATUS = "watermark:batch:{batch_id}:status"
    BATCH_PROGRESS = "watermark:batch:{batch_id}:progress"
    WORKER_HEARTBEAT = "watermark:worker:{worker_id}:heartbeat"

    def __init__(
        self,
        redis: Optional[Redis] = None,
        storage: Optional[StorageService] = None,
        worker_id: Optional[str] = None,
        concurrency: int = 5,
    ):
        """
        Initialize watermark worker.

        Args:
            redis: Redis client instance (will be created if not provided)
            storage: Storage service instance (will be created if not provided)
            worker_id: Unique worker ID (generated if not provided)
            concurrency: Number of concurrent tasks to process
        """
        self.redis = redis
        self.storage = storage or StorageService()
        self.worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
        self.concurrency = concurrency
        self.running = False
        self.semaphore = asyncio.Semaphore(concurrency)

    async def start(self) -> None:
        """
        Start the worker to process tasks from Redis queue.

        Runs continuously until stopped, processing tasks as they arrive.
        """
        logger.info(
            f"Starting watermark worker {self.worker_id} with concurrency {self.concurrency}"
        )
        self.running = True

        # Ensure Redis connection
        if self.redis is None:
            async for redis_client in get_redis():
                self.redis = redis_client
                break

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            # Process tasks continuously
            while self.running:
                try:
                    await self._process_next_task()
                except Exception as e:
                    logger.error(f"Error in worker loop: {e}", exc_info=True)
                    await asyncio.sleep(1)  # Avoid tight loop on persistent errors

        except asyncio.CancelledError:
            logger.info(f"Worker {self.worker_id} cancelled")
        finally:
            self.running = False
            heartbeat_task.cancel()
            logger.info(f"Worker {self.worker_id} stopped")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False

    async def enqueue_batch(
        self,
        batch_id: str,
        gallery_id: str,
        workspace_id: str,
        asset_ids: List[str],
        watermark_type: WatermarkType,
        text_config: Optional[TextWatermark] = None,
        image_config: Optional[ImageWatermark] = None,
    ) -> None:
        """
        Enqueue a batch of watermark tasks.

        Args:
            batch_id: Unique batch identifier
            gallery_id: Gallery UUID
            workspace_id: Workspace UUID for multi-tenancy
            asset_ids: List of asset UUIDs to watermark
            watermark_type: Type of watermark (text or image)
            text_config: Text watermark configuration
            image_config: Image watermark configuration
        """
        if self.redis is None:
            async for redis_client in get_redis():
                self.redis = redis_client
                break

        # Create batch status
        batch_status = {
            "batch_id": batch_id,
            "gallery_id": gallery_id,
            "workspace_id": workspace_id,
            "total_tasks": len(asset_ids),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "status": WatermarkTaskStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store batch status
        await self.redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=86400,  # Expire in 24 hours
        )

        # Initialize batch progress
        await self.redis.set(
            self.BATCH_PROGRESS.format(batch_id=batch_id),
            0,
            ex=86400,
        )

        # Enqueue tasks
        for asset_id in asset_ids:
            task_id = f"{batch_id}:{asset_id}"
            task_data = {
                "task_id": task_id,
                "batch_id": batch_id,
                "gallery_id": gallery_id,
                "workspace_id": workspace_id,
                "asset_id": asset_id,
                "watermark_type": watermark_type.value,
                "text_config": text_config.model_dump() if text_config else None,
                "image_config": image_config.model_dump() if image_config else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Store task data
            await self.redis.set(
                self.TASK_DATA.format(task_id=task_id),
                json.dumps(task_data),
                ex=86400,
            )

            # Push to queue
            await self.redis.rpush(self.TASK_QUEUE, task_id)

        logger.info(
            f"Enqueued {len(asset_ids)} tasks for batch {batch_id} in gallery {gallery_id}"
        )

    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """
        Get status of a batch operation.

        Args:
            batch_id: Batch identifier

        Returns:
            Batch status dict or None if not found
        """
        if self.redis is None:
            async for redis_client in get_redis():
                self.redis = redis_client
                break

        status_json = await self.redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )
        if not status_json:
            return None

        return json.loads(status_json)

    async def _process_next_task(self) -> None:
        """
        Process the next task from the queue.

        Blocks until a task is available (with timeout).
        """
        # Block for up to 5 seconds waiting for a task
        result = await self.redis.blpop(self.TASK_QUEUE, timeout=5)

        if not result:
            # No task available, just return
            return

        _, task_id = result
        if isinstance(task_id, bytes):
            task_id = task_id.decode("utf-8")

        # Acquire semaphore for concurrency control
        async with self.semaphore:
            await self._process_task(task_id)

    async def _process_task(self, task_id: str) -> None:
        """
        Process a single watermark task.

        Args:
            task_id: Task identifier
        """
        try:
            # Retrieve task data
            task_data_json = await self.redis.get(
                self.TASK_DATA.format(task_id=task_id)
            )

            if not task_data_json:
                logger.error(f"Task data not found for task {task_id}")
                return

            task_data = json.loads(task_data_json)

            logger.info(
                f"Processing task {task_id} for asset {task_data['asset_id']}"
            )

            # Update batch status to processing
            await self._update_batch_status(
                task_data["batch_id"], status=WatermarkTaskStatus.PROCESSING
            )

            # Process the watermark
            success = await self._apply_watermark(task_data)

            # Update batch progress
            if success:
                await self._increment_batch_progress(
                    task_data["batch_id"], completed=True
                )
            else:
                await self._increment_batch_progress(
                    task_data["batch_id"], failed=True
                )

            # Clean up task data
            await self.redis.delete(self.TASK_DATA.format(task_id=task_id))

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            if "batch_id" in locals():
                await self._increment_batch_progress(
                    task_data["batch_id"], failed=True
                )

    async def _apply_watermark(self, task_data: Dict) -> bool:
        """
        Apply watermark to an asset.

        Args:
            task_data: Task data dictionary

        Returns:
            True if successful, False otherwise
        """
        asset_id = task_data["asset_id"]
        workspace_id = task_data["workspace_id"]
        watermark_type = WatermarkType(task_data["watermark_type"])

        try:
            # Get asset from database
            async with get_db_session() as db:
                asset_repo = AssetRepository(db)
                asset = await asset_repo.get_by_id(asset_id)

                if not asset:
                    logger.error(f"Asset not found: {asset_id}")
                    return False

                # Verify workspace isolation
                if asset.workspace_id != workspace_id:
                    logger.error(
                        f"Workspace mismatch for asset {asset_id}: expected {workspace_id}, got {asset.workspace_id}"
                    )
                    return False

                # Update processing status
                await asset_repo.update_processing_status(
                    asset_id, ProcessingStatus.PROCESSING
                )
                await db.commit()

            # Download original image from R2
            original_image = await self.storage.download_file(asset.storage_key)

            # Apply watermark based on type
            if watermark_type == WatermarkType.TEXT:
                text_config = TextWatermark(**task_data["text_config"])
                watermarked_image = apply_text_watermark(
                    original_image,
                    text_config,
                    output_format="JPEG",
                )
            elif watermark_type == WatermarkType.IMAGE:
                image_config = ImageWatermark(**task_data["image_config"])
                watermarked_image = apply_image_watermark(
                    original_image,
                    image_config,
                    output_format="JPEG",
                )
            else:
                logger.error(f"Unknown watermark type: {watermark_type}")
                return False

            # Upload watermarked image to R2
            # Store in watermarked/ prefix to keep original separate
            watermarked_key = f"watermarked/{asset.storage_key}"
            watermarked_url = await self.storage.upload_file(
                watermarked_image,
                watermarked_key,
                content_type=asset.mime_type,
                metadata={
                    "watermarked": "true",
                    "original_key": asset.storage_key,
                    "watermark_type": watermark_type.value,
                },
            )

            # Update asset with watermarked preview URL
            async with get_db_session() as db:
                asset_repo = AssetRepository(db)
                await asset_repo.update(
                    asset_id,
                    preview_url=watermarked_url,
                    preview_key=watermarked_key,
                    processing_status=ProcessingStatus.COMPLETED,
                    processing_error=None,
                )
                await db.commit()

            logger.info(
                f"Successfully watermarked asset {asset_id}: {watermarked_url}"
            )
            return True

        except StorageError as e:
            logger.error(f"Storage error for asset {asset_id}: {e}")
            await self._mark_asset_failed(asset_id, str(e))
            return False
        except Exception as e:
            logger.error(
                f"Failed to watermark asset {asset_id}: {e}", exc_info=True
            )
            await self._mark_asset_failed(asset_id, str(e))
            return False

    async def _update_batch_status(
        self, batch_id: str, status: str, **kwargs
    ) -> None:
        """
        Update batch status in Redis.

        Args:
            batch_id: Batch identifier
            status: New status
            **kwargs: Additional fields to update
        """
        status_json = await self.redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            logger.warning(f"Batch status not found: {batch_id}")
            return

        batch_status = json.loads(status_json)
        batch_status["status"] = status
        batch_status["updated_at"] = datetime.now(timezone.utc).isoformat()
        batch_status.update(kwargs)

        await self.redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=86400,
        )

    async def _increment_batch_progress(
        self, batch_id: str, completed: bool = False, failed: bool = False
    ) -> None:
        """
        Increment batch progress counters.

        Args:
            batch_id: Batch identifier
            completed: Whether task completed successfully
            failed: Whether task failed
        """
        # Increment progress counter
        await self.redis.incr(self.BATCH_PROGRESS.format(batch_id=batch_id))

        # Update batch status counters
        status_json = await self.redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            return

        batch_status = json.loads(status_json)

        if completed:
            batch_status["completed_tasks"] += 1
        if failed:
            batch_status["failed_tasks"] += 1

        # Check if batch is complete
        total = batch_status["total_tasks"]
        processed = batch_status["completed_tasks"] + batch_status["failed_tasks"]

        if processed >= total:
            batch_status["status"] = WatermarkTaskStatus.COMPLETED
            logger.info(
                f"Batch {batch_id} completed: {batch_status['completed_tasks']} succeeded, {batch_status['failed_tasks']} failed"
            )

        batch_status["updated_at"] = datetime.now(timezone.utc).isoformat()

        await self.redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=86400,
        )

    async def _mark_asset_failed(self, asset_id: str, error_message: str) -> None:
        """
        Mark asset processing as failed.

        Args:
            asset_id: Asset UUID
            error_message: Error message
        """
        try:
            async with get_db_session() as db:
                asset_repo = AssetRepository(db)
                await asset_repo.update_processing_status(
                    asset_id,
                    ProcessingStatus.FAILED,
                    error=error_message,
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to mark asset {asset_id} as failed: {e}")

    async def _heartbeat_loop(self) -> None:
        """
        Send periodic heartbeat to indicate worker is alive.

        Updates Redis key with current timestamp every 10 seconds.
        """
        try:
            while self.running:
                await self.redis.set(
                    self.WORKER_HEARTBEAT.format(worker_id=self.worker_id),
                    datetime.now(timezone.utc).isoformat(),
                    ex=30,  # Expire in 30 seconds
                )
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")


async def run_worker(concurrency: int = 5) -> None:
    """
    Run watermark worker as a standalone process.

    Args:
        concurrency: Number of concurrent tasks to process
    """
    worker = WatermarkWorker(concurrency=concurrency)

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await worker.stop()


if __name__ == "__main__":
    # Run worker directly
    asyncio.run(run_worker())
