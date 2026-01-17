"""
SQLAlchemy models for Gallery Service.

All models extend the shared Base for consistent table creation.
"""

from src.app.core.database import Base
from src.app.models.asset import Asset
from src.app.models.gallery import Gallery

__all__ = [
    "Base",
    "Gallery",
    "Asset",
]
