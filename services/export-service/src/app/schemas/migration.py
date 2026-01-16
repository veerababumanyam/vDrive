"""
Migration schemas for importing data from competitor platforms.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MigrationCreateRequest(BaseModel):
    """Request schema for creating a migration job."""

    platform: str = Field(
        ...,
        description="Source platform (pixieset, pic-time, shootproof, zenfolio, smugmug)",
        examples=["pixieset"],
    )
    credentials: dict = Field(
        ...,
        description="Platform credentials (API key, username/password, etc.)",
        examples=[
            {
                "api_key": "pk_live_1234567890",
            }
        ],
    )
    options: Optional[dict] = Field(
        default=None,
        description="Migration options (gallery_ids, import_metadata, etc.)",
        examples=[
            {
                "import_metadata": True,
                "import_thumbnails": True,
                "gallery_ids": ["gallery-1", "gallery-2"],
            }
        ],
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform is one of the supported values."""
        allowed_platforms = ["pixieset", "pic-time", "shootproof", "zenfolio", "smugmug"]
        if v not in allowed_platforms:
            raise ValueError(
                f"platform must be one of {allowed_platforms}, got '{v}'"
            )
        return v

    @field_validator("credentials")
    @classmethod
    def validate_credentials(cls, v: dict, info) -> dict:
        """Validate credentials based on platform."""
        if not v:
            raise ValueError("credentials are required")

        platform = info.data.get("platform")

        # Platform-specific credential validation
        if platform == "pixieset":
            if "api_key" not in v:
                raise ValueError("api_key required for Pixieset")
        elif platform in ["pic-time", "shootproof"]:
            if "username" not in v or "password" not in v:
                raise ValueError("username and password required for this platform")
        elif platform in ["zenfolio", "smugmug"]:
            if "api_key" not in v or "api_secret" not in v:
                raise ValueError("api_key and api_secret required for this platform")

        return v


class MigrationResponse(BaseModel):
    """Response schema for migration job."""

    id: str = Field(
        ...,
        description="UUID of the migration job",
    )
    workspace_id: str = Field(
        ...,
        description="UUID of the workspace",
    )
    user_id: str = Field(
        ...,
        description="UUID of the user who created the migration",
    )
    platform: str = Field(
        ...,
        description="Source platform (pixieset, pic-time, shootproof, zenfolio, smugmug)",
    )
    status: str = Field(
        ...,
        description="Migration job status (pending, processing, completed, failed, cancelled)",
    )
    options: Optional[dict] = Field(
        default=None,
        description="Migration options used",
    )
    total_assets: int = Field(
        default=0,
        description="Total number of assets to import",
    )
    processed_assets: int = Field(
        default=0,
        description="Number of assets processed so far",
    )
    total_galleries: int = Field(
        default=0,
        description="Total number of galleries to import",
    )
    processed_galleries: int = Field(
        default=0,
        description="Number of galleries processed so far",
    )
    progress_percentage: float = Field(
        default=0.0,
        description="Migration progress as percentage (0-100)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if migration failed",
    )
    created_at: datetime = Field(
        ...,
        description="When the migration job was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When the migration job was last updated",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the migration job completed",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "770e8400-e29b-41d4-a716-446655440002",
                "platform": "pixieset",
                "status": "completed",
                "options": {
                    "import_metadata": True,
                    "import_thumbnails": True,
                },
                "total_assets": 500,
                "processed_assets": 500,
                "total_galleries": 10,
                "processed_galleries": 10,
                "progress_percentage": 100.0,
                "error_message": None,
                "created_at": "2026-01-16T10:00:00Z",
                "updated_at": "2026-01-16T11:00:00Z",
                "completed_at": "2026-01-16T11:00:00Z",
            }
        }


class MigrationStatusResponse(MigrationResponse):
    """Response schema for migration job status (alias of MigrationResponse)."""

    pass


class MigrationListResponse(BaseModel):
    """Response schema for listing migration jobs."""

    jobs: list[MigrationResponse] = Field(
        ...,
        description="List of migration jobs",
    )
    total: int = Field(
        ...,
        description="Total number of migration jobs",
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
                        "platform": "pixieset",
                        "status": "completed",
                        "options": {"import_metadata": True},
                        "total_assets": 500,
                        "processed_assets": 500,
                        "total_galleries": 10,
                        "processed_galleries": 10,
                        "progress_percentage": 100.0,
                        "error_message": None,
                        "created_at": "2026-01-16T10:00:00Z",
                        "updated_at": "2026-01-16T11:00:00Z",
                        "completed_at": "2026-01-16T11:00:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
            }
        }
