"""Pydantic schemas for batch operations."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BatchOperationType(str, Enum):
    """Types of batch operations."""

    # Asset operations
    ADD_TO_GALLERY = "add_to_gallery"
    REMOVE_FROM_GALLERY = "remove_from_gallery"
    MOVE_TO_GALLERY = "move_to_gallery"
    COPY_TO_GALLERY = "copy_to_gallery"

    # Visibility operations
    SHOW_ASSETS = "show_assets"
    HIDE_ASSETS = "hide_assets"
    SET_FAVORITES = "set_favorites"
    UNSET_FAVORITES = "unset_favorites"

    # Gallery operations
    DELETE_GALLERIES = "delete_galleries"
    ARCHIVE_GALLERIES = "archive_galleries"
    PUBLISH_GALLERIES = "publish_galleries"
    UNPUBLISH_GALLERIES = "unpublish_galleries"


class BatchRequest(BaseModel):
    """Request for batch operation."""

    operation: BatchOperationType = Field(..., description="Type of batch operation")
    target_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="IDs of items to operate on (max 1000)",
    )
    destination_id: Optional[UUID] = Field(
        None, description="Target gallery for move/copy/add operations"
    )

    @field_validator("target_ids")
    @classmethod
    def validate_unique_ids(cls, v: list[UUID]) -> list[UUID]:
        """Ensure all IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate IDs in target_ids")
        return v


class BatchError(BaseModel):
    """Error details for a single item in batch."""

    id: Optional[str] = Field(None, description="ID of item that failed")
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")


class BatchResponse(BaseModel):
    """Response for batch operation."""

    operation: BatchOperationType
    total_requested: int = Field(..., description="Number of items requested")
    successful: int = Field(..., description="Number of successfully processed items")
    failed: int = Field(..., description="Number of failed items")
    errors: list[BatchError] = Field(
        default_factory=list, description="Error details for failed items"
    )
    processed_ids: list[str] = Field(
        default_factory=list, description="IDs of successfully processed items"
    )
    started_at: datetime
    completed_at: datetime
    duration_seconds: float = Field(..., description="Operation duration in seconds")


class BatchStatusResponse(BaseModel):
    """Status of a long-running batch operation."""

    batch_id: UUID
    operation: BatchOperationType
    status: str = Field(..., description="pending, processing, completed, failed")
    total_items: int
    processed_items: int
    progress_percent: float = Field(ge=0, le=100)
    started_at: datetime
    completed_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[float] = None


class BatchOperationSummary(BaseModel):
    """Summary of available batch operations."""

    operation: BatchOperationType
    description: str
    requires_destination: bool = Field(
        default=False, description="Whether destination_id is required"
    )
    supports_assets: bool = Field(default=True, description="Can operate on assets")
    supports_galleries: bool = Field(
        default=False, description="Can operate on galleries"
    )


# Pre-defined operation summaries
BATCH_OPERATIONS = [
    BatchOperationSummary(
        operation=BatchOperationType.ADD_TO_GALLERY,
        description="Add assets to a gallery",
        requires_destination=True,
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.REMOVE_FROM_GALLERY,
        description="Remove assets from a gallery",
        requires_destination=True,
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.MOVE_TO_GALLERY,
        description="Move assets to a different gallery",
        requires_destination=True,
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.COPY_TO_GALLERY,
        description="Copy assets to another gallery",
        requires_destination=True,
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.SHOW_ASSETS,
        description="Make assets visible in galleries",
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.HIDE_ASSETS,
        description="Hide assets from galleries",
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.SET_FAVORITES,
        description="Mark assets as favorites",
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.UNSET_FAVORITES,
        description="Remove favorite status from assets",
        supports_assets=True,
        supports_galleries=False,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.DELETE_GALLERIES,
        description="Delete galleries and their asset associations",
        supports_assets=False,
        supports_galleries=True,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.ARCHIVE_GALLERIES,
        description="Archive galleries",
        supports_assets=False,
        supports_galleries=True,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.PUBLISH_GALLERIES,
        description="Publish galleries for public access",
        supports_assets=False,
        supports_galleries=True,
    ),
    BatchOperationSummary(
        operation=BatchOperationType.UNPUBLISH_GALLERIES,
        description="Unpublish galleries",
        supports_assets=False,
        supports_galleries=True,
    ),
]
