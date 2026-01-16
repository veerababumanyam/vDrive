"""
Unit tests for ExportRepository (database operations).
"""

from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from src.app.models.export_job import ExportJob
from src.app.repositories.export_repository import ExportRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestExportRepository:
    """Test ExportRepository database operations."""

    @pytest_asyncio.fixture
    async def repository(self, test_db):
        """Create ExportRepository instance."""
        return ExportRepository(test_db)

    @pytest_asyncio.fixture
    async def test_export_job(self, test_db, test_workspace_id, test_user_id):
        """Create a test export job in database."""
        job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="pending",
            options={"include_metadata": True},
            total_assets=100,
            processed_assets=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)
        return job

    async def test_create_export_job(self, repository, test_export_job_data):
        """Test creating an export job."""
        job = await repository.create(test_export_job_data)

        assert job.id is not None
        assert job.workspace_id == test_export_job_data["workspace_id"]
        assert job.export_type == "workspace"
        assert job.status == "pending"

    async def test_get_by_id(self, repository, test_export_job):
        """Test getting export job by ID."""
        job = await repository.get_by_id(test_export_job.id)

        assert job is not None
        assert job.id == test_export_job.id
        assert job.workspace_id == test_export_job.workspace_id

    async def test_get_by_id_not_found(self, repository):
        """Test getting non-existent export job."""
        job = await repository.get_by_id("non-existent-id")

        assert job is None

    async def test_get_by_id_and_workspace(self, repository, test_export_job, test_workspace_id):
        """Test getting export job with workspace validation."""
        job = await repository.get_by_id_and_workspace(
            test_export_job.id,
            test_workspace_id,
        )

        assert job is not None
        assert job.id == test_export_job.id
        assert job.workspace_id == test_workspace_id

    async def test_get_by_id_and_workspace_wrong_workspace(self, repository, test_export_job):
        """Test workspace isolation - wrong workspace returns None."""
        wrong_workspace_id = str(uuid4())
        job = await repository.get_by_id_and_workspace(
            test_export_job.id,
            wrong_workspace_id,
        )

        assert job is None

    async def test_list_by_workspace(self, repository, test_export_job, test_workspace_id):
        """Test listing export jobs by workspace."""
        jobs, total = await repository.list_by_workspace(
            workspace_id=test_workspace_id,
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(jobs) == 1
        assert jobs[0].id == test_export_job.id

    async def test_list_by_workspace_with_status_filter(
        self,
        repository,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test listing export jobs with status filter."""
        # Create jobs with different statuses
        pending_job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="pending",
        )
        completed_job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="completed",
        )
        test_db.add_all([pending_job, completed_job])
        await test_db.commit()

        # Filter by pending status
        jobs, total = await repository.list_by_workspace(
            workspace_id=test_workspace_id,
            status="pending",
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(jobs) == 1
        assert jobs[0].status == "pending"

    async def test_update_status(self, repository, test_export_job):
        """Test updating export job status."""
        updated_job = await repository.update_status(
            test_export_job.id,
            "processing",
        )

        assert updated_job.status == "processing"
        assert updated_job.updated_at > test_export_job.updated_at

    async def test_update_progress(self, repository, test_export_job):
        """Test updating export job progress."""
        updated_job = await repository.update_progress(
            test_export_job.id,
            processed_assets=50,
            total_assets=100,
        )

        assert updated_job.processed_assets == 50
        assert updated_job.total_assets == 100

    async def test_mark_completed(self, repository, test_export_job):
        """Test marking export job as completed."""
        file_url = "https://example.com/export.zip"
        file_key = "exports/test-job.zip"
        file_size = 10240000

        updated_job = await repository.mark_completed(
            test_export_job.id,
            file_url=file_url,
            file_key=file_key,
            file_size=file_size,
        )

        assert updated_job.status == "completed"
        assert updated_job.file_url == file_url
        assert updated_job.file_key == file_key
        assert updated_job.file_size == file_size

    async def test_mark_failed(self, repository, test_export_job):
        """Test marking export job as failed."""
        error_message = "Export failed due to storage error"

        updated_job = await repository.mark_failed(
            test_export_job.id,
            error_message=error_message,
        )

        assert updated_job.status == "failed"
        assert updated_job.error_message == error_message

    async def test_cancel(self, repository, test_export_job):
        """Test cancelling an export job."""
        updated_job = await repository.cancel(test_export_job.id)

        assert updated_job.status == "cancelled"

    async def test_delete_expired(self, repository, test_db, test_workspace_id, test_user_id):
        """Test deleting expired export jobs."""
        # Create expired job
        expired_job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="completed",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )
        # Create non-expired job
        active_job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="completed",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),  # Not expired
        )
        test_db.add_all([expired_job, active_job])
        await test_db.commit()

        deleted_count = await repository.delete_expired()

        assert deleted_count == 1

        # Verify expired job is deleted
        remaining_jobs, total = await repository.list_by_workspace(
            workspace_id=test_workspace_id,
            limit=10,
            offset=0,
        )
        assert total == 1
        assert remaining_jobs[0].id == active_job.id
