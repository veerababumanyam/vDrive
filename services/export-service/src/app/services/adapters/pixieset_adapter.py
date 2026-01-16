"""
Pixieset platform adapter for migration service.

Handles authentication and data fetching from Pixieset API.
"""

import logging
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

from . import PlatformAdapter

logger = logging.getLogger(__name__)


class PixiesetAdapter(PlatformAdapter):
    """
    Pixieset platform adapter.

    Authenticates using API key and fetches galleries/photos via Pixieset API.
    API Documentation: https://pixieset.com/api/docs (example)
    """

    API_BASE_URL = "https://api.pixieset.com/v1"

    def __init__(self, credentials: dict):
        """
        Initialize Pixieset adapter.

        Args:
            credentials: Must contain 'api_key'
        """
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        if not self.api_key:
            raise ValueError("api_key is required for Pixieset adapter")

        self.client: Optional[httpx.AsyncClient] = None

    async def authenticate(self) -> bool:
        """
        Authenticate with Pixieset API.

        Returns:
            True if authentication succeeds

        Raises:
            Exception if authentication fails
        """
        try:
            # Create HTTP client with API key in headers
            self.client = httpx.AsyncClient(
                base_url=self.API_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )

            # Verify API key by fetching user info
            response = await self.client.get("/user")
            response.raise_for_status()

            logger.info("Successfully authenticated with Pixieset API")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Pixieset authentication failed: {e}")
            raise Exception(f"Invalid Pixieset API key: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Pixieset authentication error: {e}")
            raise

    async def get_galleries(
        self, gallery_ids: Optional[list[str]] = None
    ) -> AsyncIterator[dict]:
        """
        Fetch galleries from Pixieset.

        Args:
            gallery_ids: Optional list of specific gallery IDs

        Yields:
            Gallery metadata dict
        """
        if not self.client:
            raise RuntimeError("Must call authenticate() before fetching galleries")

        try:
            # Fetch galleries with pagination
            page = 1
            page_size = 50

            while True:
                response = await self.client.get(
                    "/galleries",
                    params={"page": page, "per_page": page_size},
                )
                response.raise_for_status()
                data = response.json()

                galleries = data.get("galleries", [])
                if not galleries:
                    break

                for gallery in galleries:
                    # Filter by gallery_ids if specified
                    if gallery_ids and gallery["id"] not in gallery_ids:
                        continue

                    # Transform to vDrive format
                    yield {
                        "id": gallery["id"],
                        "name": gallery.get("name", "Untitled Gallery"),
                        "description": gallery.get("description"),
                        "created_at": datetime.fromisoformat(
                            gallery.get("created_at", datetime.now().isoformat())
                        ),
                        "photo_count": gallery.get("photo_count", 0),
                    }

                # Check if there are more pages
                if len(galleries) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Pixieset galleries: {e}")
            raise Exception(f"Pixieset API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Pixieset galleries: {e}")
            raise

    async def get_photos(self, gallery_id: str) -> AsyncIterator[dict]:
        """
        Fetch photos from a Pixieset gallery.

        Args:
            gallery_id: Gallery ID to fetch photos from

        Yields:
            Photo metadata dict
        """
        if not self.client:
            raise RuntimeError("Must call authenticate() before fetching photos")

        try:
            # Fetch photos with pagination
            page = 1
            page_size = 100

            while True:
                response = await self.client.get(
                    f"/galleries/{gallery_id}/photos",
                    params={"page": page, "per_page": page_size},
                )
                response.raise_for_status()
                data = response.json()

                photos = data.get("photos", [])
                if not photos:
                    break

                for photo in photos:
                    # Transform to vDrive format
                    yield {
                        "id": photo["id"],
                        "filename": photo.get("filename", f"{photo['id']}.jpg"),
                        "url": photo.get("download_url") or photo.get("original_url"),
                        "thumbnail_url": photo.get("thumbnail_url"),
                        "metadata": {
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0),
                            "size": photo.get("file_size", 0),
                            "created_at": datetime.fromisoformat(
                                photo.get("created_at", datetime.now().isoformat())
                            ),
                            "exif": photo.get("exif", {}),
                        },
                    }

                # Check if there are more pages
                if len(photos) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Pixieset photos for gallery {gallery_id}: {e}")
            raise Exception(f"Pixieset API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Pixieset photos: {e}")
            raise

    async def download_photo(self, photo_url: str) -> bytes:
        """
        Download photo file from Pixieset.

        Args:
            photo_url: URL to download photo from

        Returns:
            Photo file content as bytes
        """
        if not self.client:
            raise RuntimeError("Must call authenticate() before downloading photos")

        try:
            response = await self.client.get(photo_url)
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to download photo from {photo_url}: {e}")
            raise Exception(f"Pixieset download error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            raise

    async def close(self) -> None:
        """Clean up HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
