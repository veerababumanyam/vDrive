"""
Unit tests for Export and Migration Job models.
"""

from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest

from src.app.models.export_job import ExportJob
from src.app.models.migration_job import MigrationJob


@pytest.mark.unit
class TestExportJobModel:
    """Test ExportJob model."""

    def test_export_job_model_creation(self):
        """Test ExportJob model can be created with all fields."""
        workspace_id = str(uuid4())
        user_id = str(uuid4())

        job = ExportJob(
            workspace_id=workspace_id,
            user_id=user_id,
            export_type="workspace",
            status="pending",
            options={"include_metadata": True},
            total_assets=100,
            processed_assets=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        assert job.workspace_id == workspace_id
        assert job.user_id == user_id
        assert job.export_type == "workspace"
        assert job.status == "pending"
        assert job.options == {"include_metadata": True}
        assert job.total_assets == 100
        assert job.processed_assets == 0

    def test_export_job_progress_percentage_zero(self):
        """Test progress_percentage property with zero assets."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="pending",
            total_assets=0,
            processed_assets=0,
        )

        assert job.progress_percentage == 0

    def test_export_job_progress_percentage_partial(self):
        """Test progress_percentage property with partial progress."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="processing",
            total_assets=100,
            processed_assets=50,
        )

        assert job.progress_percentage == 50

    def test_export_job_progress_percentage_complete(self):
        """Test progress_percentage property when complete."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="completed",
            total_assets=100,
            processed_assets=100,
        )

        assert job.progress_percentage == 100

    def test_export_job_is_active_pending(self):
        """Test is_active property for pending status."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="pending",
        )

        assert job.is_active is True

    def test_export_job_is_active_processing(self):
        """Test is_active property for processing status."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="processing",
        )

        assert job.is_active is True

    def test_export_job_is_active_completed(self):
        """Test is_active property for completed status."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="completed",
        )

        assert job.is_active is False

    def test_export_job_is_active_failed(self):
        """Test is_active property for failed status."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="failed",
        )

        assert job.is_active is False

    def test_export_job_is_complete_completed(self):
        """Test is_complete property when completed."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="completed",
        )

        assert job.is_complete is True

    def test_export_job_is_complete_pending(self):
        """Test is_complete property when not completed."""
        job = ExportJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            export_type="workspace",
            status="pending",
        )

        assert job.is_complete is False


@pytest.mark.unit
class TestMigrationJobModel:
    """Test MigrationJob model."""

    def test_migration_job_model_creation(self):
        """Test MigrationJob model can be created with all fields."""
        workspace_id = str(uuid4())
        user_id = str(uuid4())

        job = MigrationJob(
            workspace_id=workspace_id,
            user_id=user_id,
            platform="pixieset",
            status="pending",
            credentials={"api_key": "test-key"},
            total_galleries=10,
            processed_galleries=0,
            total_assets=500,
            processed_assets=0,
        )

        assert job.workspace_id == workspace_id
        assert job.user_id == user_id
        assert job.platform == "pixieset"
        assert job.status == "pending"
        assert job.credentials == {"api_key": "test-key"}
        assert job.total_galleries == 10
        assert job.processed_galleries == 0
        assert job.total_assets == 500
        assert job.processed_assets == 0

    def test_migration_job_gallery_progress_percentage(self):
        """Test gallery_progress_percentage property."""
        job = MigrationJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            platform="pixieset",
            status="processing",
            total_galleries=10,
            processed_galleries=5,
        )

        assert job.gallery_progress_percentage == 50

    def test_migration_job_asset_progress_percentage(self):
        """Test asset_progress_percentage property."""
        job = MigrationJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            platform="pixieset",
            status="processing",
            total_assets=100,
            processed_assets=75,
        )

        assert job.asset_progress_percentage == 75

    def test_migration_job_is_active_pending(self):
        """Test is_active property for pending status."""
        job = MigrationJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            platform="pixieset",
            status="pending",
        )

        assert job.is_active is True

    def test_migration_job_is_complete_completed(self):
        """Test is_complete property when completed."""
        job = MigrationJob(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            platform="pixieset",
            status="completed",
        )

        assert job.is_complete is True
