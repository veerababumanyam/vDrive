"""Pydantic schemas for WebSocket messages."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""

    # Server -> Client
    CONNECTED = "connected"
    PHOTO_ADDED = "photo_added"
    PHOTO_REMOVED = "photo_removed"
    GALLERY_UPDATED = "gallery_updated"
    ERROR = "error"
    PONG = "pong"

    # Client -> Server
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class PhotoAddedData(BaseModel):
    """Data for photo_added message."""

    asset_id: UUID = Field(..., description="Added photo asset ID")
    thumbnail_url: str = Field(default="", description="Thumbnail URL")
    position: Optional[int] = Field(None, description="Position in gallery")


class PhotoRemovedData(BaseModel):
    """Data for photo_removed message."""

    asset_id: UUID = Field(..., description="Removed photo asset ID")


class GalleryUpdatedData(BaseModel):
    """Data for gallery_updated message."""

    update_type: str = Field(
        ...,
        description="Type of update: name, cover, settings, published",
    )
    name: Optional[str] = Field(None, description="New gallery name")
    cover_asset_id: Optional[UUID] = Field(None, description="New cover photo")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")


class ConnectionInfo(BaseModel):
    """Data for connected message."""

    gallery_id: UUID = Field(..., description="Gallery ID")
    connection_id: str = Field(..., description="Connection identifier")
    viewer_count: int = Field(default=1, description="Current viewer count")


class ErrorData(BaseModel):
    """Data for error message."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""

    type: WebSocketMessageType = Field(..., description="Message type")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )
    data: Optional[dict[str, Any]] = Field(None, description="Message data")


class WebSocketConnectedMessage(WebSocketMessage):
    """Connected confirmation message."""

    type: Literal[WebSocketMessageType.CONNECTED] = WebSocketMessageType.CONNECTED
    data: ConnectionInfo


class WebSocketPhotoAddedMessage(WebSocketMessage):
    """Photo added notification."""

    type: Literal[WebSocketMessageType.PHOTO_ADDED] = WebSocketMessageType.PHOTO_ADDED
    data: PhotoAddedData


class WebSocketPhotoRemovedMessage(WebSocketMessage):
    """Photo removed notification."""

    type: Literal[WebSocketMessageType.PHOTO_REMOVED] = WebSocketMessageType.PHOTO_REMOVED
    data: PhotoRemovedData


class WebSocketGalleryUpdatedMessage(WebSocketMessage):
    """Gallery metadata update notification."""

    type: Literal[WebSocketMessageType.GALLERY_UPDATED] = WebSocketMessageType.GALLERY_UPDATED
    data: GalleryUpdatedData


class WebSocketErrorMessage(WebSocketMessage):
    """Error notification."""

    type: Literal[WebSocketMessageType.ERROR] = WebSocketMessageType.ERROR
    data: ErrorData


# Client message schemas
class ClientPingMessage(BaseModel):
    """Client ping for keepalive."""

    type: Literal["ping"] = "ping"


class ClientSubscribeMessage(BaseModel):
    """Client subscribe to additional gallery (future use)."""

    type: Literal["subscribe"] = "subscribe"
    gallery_id: UUID = Field(..., description="Gallery to subscribe to")


class MagicLinkAuth(BaseModel):
    """Magic link authentication for WebSocket."""

    token: str = Field(..., description="Magic link token")
    gallery_id: UUID = Field(..., description="Gallery ID from magic link")


class WebSocketAuthResponse(BaseModel):
    """Authentication response for WebSocket connection."""

    authenticated: bool = Field(..., description="Whether authentication succeeded")
    gallery_id: Optional[UUID] = Field(None, description="Authenticated gallery ID")
    expires_at: Optional[datetime] = Field(None, description="Token expiration")
    error: Optional[str] = Field(None, description="Error message if failed")
