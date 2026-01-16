"""
Unit tests for MigrationService (migration business logic).
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio

from src.app.models.migration_job import MigrationJob
from src.app.repositories.migration_repository import MigrationRepository
from src.app.services.migration_service import MigrationService, MigrationError


@pytest.mark.unit
@pytest.mark.asyncio
class TestMigrationService:
    """Test MigrationService business logic."""

    @pytest_asyncio.fixture
    async def repository(self):
        """Create mock MigrationRepository."""
        repository = AsyncMock(spec=MigrationRepository)
        return repository

    @pytest_asyncio.fixture
    async def service(self, repository):
        """Create MigrationService instance with mock repository."""
        return MigrationService(repository)

    async def test_create_migration_job_pixieset(
        self,
        service,
        repository,
        test_workspace_id,
        test_user_id,
    ):
        """Test creating a Pixieset migration job."""
        mock_job = MigrationJob(
            id=str(uuid4()),
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pixieset",
            status="pending",
            credentials={"api_key": "test-key"},
        )
        repository.create.return_value = mock_job

        job = await service.create_migration_job(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pixieset",
            credentials={"api_key": "test-key"},
        )

        assert job.platform == "pixieset"
        assert job.status == "pending"
        repository.create.assert_called_once()

    async def test_create_migration_job_pictime(
        self,
        service,
        repository,
        test_workspace_id,
        test_user_id,
    ):
        """Test creating a Pic-Time migration job."""
        mock_job = MigrationJob(
            id=str(uuid4()),
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pic-time",
            status="pending",
            credentials={"username": "user", "password": "pass"},
        )
        repository.create.return_value = mock_job

        job = await service.create_migration_job(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pic-time",
            credentials={"username": "user", "password": "pass"},
        )

        assert job.platform == "pic-time"

    async def test_validate_credentials_pixieset(self, service):
        """Test validating Pixieset credentials."""
        credentials = {"api_key": "test-pixieset-key"}

        # Should not raise error for valid structure
        result = await service.validate_credentials("pixieset", credentials)

        assert result is True

    async def test_validate_credentials_invalid_platform(self, service):
        """Test validating credentials for invalid platform."""
        credentials = {"api_key": "test-key"}

        with pytest.raises(MigrationError) as exc_info:
            await service.validate_credentials("invalid-platform", credentials)

        assert "platform" in str(exc_info.value).lower()

    async def test_get_migration_job(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test getting migration job."""
        job_id = str(uuid4())
        mock_job = MigrationJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            platform="pixieset",
            status="processing",
        )
        repository.get_by_id_and_workspace.return_value = mock_job

        job = await service.get_migration_job(
            job_id=job_id,
            workspace_id=test_workspace_id,
        )

        assert job is not None
        assert job.id == job_id

    async def test_list_migration_jobs(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test listing migration jobs."""
        mock_jobs = [
            MigrationJob(
                id=str(uuid4()),
                workspace_id=test_workspace_id,
                user_id=str(uuid4()),
                platform="pixieset",
                status="completed",
            )
            for _ in range(3)
        ]
        repository.list_by_workspace.return_value = (mock_jobs, 3)

        jobs, total = await service.list_migration_jobs(
            workspace_id=test_workspace_id,
            limit=10,
            offset=0,
        )

        assert total == 3
        assert len(jobs) == 3

    async def test_cancel_migration_job(
        self,
        service,
        repository,
        test_workspace_id,
    ):
        """Test cancelling a migration job."""
        job_id = str(uuid4())
        mock_job = MigrationJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            platform="pixieset",
            status="processing",
        )
        repository.get_by_id_and_workspace.return_value = mock_job

        cancelled_job = MigrationJob(
            id=job_id,
            workspace_id=test_workspace_id,
            user_id=str(uuid4()),
            platform="pixieset",
            status="cancelled",
        )
        repository.cancel.return_value = cancelled_job

        job = await service.cancel_migration_job(
            job_id=job_id,
            workspace_id=test_workspace_id,
        )

        assert job.status == "cancelled"
