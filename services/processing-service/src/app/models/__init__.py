"""SQLAlchemy models for Processing Service.

These models match the database schema created by upload-service migrations.
Both services interact with the same database tables independently.
"""

from .asset import Asset, ProcessingStatus
from .asset_metadata import AssetMetadata
from .face import Face
from .processing_task import ProcessingTask, TaskType, TaskStatus

__all__ = [
    "Asset",
    "ProcessingStatus",
    "AssetMetadata",
    "Face",
    "ProcessingTask",
    "TaskType",
    "TaskStatus",
]
