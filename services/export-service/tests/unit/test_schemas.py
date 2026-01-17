"""
Unit tests for Export and Migration schemas (Pydantic validation).
"""

import pytest
from pydantic import ValidationError

from src.app.schemas.export import ExportCreateRequest, ExportResponse
from src.app.schemas.migration import MigrationCreateRequest, MigrationResponse


@pytest.mark.unit
class TestExportSchemas:
    """Test Export Pydantic schemas."""

    def test_export_create_request_workspace_type(self):
        """Test ExportCreateRequest with workspace export type."""
        data = {
            "export_type": "workspace",
            "options": {
                "include_metadata": True,
                "include_thumbnails": True,
            },
        }

        request = ExportCreateRequest(**data)

        assert request.export_type == "workspace"
        assert request.options["include_metadata"] is True
        assert request.options["include_thumbnails"] is True

    def test_export_create_request_gallery_type(self):
        """Test ExportCreateRequest with gallery export type."""
        data = {
            "export_type": "gallery",
            "options": {
                "gallery_ids": ["gallery-id-1", "gallery-id-2"],
                "include_metadata": False,
            },
        }

        request = ExportCreateRequest(**data)

        assert request.export_type == "gallery"
        assert len(request.options["gallery_ids"]) == 2

    def test_export_create_request_selection_type(self):
        """Test ExportCreateRequest with selection export type."""
        data = {
            "export_type": "selection",
            "options": {
                "asset_ids": ["asset-1", "asset-2", "asset-3"],
            },
        }

        request = ExportCreateRequest(**data)

        assert request.export_type == "selection"
        assert len(request.options["asset_ids"]) == 3

    def test_export_create_request_invalid_type(self):
        """Test ExportCreateRequest with invalid export type."""
        data = {
            "export_type": "invalid-type",
            "options": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            ExportCreateRequest(**data)

        assert "export_type" in str(exc_info.value)

    def test_export_create_request_empty_options(self):
        """Test ExportCreateRequest with empty options."""
        data = {
            "export_type": "workspace",
            "options": {},
        }

        request = ExportCreateRequest(**data)

        assert request.export_type == "workspace"
        assert request.options == {}

    def test_export_response_serialization(self, test_user_id, test_workspace_id):
        """Test ExportResponse can serialize export job data."""
        from datetime import datetime, timezone

        data = {
            "id": "export-job-id",
            "workspace_id": test_workspace_id,
            "user_id": test_user_id,
            "status": "completed",
            "export_type": "workspace",
            "options": {"include_metadata": True},
            "total_assets": 100,
            "processed_assets": 100,
            "file_url": "https://example.com/export.zip",
            "file_size": 10240000,
            "file_key": "exports/export-job-id.zip",
            "error_message": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc),
        }

        response = ExportResponse(**data)

        assert response.id == "export-job-id"
        assert response.status == "completed"
        assert response.file_url == "https://example.com/export.zip"


@pytest.mark.unit
class TestMigrationSchemas:
    """Test Migration Pydantic schemas."""

    def test_migration_create_request_pixieset(self):
        """Test MigrationCreateRequest with Pixieset platform."""
        data = {
            "platform": "pixieset",
            "credentials": {
                "api_key": "test-pixieset-api-key",
            },
        }

        request = MigrationCreateRequest(**data)

        assert request.platform == "pixieset"
        assert request.credentials["api_key"] == "test-pixieset-api-key"

    def test_migration_create_request_pictime(self):
        """Test MigrationCreateRequest with Pic-Time platform."""
        data = {
            "platform": "pic-time",
            "credentials": {
                "username": "photographer@example.com",
                "password": "secure-password",
            },
        }

        request = MigrationCreateRequest(**data)

        assert request.platform == "pic-time"
        assert "username" in request.credentials
        assert "password" in request.credentials

    def test_migration_create_request_shootproof(self):
        """Test MigrationCreateRequest with ShootProof platform."""
        data = {
            "platform": "shootproof",
            "credentials": {
                "access_token": "shootproof-access-token",
            },
        }

        request = MigrationCreateRequest(**data)

        assert request.platform == "shootproof"
        assert request.credentials["access_token"] == "shootproof-access-token"

    def test_migration_create_request_invalid_platform(self):
        """Test MigrationCreateRequest with invalid platform."""
        data = {
            "platform": "invalid-platform",
            "credentials": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            MigrationCreateRequest(**data)

        assert "platform" in str(exc_info.value)

    def test_migration_response_serialization(self, test_user_id, test_workspace_id):
        """Test MigrationResponse can serialize migration job data."""
        from datetime import datetime, timezone

        data = {
            "id": "migration-job-id",
            "workspace_id": test_workspace_id,
            "user_id": test_user_id,
            "platform": "pixieset",
            "status": "processing",
            "credentials": {"api_key": "***"},  # Masked in response
            "total_galleries": 10,
            "processed_galleries": 5,
            "total_assets": 500,
            "processed_assets": 250,
            "error_message": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        response = MigrationResponse(**data)

        assert response.id == "migration-job-id"
        assert response.platform == "pixieset"
        assert response.processed_galleries == 5
        assert response.processed_assets == 250
