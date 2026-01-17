"""Tests for WebSocket connection manager service."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.services.websocket_manager import (
    WebSocketConnection,
    WebSocketManager,
    create_gallery_updated_message,
    create_photo_added_message,
    create_photo_removed_message,
)


class TestWebSocketConnection:
    """Test WebSocketConnection dataclass."""

    def test_create_connection(self):
        """Test creating a WebSocket connection."""
        mock_ws = MagicMock()
        conn = WebSocketConnection(
            websocket=mock_ws,
            gallery_id="test-gallery",
            user_id="user-123",
            is_authenticated=True,
        )

        assert conn.websocket == mock_ws
        assert conn.gallery_id == "test-gallery"
        assert conn.user_id == "user-123"
        assert conn.is_authenticated is True
        assert isinstance(conn.connected_at, datetime)

    def test_connection_defaults(self):
        """Test WebSocketConnection default values."""
        mock_ws = MagicMock()
        conn = WebSocketConnection(
            websocket=mock_ws,
            gallery_id="test-gallery",
        )

        assert conn.user_id is None
        assert conn.is_authenticated is False
        assert conn.connected_at is not None


@pytest.mark.asyncio
class TestWebSocketManagerInit:
    """Test WebSocketManager initialization."""

    async def test_init_creates_empty_connections(self):
        """Test manager initializes with empty connections."""
        manager = WebSocketManager()

        assert manager._connections == {}
        assert manager._redis_client is None
        assert manager._pubsub is None

    async def test_initialize_without_redis(self):
        """Test initialization without Redis client."""
        manager = WebSocketManager()
        await manager.initialize()

        assert manager._redis_client is None
        assert manager._pubsub is None
        assert manager._pubsub_task is None

    async def test_initialize_with_redis(self):
        """Test initialization with Redis client."""
        manager = WebSocketManager()
        mock_redis = MagicMock()  # Not AsyncMock - pubsub() is sync
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        # Mock the listen method as async generator
        async def mock_listen():
            # Yield nothing and exit immediately
            if False:
                yield  # Make it an async generator

        mock_pubsub.listen.return_value = mock_listen()

        await manager.initialize(redis_client=mock_redis)

        assert manager._redis_client == mock_redis
        assert manager._pubsub == mock_pubsub

        # Cleanup
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
class TestWebSocketManagerConnect:
    """Test WebSocketManager connect functionality."""

    async def test_connect_new_gallery(self):
        """Test connecting to a new gallery."""
        manager = WebSocketManager()
        mock_ws = AsyncMock()

        connection = await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
            user_id="user-1",
            is_authenticated=True,
        )

        mock_ws.accept.assert_called_once()
        assert connection.gallery_id == "gallery-1"
        assert connection.user_id == "user-1"
        assert connection.is_authenticated is True
        assert "gallery-1" in manager._connections
        assert len(manager._connections["gallery-1"]) == 1

    async def test_connect_multiple_to_same_gallery(self):
        """Test multiple connections to same gallery."""
        manager = WebSocketManager()

        for i in range(3):
            mock_ws = AsyncMock()
            await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
                user_id=f"user-{i}",
            )

        assert len(manager._connections["gallery-1"]) == 3

    async def test_connect_to_different_galleries(self):
        """Test connections to different galleries."""
        manager = WebSocketManager()

        await manager.connect(
            websocket=AsyncMock(),
            gallery_id="gallery-1",
        )
        await manager.connect(
            websocket=AsyncMock(),
            gallery_id="gallery-2",
        )

        assert "gallery-1" in manager._connections
        assert "gallery-2" in manager._connections
        assert len(manager._connections) == 2

    async def test_connect_subscribes_to_redis(self):
        """Test connecting subscribes to Redis channel."""
        manager = WebSocketManager()
        mock_redis = MagicMock()  # Not AsyncMock - pubsub() is sync
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        async def mock_listen():
            if False:
                yield

        mock_pubsub.listen.return_value = mock_listen()

        await manager.initialize(redis_client=mock_redis)

        mock_ws = AsyncMock()
        await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
        )

        mock_pubsub.subscribe.assert_called_with("gallery:gallery-1")

        # Cleanup
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
class TestWebSocketManagerDisconnect:
    """Test WebSocketManager disconnect functionality."""

    async def test_disconnect_removes_connection(self):
        """Test disconnecting removes the connection."""
        manager = WebSocketManager()
        mock_ws = AsyncMock()

        connection = await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
        )
        assert len(manager._connections["gallery-1"]) == 1

        await manager.disconnect(connection)
        assert "gallery-1" not in manager._connections

    async def test_disconnect_one_of_many(self):
        """Test disconnecting one connection leaves others."""
        manager = WebSocketManager()

        connections = []
        for i in range(3):
            mock_ws = AsyncMock()
            conn = await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
            )
            connections.append(conn)

        await manager.disconnect(connections[0])
        assert len(manager._connections["gallery-1"]) == 2

    async def test_disconnect_unsubscribes_from_redis_when_empty(self):
        """Test disconnecting last connection unsubscribes from Redis."""
        manager = WebSocketManager()
        mock_redis = MagicMock()  # Not AsyncMock - pubsub() is sync
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        async def mock_listen():
            if False:
                yield

        mock_pubsub.listen.return_value = mock_listen()

        await manager.initialize(redis_client=mock_redis)

        mock_ws = AsyncMock()
        connection = await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
        )

        await manager.disconnect(connection)
        mock_pubsub.unsubscribe.assert_called_with("gallery:gallery-1")

        # Cleanup
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
class TestWebSocketManagerSend:
    """Test WebSocketManager send functionality."""

    async def test_send_to_connection_success(self):
        """Test sending message to connection."""
        manager = WebSocketManager()
        mock_ws = AsyncMock()

        connection = await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
        )

        result = await manager.send_to_connection(
            connection,
            {"type": "test", "data": "hello"},
        )

        assert result is True
        mock_ws.send_json.assert_called_once_with({"type": "test", "data": "hello"})

    async def test_send_to_connection_failure(self):
        """Test sending message fails gracefully."""
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")

        connection = await manager.connect(
            websocket=mock_ws,
            gallery_id="gallery-1",
        )

        result = await manager.send_to_connection(
            connection,
            {"type": "test"},
        )

        assert result is False


@pytest.mark.asyncio
class TestWebSocketManagerBroadcast:
    """Test WebSocketManager broadcast functionality."""

    async def test_broadcast_to_empty_gallery(self):
        """Test broadcasting to gallery with no connections."""
        manager = WebSocketManager()

        count = await manager.broadcast_to_gallery(
            "nonexistent-gallery",
            {"type": "test"},
        )

        assert count == 0

    async def test_broadcast_to_gallery(self):
        """Test broadcasting to all connections in gallery."""
        manager = WebSocketManager()

        mock_sockets = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_sockets.append(mock_ws)
            await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
            )

        message = {"type": "test", "data": "hello"}
        count = await manager.broadcast_to_gallery("gallery-1", message)

        assert count == 3
        for mock_ws in mock_sockets:
            mock_ws.send_json.assert_called_once_with(message)

    async def test_broadcast_excludes_user(self):
        """Test broadcasting excludes specified user."""
        manager = WebSocketManager()

        connections = []
        for i in range(3):
            mock_ws = AsyncMock()
            conn = await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
                user_id=f"user-{i}",
            )
            connections.append(conn)

        message = {"type": "test"}
        count = await manager.broadcast_to_gallery(
            "gallery-1",
            message,
            exclude_user_id="user-1",
        )

        assert count == 2
        # User 0 and 2 should receive, user 1 excluded
        connections[0].websocket.send_json.assert_called_once()
        connections[1].websocket.send_json.assert_not_called()
        connections[2].websocket.send_json.assert_called_once()

    async def test_broadcast_cleans_up_failed_connections(self):
        """Test broadcast removes failed connections."""
        manager = WebSocketManager()

        mock_ws_good = AsyncMock()
        mock_ws_bad = AsyncMock()
        mock_ws_bad.send_json.side_effect = Exception("Connection lost")

        await manager.connect(
            websocket=mock_ws_good,
            gallery_id="gallery-1",
        )
        await manager.connect(
            websocket=mock_ws_bad,
            gallery_id="gallery-1",
        )

        assert len(manager._connections["gallery-1"]) == 2

        await manager.broadcast_to_gallery("gallery-1", {"type": "test"})

        # Failed connection should be cleaned up
        assert len(manager._connections["gallery-1"]) == 1

    async def test_broadcast_with_redis_publishes(self):
        """Test broadcast with Redis publishes to channel."""
        manager = WebSocketManager()
        mock_redis = MagicMock()  # Not AsyncMock - pubsub() is sync
        mock_redis.publish = AsyncMock()  # publish is async
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        async def mock_listen():
            if False:
                yield

        mock_pubsub.listen.return_value = mock_listen()
        await manager.initialize(redis_client=mock_redis)

        await manager.connect(
            websocket=AsyncMock(),
            gallery_id="gallery-1",
        )

        message = {"type": "test"}
        await manager.broadcast_to_gallery("gallery-1", message)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "gallery:gallery-1"

        # Cleanup
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
class TestWebSocketManagerClose:
    """Test WebSocketManager close functionality."""

    async def test_close_clears_connections(self):
        """Test closing manager clears all connections."""
        manager = WebSocketManager()

        for i in range(3):
            await manager.connect(
                websocket=AsyncMock(),
                gallery_id=f"gallery-{i}",
            )

        assert len(manager._connections) == 3

        await manager.close()

        assert len(manager._connections) == 0

    async def test_close_closes_websockets(self):
        """Test closing manager closes all WebSockets."""
        manager = WebSocketManager()
        mock_sockets = []

        for i in range(2):
            mock_ws = AsyncMock()
            mock_sockets.append(mock_ws)
            await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
            )

        await manager.close()

        for mock_ws in mock_sockets:
            mock_ws.close.assert_called_once()

    async def test_close_cancels_pubsub_task(self):
        """Test closing cancels pubsub listener task."""
        manager = WebSocketManager()
        mock_redis = MagicMock()  # Not AsyncMock - pubsub() is sync
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        async def mock_listen():
            while True:
                await asyncio.sleep(0.1)
                yield {"type": "message", "channel": "test", "data": "{}"}

        mock_pubsub.listen.return_value = mock_listen()
        await manager.initialize(redis_client=mock_redis)

        assert manager._pubsub_task is not None

        await manager.close()

        mock_pubsub.close.assert_called_once()


@pytest.mark.asyncio
class TestWebSocketManagerHelpers:
    """Test WebSocketManager helper methods."""

    async def test_get_connection_count_empty(self):
        """Test getting connection count when empty."""
        manager = WebSocketManager()

        assert manager.get_connection_count() == 0
        assert manager.get_connection_count("gallery-1") == 0

    async def test_get_connection_count_total(self):
        """Test getting total connection count."""
        manager = WebSocketManager()

        await manager.connect(AsyncMock(), "gallery-1")
        await manager.connect(AsyncMock(), "gallery-1")
        await manager.connect(AsyncMock(), "gallery-2")

        assert manager.get_connection_count() == 3

    async def test_get_connection_count_by_gallery(self):
        """Test getting connection count for specific gallery."""
        manager = WebSocketManager()

        await manager.connect(AsyncMock(), "gallery-1")
        await manager.connect(AsyncMock(), "gallery-1")
        await manager.connect(AsyncMock(), "gallery-2")

        assert manager.get_connection_count("gallery-1") == 2
        assert manager.get_connection_count("gallery-2") == 1

    async def test_get_gallery_ids(self):
        """Test getting list of gallery IDs."""
        manager = WebSocketManager()

        await manager.connect(AsyncMock(), "gallery-a")
        await manager.connect(AsyncMock(), "gallery-b")
        await manager.connect(AsyncMock(), "gallery-c")

        gallery_ids = manager.get_gallery_ids()

        assert len(gallery_ids) == 3
        assert "gallery-a" in gallery_ids
        assert "gallery-b" in gallery_ids
        assert "gallery-c" in gallery_ids


class TestMessageCreationHelpers:
    """Test message creation helper functions."""

    def test_create_photo_added_message(self):
        """Test creating photo_added message."""
        message = create_photo_added_message(
            asset_id="asset-123",
            thumbnail_url="https://example.com/thumb.jpg",
            position=5,
        )

        assert message["type"] == "photo_added"
        assert "timestamp" in message
        assert message["data"]["asset_id"] == "asset-123"
        assert message["data"]["thumbnail_url"] == "https://example.com/thumb.jpg"
        assert message["data"]["position"] == 5

    def test_create_photo_added_message_without_position(self):
        """Test creating photo_added message without position."""
        message = create_photo_added_message(
            asset_id="asset-123",
            thumbnail_url="https://example.com/thumb.jpg",
        )

        assert message["data"]["position"] is None

    def test_create_photo_removed_message(self):
        """Test creating photo_removed message."""
        message = create_photo_removed_message(asset_id="asset-456")

        assert message["type"] == "photo_removed"
        assert "timestamp" in message
        assert message["data"]["asset_id"] == "asset-456"

    def test_create_gallery_updated_message(self):
        """Test creating gallery_updated message."""
        message = create_gallery_updated_message(
            update_type="title_changed",
            data={"new_title": "My Gallery"},
        )

        assert message["type"] == "gallery_updated"
        assert "timestamp" in message
        assert message["data"]["update_type"] == "title_changed"
        assert message["data"]["new_title"] == "My Gallery"

    def test_message_timestamp_format(self):
        """Test message timestamps are ISO formatted."""
        message = create_photo_added_message("asset", "url")

        # Should be parseable as ISO format
        timestamp = message["timestamp"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)


@pytest.mark.asyncio
class TestWebSocketManagerConcurrency:
    """Test WebSocketManager thread safety."""

    async def test_concurrent_connections(self):
        """Test multiple concurrent connections."""
        manager = WebSocketManager()

        async def connect_task(gallery_id: str, user_num: int):
            mock_ws = AsyncMock()
            await manager.connect(
                websocket=mock_ws,
                gallery_id=gallery_id,
                user_id=f"user-{user_num}",
            )

        # Create 10 concurrent connections
        tasks = [
            connect_task("gallery-1", i) for i in range(10)
        ]
        await asyncio.gather(*tasks)

        assert manager.get_connection_count("gallery-1") == 10

    async def test_concurrent_connect_disconnect(self):
        """Test concurrent connect and disconnect operations."""
        manager = WebSocketManager()

        connections = []
        for i in range(5):
            mock_ws = AsyncMock()
            conn = await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
            )
            connections.append(conn)

        # Concurrently disconnect half and add more
        async def disconnect_task(conn):
            await manager.disconnect(conn)

        async def connect_task():
            mock_ws = AsyncMock()
            await manager.connect(
                websocket=mock_ws,
                gallery_id="gallery-1",
            )

        tasks = [
            disconnect_task(connections[0]),
            disconnect_task(connections[1]),
            connect_task(),
            connect_task(),
            connect_task(),
        ]
        await asyncio.gather(*tasks)

        # 5 - 2 + 3 = 6
        assert manager.get_connection_count("gallery-1") == 6


@pytest.mark.asyncio
class TestWebSocketManagerPubSubListener:
    """Test WebSocketManager Redis Pub/Sub listener."""

    async def test_listen_pubsub_handles_messages(self):
        """Test _listen_pubsub processes Redis messages correctly."""
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        # Create a message generator that yields one message then stops
        messages = [
            {"type": "message", "channel": b"gallery:gallery-1", "data": b'{"type": "test"}'},
        ]

        async def mock_listen():
            for msg in messages:
                yield msg

        mock_pubsub.listen.return_value = mock_listen()

        # Connect a client to receive the message
        mock_ws = AsyncMock()
        await manager.connect(websocket=mock_ws, gallery_id="gallery-1")

        await manager.initialize(redis_client=mock_redis)

        # Wait briefly for pubsub task to process
        await asyncio.sleep(0.1)

        # Cleanup
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass

    async def test_listen_pubsub_handles_string_channel(self):
        """Test _listen_pubsub handles string channel name."""
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        # Message with string channel instead of bytes
        messages = [
            {"type": "message", "channel": "gallery:gallery-2", "data": '{"type": "update"}'},
        ]

        async def mock_listen():
            for msg in messages:
                yield msg

        mock_pubsub.listen.return_value = mock_listen()

        mock_ws = AsyncMock()
        await manager.connect(websocket=mock_ws, gallery_id="gallery-2")

        await manager.initialize(redis_client=mock_redis)
        await asyncio.sleep(0.1)

        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass

    async def test_listen_pubsub_ignores_non_message_types(self):
        """Test _listen_pubsub ignores subscribe/unsubscribe events."""
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        messages = [
            {"type": "subscribe", "channel": "gallery:gallery-1", "data": 1},
            {"type": "psubscribe", "channel": "*", "data": 1},
        ]

        async def mock_listen():
            for msg in messages:
                yield msg

        mock_pubsub.listen.return_value = mock_listen()

        await manager.initialize(redis_client=mock_redis)
        await asyncio.sleep(0.1)

        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except asyncio.CancelledError:
                pass

    async def test_listen_pubsub_handles_error(self):
        """Test _listen_pubsub handles errors gracefully."""
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        async def mock_listen():
            raise Exception("Redis connection lost")
            yield  # Make it a generator

        mock_pubsub.listen.return_value = mock_listen()

        await manager.initialize(redis_client=mock_redis)
        await asyncio.sleep(0.1)

        # Task should have completed (with error) without crashing
        if manager._pubsub_task:
            manager._pubsub_task.cancel()
            try:
                await manager._pubsub_task
            except (asyncio.CancelledError, Exception):
                pass

    async def test_listen_pubsub_returns_early_without_pubsub(self):
        """Test _listen_pubsub returns early if no pubsub configured."""
        manager = WebSocketManager()
        # Don't initialize with redis
        await manager._listen_pubsub()  # Should return immediately


@pytest.mark.asyncio
class TestWebSocketManagerCloseEdgeCases:
    """Test WebSocketManager close edge cases."""

    async def test_close_handles_websocket_close_exception(self):
        """Test close gracefully handles exceptions when closing WebSockets."""
        manager = WebSocketManager()

        # Create mock websocket that throws on close
        mock_ws_error = AsyncMock()
        mock_ws_error.close.side_effect = Exception("Connection already closed")

        mock_ws_good = AsyncMock()

        await manager.connect(websocket=mock_ws_error, gallery_id="gallery-1")
        await manager.connect(websocket=mock_ws_good, gallery_id="gallery-1")

        # Should not raise even though one close fails
        await manager.close()

        # Connections should still be cleared
        assert len(manager._connections) == 0

    async def test_close_handles_all_websockets_failing(self):
        """Test close completes even if all WebSocket closes fail."""
        manager = WebSocketManager()

        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.close.side_effect = Exception("Failed to close")
            await manager.connect(websocket=mock_ws, gallery_id=f"gallery-{i}")

        # Should complete without raising
        await manager.close()
        assert len(manager._connections) == 0
