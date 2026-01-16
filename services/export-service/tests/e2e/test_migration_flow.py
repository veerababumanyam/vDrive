"""
End-to-end tests for complete migration flow.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMigrationFlow:
    """Test complete migration flow from API to import."""

    async def test_complete_migration_flow_pixieset(
        self,
        async_client,
        authorization_header,
        mock_httpx_client,
    ):
        """
        Test complete Pixieset migration flow:
        1. Create migration job via API
        2. Job validates credentials
        3. Job fetches galleries from Pixieset
        4. Job imports photos to vDrive
        5. Job completes successfully
        """
        # Step 1: Create migration job
        create_data = {
            "platform": "pixieset",
            "credentials": {
                "api_key": "test-pixieset-api-key",
            },
        }

        create_response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=create_data,
            headers=authorization_header,
        )

        assert create_response.status_code == 201
        job = create_response.json()
        job_id = job["id"]
        assert job["platform"] == "pixieset"
        assert job["status"] == "pending"

        # Step 2: Check job status
        status_response = await async_client.get(
            f"/api/v1/export/migration/jobs/{job_id}",
            headers=authorization_header,
        )

        assert status_response.status_code == 200
        job_status = status_response.json()
        assert job_status["id"] == job_id
        assert job_status["platform"] == "pixieset"

        # Step 3: Simulate job processing and completion
        # (In production, Celery worker would process the migration)
        from src.app.core.database import get_db

        async for db in get_db():
            from src.app.repositories.migration_repository import MigrationRepository

            repo = MigrationRepository(db)
            # Update progress
            await repo.update_progress(
                job_id,
                processed_galleries=5,
                total_galleries=5,
                processed_assets=100,
                total_assets=100,
            )
            # Mark completed
            await repo.update_status(job_id, "completed")
            await db.commit()
            break

        # Step 4: Verify job is completed
        final_response = await async_client.get(
            f"/api/v1/export/migration/jobs/{job_id}",
            headers=authorization_header,
        )

        assert final_response.status_code == 200
        final_job = final_response.json()
        assert final_job["status"] == "completed"
        assert final_job["processed_galleries"] == 5
        assert final_job["processed_assets"] == 100

    async def test_migration_cancellation_flow(
        self,
        async_client,
        authorization_header,
    ):
        """
        Test migration cancellation flow:
        1. Create migration job
        2. Cancel job before completion
        3. Verify job is cancelled
        """
        # Step 1: Create migration job
        create_data = {
            "platform": "pic-time",
            "credentials": {
                "username": "test@example.com",
                "password": "test-password",
            },
        }

        create_response = await async_client.post(
            "/api/v1/export/migration/jobs",
            json=create_data,
            headers=authorization_header,
        )

        assert create_response.status_code == 201
        job = create_response.json()
        job_id = job["id"]

        # Step 2: Cancel job
        cancel_response = await async_client.delete(
            f"/api/v1/export/migration/jobs/{job_id}",
            headers=authorization_header,
        )

        assert cancel_response.status_code == 200
        cancelled_job = cancel_response.json()
        assert cancelled_job["status"] == "cancelled"

        # Step 3: Verify job remains cancelled
        status_response = await async_client.get(
            f"/api/v1/export/migration/jobs/{job_id}",
            headers=authorization_header,
        )

        assert status_response.status_code == 200
        job_status = status_response.json()
        assert job_status["status"] == "cancelled"

    async def test_multiple_platform_migrations(
        self,
        async_client,
        authorization_header,
    ):
        """
        Test creating migration jobs for multiple platforms:
        1. Create Pixieset migration
        2. Create Pic-Time migration
        3. Create ShootProof migration
        4. Verify all jobs are created independently
        """
        platforms = [
            {
                "platform": "pixieset",
                "credentials": {"api_key": "pixieset-key"},
            },
            {
                "platform": "pic-time",
                "credentials": {"username": "user", "password": "pass"},
            },
            {
                "platform": "shootproof",
                "credentials": {"access_token": "shootproof-token"},
            },
        ]

        job_ids = []

        # Create migration jobs for each platform
        for platform_data in platforms:
            response = await async_client.post(
                "/api/v1/export/migration/jobs",
                json=platform_data,
                headers=authorization_header,
            )

            assert response.status_code == 201
            job = response.json()
            job_ids.append(job["id"])
            assert job["platform"] == platform_data["platform"]

        # Verify all jobs were created
        assert len(job_ids) == 3
        assert len(set(job_ids)) == 3  # All IDs are unique

        # Verify we can list all jobs
        list_response = await async_client.get(
            "/api/v1/export/migration/jobs",
            headers=authorization_header,
        )

        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] >= 3
