"""
Export schemas for bulk export operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExportCreateRequest(BaseModel):
    """Request schema for creating an export job."""

    export_type: str = Field(
        ...,
        description="Type of export (workspace, gallery, selection)",
        examples=["workspace"],
    )
    options: Optional[dict] = Field(
        default=None,
        description="Export options (include_metadata, include_thumbnails, gallery_ids, etc.)",
        examples=[
            {
                "include_metadata": True,
                "include_thumbnails": False,
                "gallery_ids": ["gallery-uuid-1", "gallery-uuid-2"],
            }
        ],
    )

    @field_validator("export_type")
    @classmethod
    def validate_export_type(cls, v: str) -> str:
        """Validate export_type is one of the allowed values."""
        allowed_types = ["workspace", "gallery", "selection"]
        if v not in allowed_types:
            raise ValueError(
                f"export_type must be one of {allowed_types}, got '{v}'"
            )
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[dict], info) -> Optional[dict]:
        """Validate export options based on export_type."""
        if v is None:
            return v

        export_type = info.data.get("export_type")

        # For gallery exports, require gallery_ids
        if export_type == "gallery":
            if "gallery_ids" not in v or not v["gallery_ids"]:
                raise ValueError("gallery_ids required for gallery export")
            if not isinstance(v["gallery_ids"], list):
                raise ValueError("gallery_ids must be a list")

        # For selection exports, require asset_ids
        if export_type == "selection":
            if "asset_ids" not in v or not v["asset_ids"]:
                raise ValueError("asset_ids required for selection export")
            if not isinstance(v["asset_ids"], list):
                raise ValueError("asset_ids must be a list")

        return v


class ExportResponse(BaseModel):
    """Response schema for export job."""

    id: str = Field(
        ...,
        description="UUID of the export job",
    )
    workspace_id: str = Field(
        ...,
        description="UUID of the workspace",
    )
    user_id: str = Field(
        ...,
        description="UUID of the user who created the export",
    )
    export_type: str = Field(
        ...,
        description="Type of export (workspace, gallery, selection)",
    )
    status: str = Field(
        ...,
        description="Export job status (pending, processing, completed, failed, cancelled)",
    )
    options: Optional[dict] = Field(
        default=None,
        description="Export options used",
    )
    total_assets: int = Field(
        default=0,
        description="Total number of assets to export",
    )
    processed_assets: int = Field(
        default=0,
        description="Number of assets processed so far",
    )
    progress_percentage: float = Field(
        default=0.0,
        description="Export progress as percentage (0-100)",
    )
    file_url: Optional[str] = Field(
        default=None,
        description="Presigned URL for downloading the export file",
    )
    file_size: Optional[int] = Field(
        default=None,
        description="Size of the export file in bytes",
    )
    file_key: Optional[str] = Field(
        default=None,
        description="R2 storage key for the export file",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if export failed",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the export file will be deleted",
    )
    created_at: datetime = Field(
        ...,
        description="When the export job was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When the export job was last updated",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the export job completed",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "770e8400-e29b-41d4-a716-446655440002",
                "export_type": "workspace",
                "status": "completed",
                "options": {
                    "include_metadata": True,
                    "include_thumbnails": False,
                },
                "total_assets": 1500,
                "processed_assets": 1500,
                "progress_percentage": 100.0,
                "file_url": "https://r2.vdrive.io/exports/workspace-export-123.zip?signature=...",
                "file_size": 524288000,
                "file_key": "exports/workspace-export-123.zip",
                "error_message": None,
                "expires_at": "2026-01-23T10:00:00Z",
                "created_at": "2026-01-16T10:00:00Z",
                "updated_at": "2026-01-16T10:30:00Z",
                "completed_at": "2026-01-16T10:30:00Z",
            }
        }


class ExportStatusResponse(ExportResponse):
    """Response schema for export job status (alias of ExportResponse)."""

    pass


class ExportListResponse(BaseModel):
    """Response schema for listing export jobs."""

    jobs: list[ExportResponse] = Field(
        ...,
        description="List of export jobs",
    )
    total: int = Field(
        ...,
        description="Total number of export jobs",
    )
    page: int = Field(
        default=1,
        description="Current page number",
    )
    page_size: int = Field(
        default=20,
        description="Number of items per page",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "workspace_id": "660e8400-e29b-41d4-a716-446655440001",
                        "user_id": "770e8400-e29b-41d4-a716-446655440002",
                        "export_type": "workspace",
                        "status": "completed",
                        "options": {"include_metadata": True},
                        "total_assets": 1500,
                        "processed_assets": 1500,
                        "progress_percentage": 100.0,
                        "file_url": "https://r2.vdrive.io/exports/workspace-export-123.zip",
                        "file_size": 524288000,
                        "file_key": "exports/workspace-export-123.zip",
                        "error_message": None,
                        "expires_at": "2026-01-23T10:00:00Z",
                        "created_at": "2026-01-16T10:00:00Z",
                        "updated_at": "2026-01-16T10:30:00Z",
                        "completed_at": "2026-01-16T10:30:00Z",
                    }
                ],
                "total": 15,
                "page": 1,
                "page_size": 20,
            }
        }
