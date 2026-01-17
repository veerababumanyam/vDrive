"""
Progress tracking service for batch operations in Redis.

Provides a clean service layer for tracking batch watermark operations,
storing progress and status information in Redis.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from redis.asyncio import Redis

from src.app.core.redis import get_redis

logger = logging.getLogger(__name__)


class BatchStatus:
    """Batch operation status constants."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressService:
    """
    Service for tracking batch operation progress in Redis.

    Provides methods to create, update, and query batch operation status
    for watermarking and other batch operations.
    """

    # Redis key patterns
    BATCH_STATUS = "watermark:batch:{batch_id}:status"
    BATCH_PROGRESS = "watermark:batch:{batch_id}:progress"
    BATCH_TASKS = "watermark:batch:{batch_id}:tasks"
    GALLERY_BATCHES = "watermark:gallery:{gallery_id}:batches"

    # Default TTL for batch data (24 hours)
    DEFAULT_TTL = 86400

    def __init__(self, redis: Optional[Redis] = None):
        """
        Initialize progress service.

        Args:
            redis: Redis client instance (will be created if not provided)
        """
        self.redis = redis

    async def _get_redis(self) -> Redis:
        """Get or create Redis client."""
        if self.redis is None:
            async for redis_client in get_redis():
                self.redis = redis_client
                break
        return self.redis

    async def create_batch(
        self,
        batch_id: str,
        gallery_id: str,
        workspace_id: str,
        total_tasks: int,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a new batch operation.

        Args:
            batch_id: Unique batch identifier
            gallery_id: Gallery UUID
            workspace_id: Workspace UUID for multi-tenancy
            total_tasks: Total number of tasks in the batch
            metadata: Optional metadata to store with batch

        Returns:
            Batch status dictionary
        """
        redis = await self._get_redis()

        batch_status = {
            "batch_id": batch_id,
            "gallery_id": gallery_id,
            "workspace_id": workspace_id,
            "total_tasks": total_tasks,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "status": BatchStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        # Store batch status
        await redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=self.DEFAULT_TTL,
        )

        # Initialize progress counter
        await redis.set(
            self.BATCH_PROGRESS.format(batch_id=batch_id),
            0,
            ex=self.DEFAULT_TTL,
        )

        # Add batch to gallery's batch list
        await redis.sadd(
            self.GALLERY_BATCHES.format(gallery_id=gallery_id),
            batch_id,
        )
        await redis.expire(
            self.GALLERY_BATCHES.format(gallery_id=gallery_id),
            self.DEFAULT_TTL,
        )

        logger.info(
            f"Created batch {batch_id} for gallery {gallery_id} with {total_tasks} tasks"
        )

        return batch_status

    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """
        Get current status of a batch operation.

        Args:
            batch_id: Batch identifier

        Returns:
            Batch status dictionary or None if not found
        """
        redis = await self._get_redis()

        status_json = await redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            return None

        return json.loads(status_json)

    async def update_batch_status(
        self,
        batch_id: str,
        status: Optional[str] = None,
        completed_tasks: Optional[int] = None,
        failed_tasks: Optional[int] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Update batch status.

        Args:
            batch_id: Batch identifier
            status: New status (pending/processing/completed/failed)
            completed_tasks: Number of completed tasks
            failed_tasks: Number of failed tasks
            **kwargs: Additional fields to update

        Returns:
            Updated batch status or None if batch not found
        """
        redis = await self._get_redis()

        status_json = await redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            logger.warning(f"Batch status not found: {batch_id}")
            return None

        batch_status = json.loads(status_json)

        # Update provided fields
        if status is not None:
            batch_status["status"] = status
        if completed_tasks is not None:
            batch_status["completed_tasks"] = completed_tasks
        if failed_tasks is not None:
            batch_status["failed_tasks"] = failed_tasks

        batch_status["updated_at"] = datetime.now(timezone.utc).isoformat()
        batch_status.update(kwargs)

        await redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=self.DEFAULT_TTL,
        )

        return batch_status

    async def increment_progress(
        self,
        batch_id: str,
        completed: bool = False,
        failed: bool = False,
    ) -> Optional[Dict]:
        """
        Increment batch progress counters.

        Automatically marks batch as completed when all tasks are processed.

        Args:
            batch_id: Batch identifier
            completed: Whether task completed successfully
            failed: Whether task failed

        Returns:
            Updated batch status or None if batch not found
        """
        redis = await self._get_redis()

        # Increment progress counter
        await redis.incr(self.BATCH_PROGRESS.format(batch_id=batch_id))

        # Update batch status counters
        status_json = await redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            logger.warning(f"Batch status not found: {batch_id}")
            return None

        batch_status = json.loads(status_json)

        if completed:
            batch_status["completed_tasks"] += 1
        if failed:
            batch_status["failed_tasks"] += 1

        # Check if batch is complete
        total = batch_status["total_tasks"]
        processed = batch_status["completed_tasks"] + batch_status["failed_tasks"]

        if processed >= total:
            # All tasks processed, mark as completed
            batch_status["status"] = BatchStatus.COMPLETED
            logger.info(
                f"Batch {batch_id} completed: {batch_status['completed_tasks']} succeeded, "
                f"{batch_status['failed_tasks']} failed"
            )

        batch_status["updated_at"] = datetime.now(timezone.utc).isoformat()

        await redis.set(
            self.BATCH_STATUS.format(batch_id=batch_id),
            json.dumps(batch_status),
            ex=self.DEFAULT_TTL,
        )

        return batch_status

    async def get_batch_progress_percentage(self, batch_id: str) -> Optional[float]:
        """
        Calculate progress percentage for a batch.

        Args:
            batch_id: Batch identifier

        Returns:
            Progress percentage (0-100) or None if batch not found
        """
        batch_status = await self.get_batch_status(batch_id)

        if not batch_status:
            return None

        total = batch_status["total_tasks"]
        if total == 0:
            return 100.0

        processed = batch_status["completed_tasks"] + batch_status["failed_tasks"]
        return (processed / total) * 100.0

    async def get_gallery_batches(self, gallery_id: str) -> List[str]:
        """
        Get all batch IDs for a gallery.

        Args:
            gallery_id: Gallery UUID

        Returns:
            List of batch IDs
        """
        redis = await self._get_redis()

        batch_ids = await redis.smembers(
            self.GALLERY_BATCHES.format(gallery_id=gallery_id)
        )

        return list(batch_ids) if batch_ids else []

    async def get_gallery_batch_statuses(self, gallery_id: str) -> List[Dict]:
        """
        Get status for all batches in a gallery.

        Args:
            gallery_id: Gallery UUID

        Returns:
            List of batch status dictionaries
        """
        batch_ids = await self.get_gallery_batches(gallery_id)

        statuses = []
        for batch_id in batch_ids:
            status = await self.get_batch_status(batch_id)
            if status:
                statuses.append(status)

        # Sort by created_at (newest first)
        statuses.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )

        return statuses

    async def delete_batch(self, batch_id: str, gallery_id: Optional[str] = None) -> bool:
        """
        Delete a batch and all its data.

        Args:
            batch_id: Batch identifier
            gallery_id: Optional gallery ID to remove batch from gallery's batch list

        Returns:
            True if batch was deleted, False if not found
        """
        redis = await self._get_redis()

        # Check if batch exists
        status_json = await redis.get(
            self.BATCH_STATUS.format(batch_id=batch_id)
        )

        if not status_json:
            return False

        # Get gallery_id from status if not provided
        if not gallery_id:
            batch_status = json.loads(status_json)
            gallery_id = batch_status.get("gallery_id")

        # Delete batch data
        await redis.delete(self.BATCH_STATUS.format(batch_id=batch_id))
        await redis.delete(self.BATCH_PROGRESS.format(batch_id=batch_id))
        await redis.delete(self.BATCH_TASKS.format(batch_id=batch_id))

        # Remove from gallery's batch list
        if gallery_id:
            await redis.srem(
                self.GALLERY_BATCHES.format(gallery_id=gallery_id),
                batch_id,
            )

        logger.info(f"Deleted batch {batch_id}")
        return True

    async def cleanup_completed_batches(
        self,
        gallery_id: str,
        max_age_hours: int = 24,
    ) -> int:
        """
        Clean up old completed batches for a gallery.

        Args:
            gallery_id: Gallery UUID
            max_age_hours: Maximum age in hours for completed batches to keep

        Returns:
            Number of batches deleted
        """
        batch_ids = await self.get_gallery_batches(gallery_id)
        deleted_count = 0

        for batch_id in batch_ids:
            status = await self.get_batch_status(batch_id)
            if not status:
                continue

            # Only delete completed or failed batches
            if status["status"] not in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
                continue

            # Check age
            created_at = datetime.fromisoformat(status["created_at"])
            age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

            if age_hours > max_age_hours:
                await self.delete_batch(batch_id, gallery_id)
                deleted_count += 1

        if deleted_count > 0:
            logger.info(
                f"Cleaned up {deleted_count} old batches for gallery {gallery_id}"
            )

        return deleted_count
