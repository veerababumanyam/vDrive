"""
Unit tests for ExportService (business logic).
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from src.app.models.export_job import ExportJob
from src.app.repositories.export_repository import ExportRepository
from src.app.services.export_service import ExportService, ExportError


@pytest.mark.unit
@pytest.mark.asyncio
class TestExportService:
    """Test ExportService business logic."""

    @pytest_asyncio.fixture
    async def repository(self):
        """Create mock ExportRepository."""
        repository = AsyncMock(spec=ExportRepository)
        return repository

    @pytest_asyncio.fixture
    async def service(self, repository):
        """Create ExportService instance with mock repository."""
        return ExportService(repository)

    async def test_create_export_job_workspace(
        self,
        service,
        repository,
        test_workspace_id,
        test_user_id,
    ):
        """Test creating a workspace export job."""
        # Mock repository response
        mock_job = ExportJob(
            id=str(uuid4()),
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="pending",
            options={"include_metadata": True},
        )
        repository.create.return_value = mock_job

        # Create export job
        job = await service.create_export_job(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            options={"include_metadata": True},
        )

        assert job.export_type == "workspace"
        assert job.status == "pending"
        repository.create.assert_called_once()

    async def test_create_export_job_gallery(
        self,
        service,
        repository,
        test_workspace_id,
        test_user_id,
        test_gallery_id,
    ):
        """Test creating a gallery export job."""
        # Mock repository response
        mock_job = ExportJob(
            id=str(uuid4()),
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="gallery",
            status="pending",
            options={"gallery_ids": [test_gallery_id]},
        )
        repository.create.return_value = mock_job

        # Create export job
        job = await service.create_export_job(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="gallery",
            options={"gallery_ids": [test_gallery_id]},
        )

        assert job.export_type == "gallery"
        assert test_gallery_id in job.options["gallery_ids"]

    async def test_create_export_job_concurrent_limit(
        self,
        service,
        repository,
        test_workspace_id,
        test_user_id,
    ):
        """Test concurrent export limit is enforced."""
        # Mock repository to return 3 active jobs
        active_jobs = [
            ExportJob(
                id=str(uuid4()),
                workspace_id=test_workspace_id,
                user_id=test_user_id,
                export_type="workspace",
                status="processing",
            )
            for _ in range(3)
        ]
        repository.list_by_workspace.return_value = (active_jobs, 3)

        # Attempt to create another export job
        with pytest.raises(ExportError) as exc_info:
            await service.create_export_job(
                workspace_id=test_workspace_id,
                user_id=test_user_id,
                export_type="workspace",
                options={},
            )

        assert "concurrent" in str(exc_info.value).lower()

    async def test_get_export_job_with_workspace_validation(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test getting export job with workspace validation."""
        job_id = str(uuid4())
        mock_job = ExportJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            export_type="workspace",
            status="completed",
        )
        repository.get_by_id_and_workspace.return_value = mock_job

        job = await service.get_export_job(
            job_id=job_id,
            workspace_id=test_workspace_id,
        )

        assert job is not None
        assert job.id == job_id
        repository.get_by_id_and_workspace.assert_called_once_with(
            job_id,
            test_workspace_id,
        )

    async def test_get_export_job_not_found(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test getting non-existent export job raises error."""
        job_id = str(uuid4())
        repository.get_by_id_and_workspace.return_value = None

        with pytest.raises(ExportError) as exc_info:
            await service.get_export_job(
                job_id=job_id,
                workspace_id=test_workspace_id,
            )

        assert "not found" in str(exc_info.value).lower()

    async def test_list_export_jobs(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test listing export jobs."""
        mock_jobs = [
            ExportJob(
                id=str(uuid4()),
                workspace_id=test_workspace_id,
                user_id=str(uuid4()),
                export_type="workspace",
                status="completed",
            )
            for _ in range(5)
        ]
        repository.list_by_workspace.return_value = (mock_jobs, 5)

        jobs, total = await service.list_export_jobs(
            workspace_id=test_workspace_id,
            limit=10,
            offset=0,
        )

        assert total == 5
        assert len(jobs) == 5

    async def test_cancel_export_job(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test cancelling an export job."""
        job_id = str(uuid4())
        mock_job = ExportJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            export_type="workspace",
            status="processing",
        )
        repository.get_by_id_and_workspace.return_value = mock_job

        cancelled_job = ExportJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            export_type="workspace",
            status="cancelled",
        )
        repository.cancel.return_value = cancelled_job

        job = await service.cancel_export_job(
            job_id=job_id,
            workspace_id=test_workspace_id,
        )

        assert job.status == "cancelled"
        repository.cancel.assert_called_once()

    async def test_cancel_export_job_already_completed(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test cannot cancel completed export job."""
        job_id = str(uuid4())
        mock_job = ExportJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            export_type="workspace",
            status="completed",
        )
        repository.get_by_id_and_workspace.return_value = mock_job

        with pytest.raises(ExportError) as exc_info:
            await service.cancel_export_job(
                job_id=job_id,
                workspace_id=test_workspace_id,
            )

        assert "cannot cancel" in str(exc_info.value).lower()

    async def test_cleanup_expired_exports(
        self,
        service,
        repository,
    ):
        """Test cleanup of expired exports."""
        repository.delete_expired.return_value = 5

        deleted_count = await service.cleanup_expired_exports()

        assert deleted_count == 5
        repository.delete_expired.assert_called_once()
