"""
ShootProof platform adapter for migration service.

Handles authentication and data fetching from ShootProof API.
"""

import logging
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

from . import PlatformAdapter

logger = logging.getLogger(__name__)


class ShootproofAdapter(PlatformAdapter):
    """
    ShootProof platform adapter.

    Authenticates using username/password and fetches galleries/photos via ShootProof API.
    API Documentation: https://shootproof.com/api/docs (example)
    """

    API_BASE_URL = "https://api.shootproof.com/v2"

    def __init__(self, credentials: dict):
        """
        Initialize ShootProof adapter.

        Args:
            credentials: Must contain 'username' and 'password'
        """
        super().__init__(credentials)
        self.username = credentials.get("username")
        self.password = credentials.get("password")

        if not self.username or not self.password:
            raise ValueError("username and password are required for ShootProof adapter")

        self.client: Optional[httpx.AsyncClient] = None
        self.session_token: Optional[str] = None

    async def authenticate(self) -> bool:
        """
        Authenticate with ShootProof API.

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

            # Login to get session token
            response = await self.client.post(
                "/auth/login",
                json={
                    "email": self.username,  # ShootProof uses email
                    "password": self.password,
                },
            )
            response.raise_for_status()
            data = response.json()

            self.session_token = data.get("token")
            if not self.session_token:
                raise Exception("No session token in response")

            # Update client headers with token
            self.client.headers.update({
                "X-Auth-Token": self.session_token,
            })

            logger.info("Successfully authenticated with ShootProof API")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"ShootProof authentication failed: {e}")
            raise Exception(f"Invalid ShootProof credentials: {e.response.status_code}")
        except Exception as e:
            logger.error(f"ShootProof authentication error: {e}")
            raise

    async def get_galleries(
        self, gallery_ids: Optional[list[str]] = None
    ) -> AsyncIterator[dict]:
        """
        Fetch galleries from ShootProof.

        Args:
            gallery_ids: Optional list of specific gallery IDs

        Yields:
            Gallery metadata dict
        """
        if not self.client or not self.session_token:
            raise RuntimeError("Must call authenticate() before fetching galleries")

        try:
            # Fetch events (ShootProof's term for galleries)
            page = 1
            page_size = 50

            while True:
                response = await self.client.get(
                    "/events",
                    params={"page": page, "per_page": page_size},
                )
                response.raise_for_status()
                data = response.json()

                events = data.get("events", [])
                if not events:
                    break

                for event in events:
                    event_id = str(event["id"])

                    # Filter by gallery_ids if specified
                    if gallery_ids and event_id not in gallery_ids:
                        continue

                    # Transform to vDrive format
                    yield {
                        "id": event_id,
                        "name": event.get("event_name", "Untitled Event"),
                        "description": event.get("description"),
                        "created_at": datetime.fromisoformat(
                            event.get("created_at", datetime.now().isoformat())
                        ),
                        "photo_count": event.get("photo_count", 0),
                    }

                # Check if there are more pages
                if len(events) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch ShootProof galleries: {e}")
            raise Exception(f"ShootProof API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching ShootProof galleries: {e}")
            raise

    async def get_photos(self, gallery_id: str) -> AsyncIterator[dict]:
        """
        Fetch photos from a ShootProof event.

        Args:
            gallery_id: Event ID to fetch photos from

        Yields:
            Photo metadata dict
        """
        if not self.client or not self.session_token:
            raise RuntimeError("Must call authenticate() before fetching photos")

        try:
            # Fetch photos with pagination
            page = 1
            page_size = 100

            while True:
                response = await self.client.get(
                    f"/events/{gallery_id}/photos",
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
                        "id": str(photo["id"]),
                        "filename": photo.get("file_name", f"{photo['id']}.jpg"),
                        "url": photo.get("download_url") or photo.get("original_url"),
                        "thumbnail_url": photo.get("thumb_url"),
                        "metadata": {
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0),
                            "size": photo.get("file_size", 0),
                            "created_at": datetime.fromisoformat(
                                photo.get("uploaded_at", datetime.now().isoformat())
                            ),
                            "exif": photo.get("exif", {}),
                        },
                    }

                # Check if there are more pages
                if len(photos) < page_size:
                    break
                page += 1

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch ShootProof photos for event {gallery_id}: {e}")
            raise Exception(f"ShootProof API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching ShootProof photos: {e}")
            raise

    async def download_photo(self, photo_url: str) -> bytes:
        """
        Download photo file from ShootProof.

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
            raise Exception(f"ShootProof download error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            raise

    async def close(self) -> None:
        """Clean up HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.session_token = None
