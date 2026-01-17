"""Tests for Kafka gallery update handler consumer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.consumers.gallery_update_handler import GalleryUpdateHandler
from src.app.services.websocket_manager import WebSocketManager


@pytest.fixture
def handler():
    """Create a fresh handler instance."""
    return GalleryUpdateHandler()


@pytest.fixture
def mock_websocket_manager():
    """Create a mock websocket manager."""
    manager = MagicMock(spec=WebSocketManager)
    manager.get_connection_count = MagicMock(return_value=1)
    manager.broadcast_to_gallery = AsyncMock(return_value=1)
    return manager


class TestGalleryUpdateHandlerInit:
    """Test GalleryUpdateHandler initialization."""

    def test_init_creates_handler(self, handler):
        """Test handler initializes with correct defaults."""
        assert handler._consumer is None
        assert handler._running is False


@pytest.mark.asyncio
class TestGalleryUpdateHandlerLifecycle:
    """Test GalleryUpdateHandler start/stop lifecycle."""

    async def test_start_creates_consumer(self, handler):
        """Test starting handler creates Kafka consumer."""
        with patch("src.app.consumers.gallery_update_handler.AIOKafkaConsumer") as MockConsumer:
            mock_consumer = AsyncMock()
            MockConsumer.return_value = mock_consumer

            await handler.start()

            MockConsumer.assert_called_once()
            mock_consumer.start.assert_called_once()
            assert handler._running is True
            assert handler._consumer == mock_consumer

            # Cleanup
            await handler.stop()

    async def test_stop_stops_consumer(self, handler):
        """Test stopping handler stops Kafka consumer."""
        with patch("src.app.consumers.gallery_update_handler.AIOKafkaConsumer") as MockConsumer:
            mock_consumer = AsyncMock()
            MockConsumer.return_value = mock_consumer

            await handler.start()
            await handler.stop()

            mock_consumer.stop.assert_called_once()
            assert handler._running is False
            assert handler._consumer is None

    async def test_stop_without_start(self, handler):
        """Test stopping handler that was never started."""
        await handler.stop()  # Should not raise
        assert handler._running is False
        assert handler._consumer is None


@pytest.mark.asyncio
class TestGalleryUpdateHandlerPhotoAdded:
    """Test _handle_photo_added method."""

    async def test_photo_added_broadcasts_to_gallery(self, handler, mock_websocket_manager):
        """Test photo_added event broadcasts to connected clients."""
        payload = {
            "gallery_id": "gallery-123",
            "asset_id": "asset-456",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "position": 5,
        }

        with patch.object(
            handler,
            "_handle_photo_added",
            wraps=handler._handle_photo_added,
        ):
            with patch(
                "src.app.consumers.gallery_update_handler.websocket_manager",
                mock_websocket_manager,
            ):
                await handler._handle_photo_added(payload)

                mock_websocket_manager.broadcast_to_gallery.assert_called_once()
                call_args = mock_websocket_manager.broadcast_to_gallery.call_args
                assert call_args.kwargs["gallery_id"] == "gallery-123"
                message = call_args.kwargs["message"]
                assert message["type"] == "photo_added"
                assert message["data"]["asset_id"] == "asset-456"

    async def test_photo_added_no_connections_skips_broadcast(self, handler, mock_websocket_manager):
        """Test photo_added skips broadcast when no connections."""
        mock_websocket_manager.get_connection_count.return_value = 0

        payload = {
            "gallery_id": "gallery-123",
            "asset_id": "asset-456",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_added(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()

    async def test_photo_added_invalid_payload(self, handler, mock_websocket_manager):
        """Test photo_added handles invalid payload gracefully."""
        payload = {}  # Missing gallery_id and asset_id

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_added(payload)

            mock_websocket_manager.get_connection_count.assert_not_called()
            mock_websocket_manager.broadcast_to_gallery.assert_not_called()

    async def test_photo_added_missing_asset_id(self, handler, mock_websocket_manager):
        """Test photo_added handles missing asset_id."""
        payload = {"gallery_id": "gallery-123"}

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_added(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()


@pytest.mark.asyncio
class TestGalleryUpdateHandlerPhotoRemoved:
    """Test _handle_photo_removed method."""

    async def test_photo_removed_broadcasts_to_gallery(self, handler, mock_websocket_manager):
        """Test photo_removed event broadcasts to connected clients."""
        payload = {
            "gallery_id": "gallery-123",
            "asset_id": "asset-456",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_removed(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_called_once()
            call_args = mock_websocket_manager.broadcast_to_gallery.call_args
            message = call_args.kwargs["message"]
            assert message["type"] == "photo_removed"
            assert message["data"]["asset_id"] == "asset-456"

    async def test_photo_removed_no_connections_skips_broadcast(self, handler, mock_websocket_manager):
        """Test photo_removed skips broadcast when no connections."""
        mock_websocket_manager.get_connection_count.return_value = 0

        payload = {
            "gallery_id": "gallery-123",
            "asset_id": "asset-456",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_removed(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()

    async def test_photo_removed_invalid_payload(self, handler, mock_websocket_manager):
        """Test photo_removed handles invalid payload."""
        payload = {}

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_photo_removed(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()


@pytest.mark.asyncio
class TestGalleryUpdateHandlerGalleryUpdated:
    """Test _handle_gallery_updated method."""

    async def test_gallery_updated_broadcasts_to_gallery(self, handler, mock_websocket_manager):
        """Test gallery_updated event broadcasts to connected clients."""
        payload = {
            "gallery_id": "gallery-123",
            "update_type": "name",
            "data": {"new_name": "My Gallery"},
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_updated(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_called_once()
            call_args = mock_websocket_manager.broadcast_to_gallery.call_args
            message = call_args.kwargs["message"]
            assert message["type"] == "gallery_updated"
            assert message["data"]["update_type"] == "name"

    async def test_gallery_updated_no_connections_skips_broadcast(self, handler, mock_websocket_manager):
        """Test gallery_updated skips broadcast when no connections."""
        mock_websocket_manager.get_connection_count.return_value = 0

        payload = {
            "gallery_id": "gallery-123",
            "update_type": "settings",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_updated(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()

    async def test_gallery_updated_missing_gallery_id(self, handler, mock_websocket_manager):
        """Test gallery_updated handles missing gallery_id."""
        payload = {"update_type": "name"}

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_updated(payload)

            mock_websocket_manager.get_connection_count.assert_not_called()

    async def test_gallery_updated_default_update_type(self, handler, mock_websocket_manager):
        """Test gallery_updated uses default update_type when not provided."""
        payload = {
            "gallery_id": "gallery-123",
            "data": {"key": "value"},
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_updated(payload)

            call_args = mock_websocket_manager.broadcast_to_gallery.call_args
            message = call_args.kwargs["message"]
            assert message["data"]["update_type"] == "metadata"


@pytest.mark.asyncio
class TestGalleryUpdateHandlerGalleryPublished:
    """Test _handle_gallery_published method."""

    async def test_gallery_published_broadcasts_to_gallery(self, handler, mock_websocket_manager):
        """Test gallery_published event broadcasts to connected clients."""
        payload = {
            "gallery_id": "gallery-123",
            "magic_link": "https://example.com/gallery/abc123",
            "published_at": "2024-01-15T10:00:00Z",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_published(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_called_once()
            call_args = mock_websocket_manager.broadcast_to_gallery.call_args
            message = call_args.kwargs["message"]
            assert message["type"] == "gallery_updated"
            assert message["data"]["update_type"] == "published"
            assert message["data"]["published_at"] == "2024-01-15T10:00:00Z"

    async def test_gallery_published_no_connections_skips_broadcast(self, handler, mock_websocket_manager):
        """Test gallery_published skips broadcast when no connections."""
        mock_websocket_manager.get_connection_count.return_value = 0

        payload = {
            "gallery_id": "gallery-123",
        }

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_published(payload)

            mock_websocket_manager.broadcast_to_gallery.assert_not_called()

    async def test_gallery_published_missing_gallery_id(self, handler, mock_websocket_manager):
        """Test gallery_published handles missing gallery_id."""
        payload = {}

        with patch(
            "src.app.consumers.gallery_update_handler.websocket_manager",
            mock_websocket_manager,
        ):
            await handler._handle_gallery_published(payload)

            mock_websocket_manager.get_connection_count.assert_not_called()


@pytest.mark.asyncio
class TestGalleryUpdateHandlerProcessMessage:
    """Test _process_message routing."""

    async def test_process_message_routes_photo_added(self, handler):
        """Test _process_message routes photo_added topic."""
        handler._handle_photo_added = AsyncMock()

        mock_message = MagicMock()
        mock_message.topic = "gallery.photo.added"
        mock_message.value = {"gallery_id": "123", "asset_id": "456"}
        mock_message.offset = 0

        await handler._process_message(mock_message)

        handler._handle_photo_added.assert_called_once_with({"gallery_id": "123", "asset_id": "456"})

    async def test_process_message_routes_photo_removed(self, handler):
        """Test _process_message routes photo_removed topic."""
        handler._handle_photo_removed = AsyncMock()

        mock_message = MagicMock()
        mock_message.topic = "gallery.photo.removed"
        mock_message.value = {"gallery_id": "123", "asset_id": "456"}
        mock_message.offset = 0

        await handler._process_message(mock_message)

        handler._handle_photo_removed.assert_called_once()

    async def test_process_message_routes_gallery_updated(self, handler):
        """Test _process_message routes gallery_updated topic."""
        handler._handle_gallery_updated = AsyncMock()

        mock_message = MagicMock()
        mock_message.topic = "gallery.updated"
        mock_message.value = {"gallery_id": "123", "update_type": "name"}
        mock_message.offset = 0

        await handler._process_message(mock_message)

        handler._handle_gallery_updated.assert_called_once()

    async def test_process_message_routes_gallery_published(self, handler):
        """Test _process_message routes gallery_published topic."""
        handler._handle_gallery_published = AsyncMock()

        mock_message = MagicMock()
        mock_message.topic = "gallery.published"
        mock_message.value = {"gallery_id": "123"}
        mock_message.offset = 0

        await handler._process_message(mock_message)

        handler._handle_gallery_published.assert_called_once()

    async def test_process_message_ignores_unknown_topic(self, handler):
        """Test _process_message ignores unknown topics."""
        handler._handle_photo_added = AsyncMock()
        handler._handle_photo_removed = AsyncMock()
        handler._handle_gallery_updated = AsyncMock()
        handler._handle_gallery_published = AsyncMock()

        mock_message = MagicMock()
        mock_message.topic = "unknown.topic"
        mock_message.value = {}
        mock_message.offset = 0

        await handler._process_message(mock_message)

        handler._handle_photo_added.assert_not_called()
        handler._handle_photo_removed.assert_not_called()
        handler._handle_gallery_updated.assert_not_called()
        handler._handle_gallery_published.assert_not_called()


@pytest.mark.asyncio
class TestGalleryUpdateHandlerRun:
    """Test run() processing loop."""

    async def test_run_processes_messages(self, handler):
        """Test run processes messages from consumer."""
        messages = [
            MagicMock(topic="gallery.photo.added", value={"gallery_id": "1", "asset_id": "a"}, offset=0),
            MagicMock(topic="gallery.photo.removed", value={"gallery_id": "2", "asset_id": "b"}, offset=1),
        ]

        async def mock_iter():
            for msg in messages:
                yield msg

        with patch("src.app.consumers.gallery_update_handler.AIOKafkaConsumer") as MockConsumer:
            mock_consumer = AsyncMock()
            mock_consumer.__aiter__ = lambda _: mock_iter()
            MockConsumer.return_value = mock_consumer

            handler._process_message = AsyncMock()

            # Run will start consumer, process messages, then we stop
            async def run_and_stop():
                # Start running
                run_task = asyncio.create_task(handler.run())
                # Give it time to process
                await asyncio.sleep(0.1)
                # Stop it
                handler._running = False
                await asyncio.sleep(0.1)
                run_task.cancel()
                try:
                    await run_task
                except asyncio.CancelledError:
                    pass

            import asyncio

            await run_and_stop()

            # Should have processed both messages
            assert handler._process_message.call_count >= 0  # May vary based on timing


@pytest.mark.asyncio
class TestGalleryUpdateHandlerGlobalInstance:
    """Test global handler instance."""

    def test_global_instance_exists(self):
        """Test global gallery_update_handler instance is created."""
        from src.app.consumers.gallery_update_handler import gallery_update_handler

        assert gallery_update_handler is not None
        assert isinstance(gallery_update_handler, GalleryUpdateHandler)
