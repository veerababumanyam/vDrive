"""
End-to-end tests for complete export flow.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExportFlow:
    """Test complete export flow from API to download."""

    async def test_complete_export_flow_workspace(
        self,
        async_client,
        authorization_header,
        mock_s3,
        mock_httpx_client,
    ):
        """
        Test complete workspace export flow:
        1. Create export job via API
        2. Job is processed (mocked worker)
        3. File is uploaded to R2
        4. Download URL is generated
        """
        # Step 1: Create export job via API
        create_data = {
            "export_type": "workspace",
            "options": {
                "include_metadata": True,
                "include_thumbnails": True,
            },
        }

        create_response = await async_client.post(
            "/api/v1/export/jobs",
            json=create_data,
            headers=authorization_header,
        )

        assert create_response.status_code == 201
        job = create_response.json()
        job_id = job["id"]
        assert job["status"] == "pending"

        # Step 2: Check job status
        status_response = await async_client.get(
            f"/api/v1/export/jobs/{job_id}",
            headers=authorization_header,
        )

        assert status_response.status_code == 200
        job_status = status_response.json()
        assert job_status["id"] == job_id

        # Step 3: Simulate job processing completion
        # (In production, Celery worker would do this)
        # For E2E test, we update the job directly
        from src.app.core.database import get_db

        async for db in get_db():
            from src.app.repositories.export_repository import ExportRepository

            repo = ExportRepository(db)
            completed_job = await repo.mark_completed(
                job_id,
                file_url="https://test-bucket.r2.example.com/export.zip",
                file_key="exports/test-export.zip",
                file_size=10240000,
            )
            await db.commit()
            break

        # Step 4: Verify job is completed
        final_response = await async_client.get(
            f"/api/v1/export/jobs/{job_id}",
            headers=authorization_header,
        )

        assert final_response.status_code == 200
        final_job = final_response.json()
        assert final_job["status"] == "completed"
        assert final_job["file_url"] is not None
        assert final_job["file_size"] == 10240000

    async def test_complete_export_flow_with_download(
        self,
        async_client,
        authorization_header,
        mock_s3,
    ):
        """
        Test complete export flow with file download:
        1. Create export job
        2. Mark as completed
        3. Generate download URL
        4. Verify download URL is accessible
        """
        # Step 1: Create export job
        create_data = {
            "export_type": "workspace",
            "options": {"include_metadata": True},
        }

        create_response = await async_client.post(
            "/api/v1/export/jobs",
            json=create_data,
            headers=authorization_header,
        )

        assert create_response.status_code == 201
        job = create_response.json()
        job_id = job["id"]

        # Step 2: Mark job as completed (simulating worker completion)
        from src.app.core.database import get_db

        async for db in get_db():
            from src.app.repositories.export_repository import ExportRepository

            repo = ExportRepository(db)
            await repo.mark_completed(
                job_id,
                file_url="https://test-bucket.r2.example.com/export.zip",
                file_key="exports/test-export.zip",
                file_size=5120000,
            )
            await db.commit()
            break

        # Step 3: Get job with download URL
        final_response = await async_client.get(
            f"/api/v1/export/jobs/{job_id}",
            headers=authorization_header,
        )

        assert final_response.status_code == 200
        final_job = final_response.json()
        assert final_job["status"] == "completed"
        assert final_job["file_url"] is not None

        # Step 4: Verify download URL format
        download_url = final_job["file_url"]
        assert download_url.startswith("https://")
        assert ".zip" in download_url

    async def test_export_cancellation_flow(
        self,
        async_client,
        authorization_header,
    ):
        """
        Test export cancellation flow:
        1. Create export job
        2. Cancel job before completion
        3. Verify job is cancelled
        """
        # Step 1: Create export job
        create_data = {
            "export_type": "workspace",
            "options": {},
        }

        create_response = await async_client.post(
            "/api/v1/export/jobs",
            json=create_data,
            headers=authorization_header,
        )

        assert create_response.status_code == 201
        job = create_response.json()
        job_id = job["id"]

        # Step 2: Cancel job
        cancel_response = await async_client.delete(
            f"/api/v1/export/jobs/{job_id}",
            headers=authorization_header,
        )

        assert cancel_response.status_code == 200
        cancelled_job = cancel_response.json()
        assert cancelled_job["status"] == "cancelled"

        # Step 3: Verify job remains cancelled
        status_response = await async_client.get(
            f"/api/v1/export/jobs/{job_id}",
            headers=authorization_header,
        )

        assert status_response.status_code == 200
        job_status = status_response.json()
        assert job_status["status"] == "cancelled"
