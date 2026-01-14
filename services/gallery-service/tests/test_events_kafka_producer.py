"""Tests for Kafka producer and event publishing."""

import pytest


@pytest.mark.asyncio
class TestKafkaProducer:
    """Test Kafka producer lifecycle."""

    async def test_get_kafka_producer_handles_init_failure(self, mocker):
        """Test get_kafka_producer returns None when init fails."""
        from src.app.events.kafka_producer import get_kafka_producer, close_kafka_producer

        # Ensure producer is None to trigger init
        await close_kafka_producer()

        # Mock init to raise exception
        mocker.patch(
            "src.app.events.kafka_producer.init_kafka_producer",
            side_effect=Exception("Kafka connection failed")
        )

        producer = await get_kafka_producer()
        assert producer is None

    async def test_close_kafka_producer_with_active_producer(self, mocker):
        """Test closing Kafka producer when it exists."""
        from src.app.events.kafka_producer import close_kafka_producer
        import src.app.events.kafka_producer as kafka_module

        # Create mock producer and set directly in global
        mock_producer = mocker.AsyncMock()
        kafka_module._kafka_producer = mock_producer

        # Close producer
        await close_kafka_producer()

        # Verify stop was called
        mock_producer.stop.assert_called_once()

    async def test_close_kafka_producer_when_none(self):
        """Test closing Kafka producer when it's already None."""
        from src.app.events.kafka_producer import close_kafka_producer

        # Ensure producer is None
        await close_kafka_producer()

        # Should not raise error
        await close_kafka_producer()


@pytest.mark.asyncio
class TestSendEvent:
    """Test event publishing to Kafka."""

    async def test_send_event_success(self, mocker):
        """Test successfully sending event to Kafka."""
        from src.app.events.kafka_producer import (
            send_event,
            GalleryPublishedEvent,
            get_kafka_producer,
            close_kafka_producer,
        )

        # Ensure clean state
        await close_kafka_producer()

        # Create mock producer
        mock_producer = mocker.AsyncMock()
        mocker.patch(
            "src.app.events.kafka_producer.get_kafka_producer",
            return_value=mock_producer
        )

        # Create test event
        event = GalleryPublishedEvent(
            gallery_id="gallery-123",
            workspace_id="workspace-456",
            title="Test Gallery"
        )

        # Send event
        await send_event(
            topic="gallery.events",
            event=event,
            key="gallery-123"
        )

        # Verify send_and_wait was called
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        assert call_args.kwargs["topic"] == "gallery.events"
        assert call_args.kwargs["key"] == b"gallery-123"

    async def test_send_event_producer_unavailable(self, mocker):
        """Test send_event when Kafka producer is unavailable."""
        from src.app.events.kafka_producer import (
            send_event,
            GalleryPublishedEvent,
            close_kafka_producer,
        )

        # Ensure producer is None
        await close_kafka_producer()

        # Mock get_kafka_producer to return None
        mocker.patch(
            "src.app.events.kafka_producer.get_kafka_producer",
            return_value=None
        )

        # Create test event
        event = GalleryPublishedEvent(
            gallery_id="gallery-123",
            workspace_id="workspace-456",
            title="Test Gallery"
        )

        # Send event (should log warning but not raise)
        await send_event(
            topic="gallery.events",
            event=event,
            key="gallery-123"
        )

        # Should complete without error

    async def test_send_event_publish_failure(self, mocker):
        """Test send_event when Kafka publish fails."""
        from src.app.events.kafka_producer import (
            send_event,
            GalleryArchivedEvent,
            close_kafka_producer,
        )

        # Ensure clean state
        await close_kafka_producer()

        # Create mock producer that raises exception
        mock_producer = mocker.AsyncMock()
        mock_producer.send_and_wait.side_effect = Exception("Kafka send failed")
        mocker.patch(
            "src.app.events.kafka_producer.get_kafka_producer",
            return_value=mock_producer
        )

        # Create test event
        event = GalleryArchivedEvent(
            gallery_id="gallery-789",
            workspace_id="workspace-456"
        )

        # Send event (should log error but not raise)
        await send_event(
            topic="gallery.events",
            event=event,
            key="gallery-789"
        )

        # Should complete without error

    async def test_send_visitor_registered_event(self, mocker):
        """Test sending VisitorRegisteredEvent."""
        from src.app.events.kafka_producer import (
            send_event,
            VisitorRegisteredEvent,
            close_kafka_producer,
        )

        # Ensure clean state
        await close_kafka_producer()

        # Create mock producer
        mock_producer = mocker.AsyncMock()
        mocker.patch(
            "src.app.events.kafka_producer.get_kafka_producer",
            return_value=mock_producer
        )

        # Create visitor event
        event = VisitorRegisteredEvent(
            visitor_id="visitor-123",
            workspace_id="workspace-456",
            email="visitor@example.com",
            gallery_id="gallery-789"
        )

        # Send event
        await send_event(
            topic="visitor.events",
            event=event,
            key="visitor-123"
        )

        # Verify event was sent
        mock_producer.send_and_wait.assert_called_once()
