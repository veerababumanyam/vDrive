"""
Platform adapters for migration service.

Each adapter handles platform-specific API/CSV import logic for different
photography platforms (Pixieset, Pic-Time, ShootProof, Zenfolio, SmugMug).
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class PlatformAdapter(ABC):
    """
    Base class for platform adapters.

    Each platform adapter implements methods to:
    - Authenticate with the platform
    - Fetch gallery metadata
    - Fetch photo metadata and files
    - Transform data to vDrive format
    """

    def __init__(self, credentials: dict):
        """
        Initialize platform adapter.

        Args:
            credentials: Platform-specific credentials (API keys, tokens, etc.)
        """
        self.credentials = credentials

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the platform using provided credentials.

        Returns:
            True if authentication succeeds, False otherwise

        Raises:
            Exception if authentication fails
        """
        pass

    @abstractmethod
    async def get_galleries(
        self, gallery_ids: Optional[list[str]] = None
    ) -> AsyncIterator[dict]:
        """
        Fetch galleries from the platform.

        Args:
            gallery_ids: Optional list of specific gallery IDs to fetch.
                        If None, fetch all galleries.

        Yields:
            Gallery metadata dict with structure:
            {
                "id": str,
                "name": str,
                "description": Optional[str],
                "created_at": datetime,
                "photo_count": int,
            }
        """
        pass

    @abstractmethod
    async def get_photos(
        self, gallery_id: str
    ) -> AsyncIterator[dict]:
        """
        Fetch photos from a specific gallery.

        Args:
            gallery_id: Gallery ID to fetch photos from

        Yields:
            Photo metadata dict with structure:
            {
                "id": str,
                "filename": str,
                "url": str,  # Download URL for original file
                "thumbnail_url": Optional[str],
                "metadata": {
                    "width": int,
                    "height": int,
                    "size": int,
                    "created_at": datetime,
                    "exif": dict,
                },
            }
        """
        pass

    @abstractmethod
    async def download_photo(self, photo_url: str) -> bytes:
        """
        Download photo file from platform.

        Args:
            photo_url: URL to download photo from

        Returns:
            Photo file content as bytes

        Raises:
            Exception if download fails
        """
        pass

    async def close(self) -> None:
        """
        Clean up any resources (HTTP clients, connections, etc.).

        Override this method if your adapter needs cleanup.
        """
        pass
