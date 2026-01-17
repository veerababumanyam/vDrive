"""
Pic-Time platform adapter for migration service.

Handles authentication and data fetching from Pic-Time API.
"""

import logging
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

from . import PlatformAdapter

logger = logging.getLogger(__name__)


class PictimeAdapter(PlatformAdapter):
    """
    Pic-Time platform adapter.

    Authenticates using username/password and fetches galleries/photos via Pic-Time API.
    API Documentation: https://pic-time.com/api/docs (example)
    """

    API_BASE_URL = "https://api.pic-time.com/v2"

    def __init__(self, credentials: dict):
        """
        Initialize Pic-Time adapter.

        Args:
            credentials: Must contain 'username' and 'password'
        """
        super().__init__(credentials)
        self.username = credentials.get("username")
        self.password = credentials.get("password")

        if not self.username or not self.password:
            raise ValueError("username and password are required for Pic-Time adapter")

        self.client: Optional[httpx.AsyncClient] = None
        self.access_token: Optional[str] = None

    async def authenticate(self) -> bool:
        """
        Authenticate with Pic-Time API.

        Returns:
            True if authentication succeeds

        Raises:
            Exception if authentication fails
        """
        try:
            # Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.API_BASE_URL,
                headers={"Accept": "application/json"},
                timeout=30.0,
            )

            # Login to get access token
            response = await self.client.post(
                "/auth/login",
                json={
                    "username": self.username,
                    "password": self.password,
                },
            )
            response.raise_for_status()
            data = response.json()

            self.access_token = data.get("access_token")
            if not self.access_token:
                raise Exception("No access token in response")

            # Update client headers with token
            self.client.headers.update({
                "Authorization": f"Bearer {self.access_token}",
            })

            logger.info("Successfully authenticated with Pic-Time API")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Pic-Time authentication failed: {e}")
            raise Exception(f"Invalid Pic-Time credentials: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Pic-Time authentication error: {e}")
            raise

    async def get_galleries(
        self, gallery_ids: Optional[list[str]] = None
    ) -> AsyncIterator[dict]:
        """
        Fetch galleries from Pic-Time.

        Args:
            gallery_ids: Optional list of specific gallery IDs

        Yields:
            Gallery metadata dict
        """
        if not self.client or not self.access_token:
            raise RuntimeError("Must call authenticate() before fetching galleries")

        try:
            # Fetch galleries with pagination
            page = 1
            page_size = 50

            while True:
                response = await self.client.get(
                    "/galleries",
                    params={"page": page, "limit": page_size},
                )
                response.raise_for_status()
                data = response.json()

                galleries = data.get("data", [])
                if not galleries:
                    break

                for gallery in galleries:
                    # Filter by gallery_ids if specified
                    if gallery_ids and gallery["id"] not in gallery_ids:
                        continue

                    # Transform to vDrive format
                    yield {
                        "id": gallery["id"],
                        "name": gallery.get("title", "Untitled Gallery"),
                        "description": gallery.get("description"),
                        "created_at": datetime.fromisoformat(
                            gallery.get("date_created", datetime.now().isoformat())
                        ),
                        "photo_count": gallery.get("image_count", 0),
                    }

                # Check if there are more pages
                if len(galleries) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Pic-Time galleries: {e}")
            raise Exception(f"Pic-Time API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Pic-Time galleries: {e}")
            raise

    async def get_photos(self, gallery_id: str) -> AsyncIterator[dict]:
        """
        Fetch photos from a Pic-Time gallery.

        Args:
            gallery_id: Gallery ID to fetch photos from

        Yields:
            Photo metadata dict
        """
        if not self.client or not self.access_token:
            raise RuntimeError("Must call authenticate() before fetching photos")

        try:
            # Fetch photos with pagination
            page = 1
            page_size = 100

            while True:
                response = await self.client.get(
                    f"/galleries/{gallery_id}/images",
                    params={"page": page, "limit": page_size},
                )
                response.raise_for_status()
                data = response.json()

                photos = data.get("data", [])
                if not photos:
                    break

                for photo in photos:
                    # Transform to vDrive format
                    yield {
                        "id": photo["id"],
                        "filename": photo.get("name", f"{photo['id']}.jpg"),
                        "url": photo.get("url_original") or photo.get("url"),
                        "thumbnail_url": photo.get("url_thumb"),
                        "metadata": {
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0),
                            "size": photo.get("size", 0),
                            "created_at": datetime.fromisoformat(
                                photo.get("date_uploaded", datetime.now().isoformat())
                            ),
                            "exif": photo.get("exif_data", {}),
                        },
                    }

                # Check if there are more pages
                if len(photos) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Pic-Time photos for gallery {gallery_id}: {e}")
            raise Exception(f"Pic-Time API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Pic-Time photos: {e}")
            raise

    async def download_photo(self, photo_url: str) -> bytes:
        """
        Download photo file from Pic-Time.

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
            raise Exception(f"Pic-Time download error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            raise

    async def close(self) -> None:
        """Clean up HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.access_token = None
