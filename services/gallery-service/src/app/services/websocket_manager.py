"""WebSocket connection manager for real-time gallery updates."""

import asyncio
import json
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger()


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""

    websocket: WebSocket
    gallery_id: str
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_authenticated: bool = False


class WebSocketManager:
    """
    Manages WebSocket connections for real-time gallery updates.

    Features:
    - Connection tracking per gallery
    - Broadcast to all connections in a gallery
    - Redis Pub/Sub integration for multi-instance scaling
    """

    def __init__(self):
        self._connections: dict[str, list[WebSocketConnection]] = {}
        self._redis_client = None
        self._pubsub = None
        self._pubsub_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def initialize(self, redis_client=None) -> None:
        """
        Initialize the WebSocket manager with optional Redis for scaling.

        Args:
            redis_client: Optional Redis client for Pub/Sub
        """
        self._redis_client = redis_client

        if self._redis_client:
            self._pubsub = self._redis_client.pubsub()
            self._pubsub_task = asyncio.create_task(self._listen_pubsub())
            logger.info("WebSocket manager initialized with Redis Pub/Sub")
        else:
            logger.info("WebSocket manager initialized (single instance mode)")

    async def close(self) -> None:
        """Close all connections and cleanup resources."""
        # Cancel pubsub listener
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()

        # Close all WebSocket connections
        for gallery_id, connections in self._connections.items():
            for conn in connections:
                try:
                    await conn.websocket.close()
                except Exception:
                    pass

        self._connections.clear()
        logger.info("WebSocket manager closed")

    async def connect(
        self,
        websocket: WebSocket,
        gallery_id: str,
        user_id: Optional[str] = None,
        is_authenticated: bool = False,
    ) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            gallery_id: Gallery ID to subscribe to
            user_id: Optional user ID
            is_authenticated: Whether connection is authenticated

        Returns:
            WebSocketConnection object
        """
        await websocket.accept()

        connection = WebSocketConnection(
            websocket=websocket,
            gallery_id=gallery_id,
            user_id=user_id,
            is_authenticated=is_authenticated,
        )

        async with self._lock:
            if gallery_id not in self._connections:
                self._connections[gallery_id] = []
                # Subscribe to Redis channel for this gallery
                if self._pubsub:
                    await self._pubsub.subscribe(f"gallery:{gallery_id}")

            self._connections[gallery_id].append(connection)

        logger.info(
            "WebSocket connected",
            gallery_id=gallery_id,
            user_id=user_id,
            total_connections=len(self._connections.get(gallery_id, [])),
        )

        return connection

    async def disconnect(self, connection: WebSocketConnection) -> None:
        """
        Remove a WebSocket connection.

        Args:
            connection: The connection to remove
        """
        async with self._lock:
            gallery_id = connection.gallery_id
            if gallery_id in self._connections:
                self._connections[gallery_id] = [
                    c for c in self._connections[gallery_id]
                    if c.websocket != connection.websocket
                ]

                # Cleanup empty galleries
                if not self._connections[gallery_id]:
                    del self._connections[gallery_id]
                    if self._pubsub:
                        await self._pubsub.unsubscribe(f"gallery:{gallery_id}")

        logger.info(
            "WebSocket disconnected",
            gallery_id=connection.gallery_id,
            user_id=connection.user_id,
        )

    async def send_to_connection(
        self,
        connection: WebSocketConnection,
        message: dict[str, Any],
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection: Target connection
            message: Message to send

        Returns:
            True if sent successfully
        """
        try:
            await connection.websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(
                "Failed to send WebSocket message",
                gallery_id=connection.gallery_id,
                error=str(e),
            )
            return False

    async def broadcast_to_gallery(
        self,
        gallery_id: str,
        message: dict[str, Any],
        exclude_user_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast a message to all connections in a gallery.

        Args:
            gallery_id: Target gallery
            message: Message to broadcast
            exclude_user_id: Optional user ID to exclude

        Returns:
            Number of successful sends
        """
        connections = self._connections.get(gallery_id, [])
        if not connections:
            return 0

        # Also publish to Redis for other instances
        if self._redis_client:
            await self._redis_client.publish(
                f"gallery:{gallery_id}",
                json.dumps(message),
            )
            # Redis will handle delivery to all instances
            return len(connections)

        # Direct delivery for single instance
        sent_count = 0
        failed_connections = []

        for conn in connections:
            if exclude_user_id and conn.user_id == exclude_user_id:
                continue

            if await self.send_to_connection(conn, message):
                sent_count += 1
            else:
                failed_connections.append(conn)

        # Clean up failed connections
        for conn in failed_connections:
            await self.disconnect(conn)

        return sent_count

    async def _listen_pubsub(self) -> None:
        """Listen for Redis Pub/Sub messages and forward to local connections."""
        if not self._pubsub:
            return

        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue

                channel = message["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode("utf-8")

                # Extract gallery_id from channel name
                if channel.startswith("gallery:"):
                    gallery_id = channel[8:]  # Remove "gallery:" prefix
                    data = message["data"]

                    if isinstance(data, bytes):
                        data = json.loads(data.decode("utf-8"))
                    elif isinstance(data, str):
                        data = json.loads(data)

                    # Deliver to local connections
                    connections = self._connections.get(gallery_id, [])
                    for conn in connections:
                        await self.send_to_connection(conn, data)

        except asyncio.CancelledError:
            logger.info("Pub/Sub listener cancelled")
        except Exception as e:
            logger.error("Pub/Sub listener error", error=str(e))

    def get_connection_count(self, gallery_id: Optional[str] = None) -> int:
        """
        Get the number of active connections.

        Args:
            gallery_id: Optional gallery to filter by

        Returns:
            Number of connections
        """
        if gallery_id:
            return len(self._connections.get(gallery_id, []))
        return sum(len(conns) for conns in self._connections.values())

    def get_gallery_ids(self) -> list[str]:
        """Get list of gallery IDs with active connections."""
        return list(self._connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# Message type helpers
def create_photo_added_message(
    asset_id: str,
    thumbnail_url: str,
    position: Optional[int] = None,
) -> dict[str, Any]:
    """Create a photo_added WebSocket message."""
    return {
        "type": "photo_added",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "asset_id": asset_id,
            "thumbnail_url": thumbnail_url,
            "position": position,
        },
    }


def create_photo_removed_message(asset_id: str) -> dict[str, Any]:
    """Create a photo_removed WebSocket message."""
    return {
        "type": "photo_removed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "asset_id": asset_id,
        },
    }


def create_gallery_updated_message(
    update_type: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Create a gallery_updated WebSocket message."""
    return {
        "type": "gallery_updated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "update_type": update_type,
            **data,
        },
    }
