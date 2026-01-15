"""WebSocket endpoint for real-time gallery updates."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.share_link_service import ShareLinkService
from ...services.websocket_manager import websocket_manager

logger = structlog.get_logger()
router = APIRouter(prefix="/ws", tags=["websocket"])


async def verify_magic_link_token(
    token: str,
    gallery_id: str,
    db: AsyncSession,
) -> tuple[bool, Optional[str]]:
    """
    Verify a magic link token for WebSocket authentication.

    Args:
        token: Magic link token
        gallery_id: Expected gallery ID
        db: Database session

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, share_link, error_code = await ShareLinkService.verify_link(
        link_id=token,
        password=None,  # Password already verified during initial access
        db=db,
    )

    if not is_valid:
        error_messages = {
            "invalid_link": "Invalid magic link token",
            "expired": "Magic link has expired",
            "password_required": "Gallery requires password",
            "invalid_password": "Invalid password",
        }
        return False, error_messages.get(error_code, "Authentication failed")

    # Verify the token is for the correct gallery
    if str(share_link.gallery_id) != gallery_id:
        return False, "Token does not match gallery"

    return True, None


@router.websocket("/gallery/{gallery_id}")
async def gallery_websocket(
    websocket: WebSocket,
    gallery_id: str,
    token: Optional[str] = Query(None, description="Magic link token for authentication"),
):
    """
    WebSocket endpoint for real-time gallery updates.

    Connection URL: ws://api/v1/ws/gallery/{gallery_id}?token={magic_link_token}

    For public galleries with magic links:
    - Include the magic link token as a query parameter
    - Connection will be authenticated and receive real-time updates

    Messages received:
    - connected: Sent when connection is established
    - photo_added: When a new photo is added to the gallery
    - photo_removed: When a photo is removed from the gallery
    - gallery_updated: When gallery metadata changes
    - error: If an error occurs
    - pong: Response to ping

    Messages can send:
    - ping: Keepalive ping (will receive pong)

    Example connection (JavaScript):
    ```
    const ws = new WebSocket('ws://api/v1/ws/gallery/abc123?token=magic-link-token');
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'photo_added') {
            // Handle new photo
        }
    };
    ```
    """
    connection = None

    try:
        # Validate gallery_id format
        try:
            UUID(gallery_id)
        except ValueError:
            await websocket.close(code=4000, reason="Invalid gallery ID format")
            return

        # Get database session for authentication
        # Note: For WebSocket, we create a session just for auth
        from ...core.database import async_session_factory

        async with async_session_factory() as db:
            # Authenticate if token provided
            is_authenticated = False
            if token:
                is_valid, error_message = await verify_magic_link_token(
                    token=token,
                    gallery_id=gallery_id,
                    db=db,
                )

                if not is_valid:
                    logger.warning(
                        "WebSocket auth failed",
                        gallery_id=gallery_id,
                        error=error_message,
                    )
                    await websocket.close(code=4001, reason=error_message)
                    return

                is_authenticated = True
                logger.info(
                    "WebSocket authenticated via magic link",
                    gallery_id=gallery_id,
                )

        # Register connection
        connection = await websocket_manager.connect(
            websocket=websocket,
            gallery_id=gallery_id,
            user_id=None,  # Anonymous for public galleries
            is_authenticated=is_authenticated,
        )

        # Send connected confirmation
        connection_count = websocket_manager.get_connection_count(gallery_id)
        await websocket_manager.send_to_connection(
            connection,
            {
                "type": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "gallery_id": gallery_id,
                    "connection_id": str(id(connection)),
                    "viewer_count": connection_count,
                    "authenticated": is_authenticated,
                },
            },
        )

        # Broadcast viewer count update to other connections
        await websocket_manager.broadcast_to_gallery(
            gallery_id=gallery_id,
            message={
                "type": "gallery_updated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "update_type": "viewer_count",
                    "viewer_count": connection_count,
                },
            },
            exclude_user_id=None,
        )

        # Main message loop
        while True:
            try:
                # Wait for client messages with timeout for keepalive
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0,  # 60 second timeout
                )

                try:
                    message = json.loads(raw_message)
                    message_type = message.get("type")

                    if message_type == "ping":
                        # Respond to ping
                        await websocket_manager.send_to_connection(
                            connection,
                            {
                                "type": "pong",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                    # Other message types can be added here

                except json.JSONDecodeError:
                    await websocket_manager.send_to_connection(
                        connection,
                        {
                            "type": "error",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "data": {
                                "code": "invalid_json",
                                "message": "Invalid JSON message",
                            },
                        },
                    )

            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception:
                    # Connection likely dead
                    break

    except WebSocketDisconnect:
        logger.info(
            "WebSocket client disconnected",
            gallery_id=gallery_id,
        )

    except Exception as e:
        logger.error(
            "WebSocket error",
            gallery_id=gallery_id,
            error=str(e),
        )

    finally:
        # Cleanup connection
        if connection:
            await websocket_manager.disconnect(connection)

            # Broadcast updated viewer count
            connection_count = websocket_manager.get_connection_count(gallery_id)
            if connection_count > 0:
                await websocket_manager.broadcast_to_gallery(
                    gallery_id=gallery_id,
                    message={
                        "type": "gallery_updated",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data": {
                            "update_type": "viewer_count",
                            "viewer_count": connection_count,
                        },
                    },
                )
