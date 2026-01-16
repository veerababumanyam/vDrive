"""
Integration tests for Export API endpoints.
"""

from uuid import uuid4

import pytest
import pytest_asyncio


@pytest.mark.integration
@pytest.mark.asyncio
class TestExportAPI:
    """Test Export API endpoints with database."""

    async def test_create_export_job_api_with_auth(
        self,
        async_client,
        authorization_header,
    ):
        """Test creating export job via API with authentication."""
        data = {
            "export_type": "workspace",
            "options": {
                "include_metadata": True,
                "include_thumbnails": True,
            },
        }

        response = await async_client.post(
            "/api/v1/export/jobs",
            json=data,
            headers=authorization_header,
        )

        assert response.status_code == 201
        job = response.json()
        assert job["export_type"] == "workspace"
        assert job["status"] == "pending"
        assert "id" in job

    async def test_create_export_job_api_without_auth_401(
        self,
        async_client,
    ):
        """Test creating export job without authentication returns 401."""
        data = {
            "export_type": "workspace",
            "options": {},
        }

        response = await async_client.post(
            "/api/v1/export/jobs",
            json=data,
        )

        assert response.status_code == 401

    async def test_list_export_jobs_api(
        self,
        async_client,
        authorization_header,
    ):
        """Test listing export jobs via API."""
        response = await async_client.get(
            "/api/v1/export/jobs",
            headers=authorization_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

    async def test_get_export_job_status_api(
        self,
        async_client,
        authorization_header,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test getting export job status via API."""
        from src.app.models.export_job import ExportJob

        # Create a test export job in database
        job = ExportJob(
            workspace_id=test_workspace_id,
            user_id=test_user_id,
            export_type="workspace",
            status="processing",
            options={},
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Get job status via API
        response = await async_client.get(
            f"/api/v1/export/jobs/{job.id}",
            headers=authorization_header,
        )

        assert response.status_code == 200
        job_data = response.json()
        assert job_data["id"] == job.id
        assert job_data["status"] == "processing"

    async def test_cancel_export_job_api(
        self,
        async_client,
        authorization_header,
        test_db,
        test_workspace_id,
        test_user_id,
    ):
        """Test cancelling export job via API."""
        from src.app.models.export_job import ExportJob

        # Create a test export job in database
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

        # Cancel job via API
        response = await async_client.delete(
            f"/api/v1/export/jobs/{job.id}",
            headers=authorization_header,
        )

        assert response.status_code == 200
        cancelled_job = response.json()
        assert cancelled_job["status"] == "cancelled"

    async def test_multi_tenancy_enforced(
        self,
        async_client,
        test_db,
    ):
        """Test workspace multi-tenancy isolation."""
        from src.app.models.export_job import ExportJob
        from src.app.core.security import create_access_token

        # Create job for workspace A
        workspace_a_id = str(uuid4())
        user_a_id = str(uuid4())
        job_a = ExportJob(
            workspace_id=workspace_a_id,
            user_id=user_a_id,
            export_type="workspace",
            status="completed",
            options={},
        )
        test_db.add(job_a)
        await test_db.commit()
        await test_db.refresh(job_a)

        # Create token for workspace B
        workspace_b_id = str(uuid4())
        user_b_id = str(uuid4())
        token_b = create_access_token(
            data={
                "sub": user_b_id,
                "email": "user_b@example.com",
                "workspace_id": workspace_b_id,
            }
        )
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Attempt to access job from workspace A using workspace B credentials
        response = await async_client.get(
            f"/api/v1/export/jobs/{job_a.id}",
            headers=headers_b,
        )

        # Should return 404 (not found) due to workspace isolation
        assert response.status_code == 404

    async def test_create_export_job_validation_errors(
        self,
        async_client,
        authorization_header,
    ):
        """Test validation errors for invalid export job data."""
        data = {
            "export_type": "invalid-type",
            "options": {},
        }

        response = await async_client.post(
            "/api/v1/export/jobs",
            json=data,
            headers=authorization_header,
        )

        assert response.status_code == 422

    async def test_list_export_jobs_with_status_filter(
        self,
        async_client,
        authorization_header,
    ):
        """Test listing export jobs with status filter."""
        response = await async_client.get(
            "/api/v1/export/jobs?status=completed",
            headers=authorization_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        # All returned jobs should have status "completed"
        for job in data["jobs"]:
            assert job["status"] == "completed" or len(data["jobs"]) == 0
