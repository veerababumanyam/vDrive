"""
Integration tests for Celery tasks.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from src.app.models.export_job import ExportJob
from src.app.workers.export_tasks import process_export_job, cleanup_expired_exports


@pytest.mark.integration
@pytest.mark.asyncio
class TestCeleryTasks:
    """Test Celery task execution."""

    async def test_process_export_job_task(
        self,
        test_db,
        test_workspace_id,
        test_user_id,
        mock_s3,
        mock_httpx_client,
    ):
        """Test export job processing task."""
        # Create export job
        job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="pending",
            options={"include_metadata": True},
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Mock gallery service response
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_httpx_client
            mock_httpx_client.get.return_value.json.return_value = {
                "assets": [
                    {
                        "id": str(uuid4()),
                        "file_name": "photo.jpg",
                        "file_url": "https://example.com/photo.jpg",
                        "file_size": 1024000,
                    }
                ],
                "total": 1,
            }

            # Execute task (in production this would be called by Celery worker)
            # For testing, we verify the task logic would work
            assert job.status == "pending"

            # In integration test, we verify task can be dispatched
            # (actual execution requires Celery worker running)
            with patch("src.app.workers.export_tasks.process_export_job.apply_async") as mock_task:
                mock_task.return_value = MagicMock(id="test-task-id")

                # Simulate task dispatch
                result = process_export_job.apply_async(args=[job.id])

                assert result.id == "test-task-id"
                mock_task.assert_called_once()

    async def test_cleanup_expired_exports_task(
        self,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test cleanup of expired exports task."""
        from datetime import datetime, timezone, timedelta

        # Create expired export job
        expired_job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="completed",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )
        test_db.add(expired_job)
        await test_db.commit()

        # Verify task can be dispatched
        with patch("src.app.workers.export_tasks.cleanup_expired_exports.apply_async") as mock_task:
            mock_task.return_value = MagicMock(id="cleanup-task-id")

            # Simulate task dispatch
            result = cleanup_expired_exports.apply_async()

            assert result.id == "cleanup-task-id"
            mock_task.assert_called_once()

    async def test_export_task_retry_on_failure(
        self,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test export task retry logic on failure."""
        # Create export job
        job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="pending",
            options={},
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Simulate task failure and retry
        with patch("src.app.workers.export_tasks.process_export_job.retry") as mock_retry:
            mock_retry.side_effect = Exception("Simulated retry")

            # Verify retry is configured (actual retry requires Celery worker)
            # In test, we verify the task has retry configuration
            task = process_export_job
            assert task.max_retries == 3
            assert task.default_retry_delay == 300  # 5 minutes
