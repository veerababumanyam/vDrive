"""
Integration tests for Migration API endpoints.
"""

import pytest
import pytest_asyncio


@pytest.mark.integration
@pytest.mark.asyncio
class TestMigrationAPI:
    """Test Migration API endpoints with database."""

    async def test_create_migration_job_api_pixieset(
        self,
        async_client,
        authorization_header,
    ):
        """Test creating Pixieset migration job via API."""
        data = {
            "platform": "pixieset",
            "credentials": {
                "api_key": "test-pixieset-key",
            },
        }

        response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=data,
            headers=authorization_header,
        )

        assert response.status_code == 201
        job = response.json()
        assert job["platform"] == "pixieset"
        assert job["status"] == "pending"

    async def test_create_migration_job_api_pictime(
        self,
        async_client,
        authorization_header,
    ):
        """Test creating Pic-Time migration job via API."""
        data = {
            "platform": "pic-time",
            "credentials": {
                "username": "test@example.com",
                "password": "test-password",
            },
        }

        response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=data,
            headers=authorization_header,
        )

        assert response.status_code == 201
        job = response.json()
        assert job["platform"] == "pic-time"

    async def test_create_migration_job_without_auth_401(
        self,
        async_client,
    ):
        """Test creating migration job without authentication returns 401."""
        data = {
            "platform": "pixieset",
            "credentials": {"api_key": "test-key"},
        }

        response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=data,
        )

        assert response.status_code == 401

    async def test_list_migration_jobs_api(
        self,
        async_client,
        authorization_header,
    ):
        """Test listing migration jobs via API."""
        response = await async_client.get(
            "/api/v1/export/migration/jobs",
            headers=authorization_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data

    async def test_get_migration_job_status_api(
        self,
        async_client,
        authorization_header,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test getting migration job status via API."""
        from src.app.models.migration_job import MigrationJob

        # Create a test migration job in database
        job = MigrationJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pixieset",
            status="processing",
            credentials={"api_key": "test-key"},
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Get job status via API
        response = await async_client.get(
            f"/api/v1/export/migration/jobs/{job.id}",
            headers=authorization_header,
        )

        assert response.status_code == 200
        job_data = response.json()
        assert job_data["id"] == job.id
        assert job_data["status"] == "processing"

    async def test_cancel_migration_job_api(
        self,
        async_client,
        authorization_header,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test cancelling migration job via API."""
        from src.app.models.migration_job import MigrationJob

        # Create a test migration job in database
        job = MigrationJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            platform="pixieset",
            status="pending",
            credentials={"api_key": "test-key"},
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Cancel job via API
        response = await async_client.delete(
            f"/api/v1/export/migration/jobs/{job.id}",
            headers=authorization_header,
        )

        assert response.status_code == 200
        cancelled_job = response.json()
        assert cancelled_job["status"] == "cancelled"

    async def test_list_migration_jobs_with_platform_filter(
        self,
        async_client,
        authorization_header,
    ):
        """Test listing migration jobs filtered by platform."""
        response = await async_client.get(
            "/api/v1/export/migration/jobs?platform=pixieset",
            headers=authorization_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        # All returned jobs should have platform "pixieset"
        for job in data["jobs"]:
            assert job["platform"] == "pixieset" or len(data["jobs"]) == 0

    async def test_invalid_platform_validation(
        self,
        async_client,
        authorization_header,
    ):
        """Test validation error for invalid platform."""
        data = {
            "platform": "invalid-platform",
            "credentials": {},
        }

        response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=data,
            headers=authorization_header,
        )

        assert response.status_code == 422
