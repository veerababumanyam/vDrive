"""Unit tests for AssetProcessor consumer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAssetProcessorInit:
    """Tests for AssetProcessor initialization."""

    def test_init_creates_consumer(self):
        """Should create consumer with correct settings."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor

            processor = AssetProcessor()
            assert processor is not None

    def test_init_sets_topics(self):
        """Should set correct topics."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__") as mock_init:
            mock_init.return_value = None

            from app.consumers.asset_processor import AssetProcessor
            AssetProcessor()

            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert "upload.completed" in call_kwargs["topics"]

    def test_init_sets_consumer_group(self):
        """Should set correct consumer group."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__") as mock_init:
            mock_init.return_value = None

            from app.consumers.asset_processor import AssetProcessor
            AssetProcessor()

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["consumer_group"] == "asset-processor"

    def test_init_sets_max_retries(self):
        """Should set max retries to 3."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__") as mock_init:
            mock_init.return_value = None

            from app.consumers.asset_processor import AssetProcessor
            AssetProcessor()

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["max_retries"] == 3

    def test_init_disables_auto_commit(self):
        """Should disable auto commit."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__") as mock_init:
            mock_init.return_value = None

            from app.consumers.asset_processor import AssetProcessor
            AssetProcessor()

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["auto_commit"] is False


class TestProcessEvent:
    """Tests for process_event method."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_process_event_validates_event(self, processor):
        """Should call validation on event."""
        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
        }

        with patch("app.consumers.asset_processor.validate_kafka_message") as mock_validate:
            from app.core.validation import ValidationError
            mock_validate.side_effect = ValidationError("test", "error")

            with pytest.raises(ValueError):
                await processor.process_event(event)

            mock_validate.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_process_event_rejects_wrong_event_type(self, processor):
        """Should reject wrong event type."""
        event = {
            "event_type": "wrong.type",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_id": "test-upload",
            "workspace_id": "test-workspace",
            "asset_id": "test-asset",
            "storage_path": "test/path",
            "filename": "test.jpg",
            "mime_type": "image/jpeg",
            "file_size": 1024,
        }

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session") as mock_db:
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session.refresh = AsyncMock()
                mock_db.return_value = mock_session

                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task:
                    mock_task_instance = MagicMock()
                    mock_task_instance.id = "task-123"
                    mock_task.return_value = mock_task_instance

                    with pytest.raises(ValueError, match="Unexpected event type"):
                        await processor.process_event(event)

    @pytest.mark.asyncio
    async def test_process_event_missing_required_fields(self, processor):
        """Should reject event with missing fields."""
        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            # Missing required fields like upload_id, workspace_id, etc.
        }

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session") as mock_db:
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session.refresh = AsyncMock()
                mock_db.return_value = mock_session

                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task:
                    mock_task_instance = MagicMock()
                    mock_task_instance.id = "task-123"
                    mock_task.return_value = mock_task_instance

                    with pytest.raises(ValueError, match="Missing required fields"):
                        await processor.process_event(event)


class TestProcessImageIntegration:
    """Integration-style tests for _process_image."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_process_image_calls_workflow(self, processor):
        """Should call all processing steps."""
        # Mock all helper methods
        processor._download_and_decrypt = AsyncMock(return_value=b"fake image data")
        processor._generate_thumbnails_full = AsyncMock(return_value={"thumbnail_key": "thumb.webp"})
        processor._extract_exif_full = AsyncMock()
        processor._detect_faces_full = AsyncMock()
        processor._update_asset_derivatives = AsyncMock()

        result = await processor._process_image(
            asset_id="asset-1",
            workspace_id="ws-1",
            storage_path="path/to/image",
            mime_type="image/jpeg",
            is_encrypted=True,
            encryption_key_id="key-1",
        )

        processor._download_and_decrypt.assert_called_once()
        processor._generate_thumbnails_full.assert_called_once()
        processor._extract_exif_full.assert_called_once()
        processor._detect_faces_full.assert_called_once()
        processor._update_asset_derivatives.assert_called_once()
        assert result["thumbnails_generated"] is True

    @pytest.mark.asyncio
    async def test_process_image_returns_results(self, processor):
        """Should return processing results."""
        processor._download_and_decrypt = AsyncMock(return_value=b"fake image data")
        processor._generate_thumbnails_full = AsyncMock(return_value={
            "thumbnail_key": "thumb.webp",
            "preview_key": "preview.webp",
            "lqip_base64": "base64data",
        })
        processor._extract_exif_full = AsyncMock()
        processor._detect_faces_full = AsyncMock()
        processor._update_asset_derivatives = AsyncMock()

        result = await processor._process_image(
            asset_id="asset-1",
            workspace_id="ws-1",
            storage_path="path",
            mime_type="image/jpeg",
            is_encrypted=True,
            encryption_key_id="key-1",
        )

        assert result["thumbnails_generated"] is True
        assert result["thumbnail_key"] == "thumb.webp"
        assert result["preview_key"] == "preview.webp"
        assert result["exif_extracted"] is True
        assert result["faces_detected"] is True

    @pytest.mark.asyncio
    async def test_process_image_raises_on_error(self, processor):
        """Should raise on processing error."""
        processor._download_and_decrypt = AsyncMock(side_effect=Exception("Download failed"))

        with pytest.raises(Exception, match="Download failed"):
            await processor._process_image(
                asset_id="asset-1",
                workspace_id="ws-1",
                storage_path="path",
                mime_type="image/jpeg",
                is_encrypted=True,
                encryption_key_id="key-1",
            )


class TestProcessVideoIntegration:
    """Integration-style tests for _process_video."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_process_video_skips_when_unavailable(self, processor):
        """Should return None when ffmpeg unavailable."""
        processor._download_and_decrypt = AsyncMock(return_value=b"fake video data")

        mock_video_service = MagicMock()
        mock_video_service.available = False

        with patch("app.services.video_service.get_video_service", return_value=mock_video_service):
            result = await processor._process_video(
                asset_id="asset-1",
                workspace_id="ws-1",
                storage_path="path/to/video",
                mime_type="video/mp4",
                is_encrypted=False,
                encryption_key_id=None,
            )

            # The function logs and returns None when ffmpeg unavailable
            assert result is None


class TestPublishEvents:
    """Tests for event publishing methods."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_publish_processing_event_handles_failure(self, processor):
        """Should handle publish failure gracefully."""
        from datetime import datetime, timezone

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock(side_effect=Exception("Publish failed"))

        with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
            # Should not raise
            await processor._publish_asset_processing_event(
                asset_id="asset-1",
                workspace_id="ws-1",
                event_id="event-1",
                started_at=datetime.now(timezone.utc),
            )

    @pytest.mark.asyncio
    async def test_publish_processed_event_handles_failure(self, processor):
        """Should handle publish failure gracefully."""
        from datetime import datetime, timezone

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock(side_effect=Exception("Publish failed"))

        now = datetime.now(timezone.utc)

        with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
            # Should not raise
            await processor._publish_asset_processed_event(
                asset_id="asset-1",
                workspace_id="ws-1",
                event_id="event-1",
                processing_results={},
                started_at=now,
                completed_at=now,
                processing_duration_ms=100,
            )


class TestDatabaseOperations:
    """Tests for database operations."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_create_processing_task(self, processor):
        """Should create task in database."""
        from app.models import TaskType
        from contextlib import asynccontextmanager

        mock_task = MagicMock()
        mock_task.id = "task-123"

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            with patch("app.consumers.asset_processor.ProcessingTask") as mock_task_class:
                mock_task_class.return_value = mock_task

                result = await processor._create_processing_task(
                    asset_id="asset-1",
                    workspace_id="ws-1",
                    task_type=TaskType.THUMBNAIL_GENERATION,
                    input_data={"filename": "test.jpg"},
                )

                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status(self, processor):
        """Should update task status in database."""
        from app.models import TaskStatus
        from datetime import datetime, timezone
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            await processor._update_task_status(
                task_id="task-123",
                status=TaskStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )

            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_asset_derivatives(self, processor):
        """Should update asset derivatives in database."""
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            await processor._update_asset_derivatives(
                asset_id="asset-1",
                derivative_keys={
                    "thumbnail_key": "thumb.webp",
                    "preview_key": "preview.webp",
                },
            )

            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_asset_derivatives_raises_on_error(self, processor):
        """Should raise on database error."""
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            with pytest.raises(Exception, match="Database error"):
                await processor._update_asset_derivatives(
                    asset_id="asset-1",
                    derivative_keys={"thumbnail_key": "thumb.webp"},
                )


class TestExifExtraction:
    """Tests for EXIF extraction."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_extract_exif_handles_error(self, processor):
        """Should handle EXIF extraction errors gracefully."""
        mock_exif_service = MagicMock()
        mock_exif_service.extract_exif.side_effect = Exception("EXIF error")

        with patch("app.services.exif_service.get_exif_service", return_value=mock_exif_service):
            # Should not raise - EXIF extraction is non-critical
            await processor._extract_exif_full(
                asset_id="asset-1",
                image_data=b"fake",
                mime_type="image/jpeg",
            )


class TestFaceDetection:
    """Tests for face detection."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_detect_faces_skips_when_disabled(self, processor):
        """Should skip face detection when disabled."""
        mock_face_service = MagicMock()
        mock_face_service.enabled = False

        with patch("app.services.face_service.get_face_service", return_value=mock_face_service):
            await processor._detect_faces_full(
                asset_id="asset-1",
                workspace_id="ws-1",
                image_data=b"fake",
            )

            mock_face_service.detect_faces.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_faces_handles_error(self, processor):
        """Should handle face detection errors gracefully."""
        mock_face_service = MagicMock()
        mock_face_service.enabled = True
        mock_face_service.detect_faces = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.face_service.get_face_service", return_value=mock_face_service):
            # Should not raise - face detection is optional
            await processor._detect_faces_full(
                asset_id="asset-1",
                workspace_id="ws-1",
                image_data=b"fake",
            )

    @pytest.mark.asyncio
    async def test_detect_faces_handles_no_faces(self, processor):
        """Should handle no faces gracefully."""
        mock_face_service = MagicMock()
        mock_face_service.enabled = True
        mock_face_service.detect_faces = AsyncMock(return_value=[])

        with patch("app.services.face_service.get_face_service", return_value=mock_face_service):
            # Should not raise
            await processor._detect_faces_full(
                asset_id="asset-1",
                workspace_id="ws-1",
                image_data=b"fake",
            )


class TestProcessEventFullFlow:
    """Tests for complete process_event flow."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_process_event_image_full_flow(self, processor):
        """Should process image event through full workflow."""
        from contextlib import asynccontextmanager
        from datetime import datetime, timezone

        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_id": "upload-123",
            "workspace_id": "ws-123",
            "asset_id": "asset-123",
            "storage_path": "path/to/file.jpg",
            "filename": "test.jpg",
            "mime_type": "image/jpeg",
            "file_size": 1024,
            "is_encrypted": True,
            "encryption_key_id": "key-1",
        }

        mock_task = MagicMock()
        mock_task.id = "task-123"

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task_class:
                    mock_task_class.return_value = mock_task

                    processor._process_image = AsyncMock(return_value={
                        "thumbnails_generated": True,
                        "thumbnail_key": "thumb.webp",
                        "preview_key": "preview.webp",
                    })
                    processor._publish_asset_processing_event = AsyncMock()
                    processor._publish_asset_processed_event = AsyncMock()
                    processor._update_task_status = AsyncMock()

                    with patch("app.consumers.asset_processor.tasks_processed_total") as mock_metric:
                        mock_labels = MagicMock()
                        mock_metric.labels.return_value = mock_labels

                        await processor.process_event(event)

                        processor._process_image.assert_called_once()
                        processor._publish_asset_processing_event.assert_called_once()
                        processor._publish_asset_processed_event.assert_called_once()
                        mock_labels.inc.assert_called()

    @pytest.mark.asyncio
    async def test_process_event_video_full_flow(self, processor):
        """Should process video event through full workflow."""
        from contextlib import asynccontextmanager

        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_id": "upload-123",
            "workspace_id": "ws-123",
            "asset_id": "asset-123",
            "storage_path": "path/to/file.mp4",
            "filename": "test.mp4",
            "mime_type": "video/mp4",
            "file_size": 10240,
            "is_encrypted": False,
        }

        mock_task = MagicMock()
        mock_task.id = "task-123"

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task_class:
                    mock_task_class.return_value = mock_task

                    processor._process_video = AsyncMock(return_value={
                        "thumbnails_generated": True,
                        "video_duration": 30.0,
                    })
                    processor._publish_asset_processing_event = AsyncMock()
                    processor._publish_asset_processed_event = AsyncMock()
                    processor._update_task_status = AsyncMock()

                    with patch("app.consumers.asset_processor.tasks_processed_total") as mock_metric:
                        mock_labels = MagicMock()
                        mock_metric.labels.return_value = mock_labels

                        await processor.process_event(event)

                        processor._process_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_event_unsupported_mime_type(self, processor):
        """Should handle unsupported MIME types."""
        from contextlib import asynccontextmanager

        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_id": "upload-123",
            "workspace_id": "ws-123",
            "asset_id": "asset-123",
            "storage_path": "path/to/file.pdf",
            "filename": "test.pdf",
            "mime_type": "application/pdf",
            "file_size": 1024,
        }

        mock_task = MagicMock()
        mock_task.id = "task-123"

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task_class:
                    mock_task_class.return_value = mock_task

                    processor._publish_asset_processing_event = AsyncMock()
                    processor._publish_asset_processed_event = AsyncMock()
                    processor._update_task_status = AsyncMock()

                    with patch("app.consumers.asset_processor.tasks_processed_total") as mock_metric:
                        mock_labels = MagicMock()
                        mock_metric.labels.return_value = mock_labels

                        await processor.process_event(event)

    @pytest.mark.asyncio
    async def test_process_event_marks_task_failed_on_error(self, processor):
        """Should mark task as failed when processing fails."""
        from contextlib import asynccontextmanager

        event = {
            "event_type": "upload.completed",
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_id": "upload-123",
            "workspace_id": "ws-123",
            "asset_id": "asset-123",
            "storage_path": "path/to/file.jpg",
            "filename": "test.jpg",
            "mime_type": "image/jpeg",
            "file_size": 1024,
        }

        mock_task = MagicMock()
        mock_task.id = "task-123"

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.validate_kafka_message", return_value=event):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.ProcessingTask") as mock_task_class:
                    mock_task_class.return_value = mock_task

                    processor._process_image = AsyncMock(side_effect=Exception("Processing failed"))
                    processor._publish_asset_processing_event = AsyncMock()
                    processor._update_task_status = AsyncMock()

                    with patch("app.consumers.asset_processor.tasks_processed_total") as mock_metric:
                        mock_labels = MagicMock()
                        mock_metric.labels.return_value = mock_labels

                        with pytest.raises(Exception, match="Processing failed"):
                            await processor.process_event(event)

                        # Verify task was marked as failed
                        processor._update_task_status.assert_called()


class TestDownloadAndDecrypt:
    """Tests for _download_and_decrypt method."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_download_without_encryption(self, processor):
        """Should download without decryption when not encrypted."""
        mock_storage_service = MagicMock()
        mock_storage_service.download_object.return_value = b"raw data"

        with patch("app.services.storage_service.get_storage_service", return_value=mock_storage_service):
            result = await processor._download_and_decrypt(
                storage_path="path/to/file",
                workspace_id="ws-1",
                is_encrypted=False,
            )

            assert result == b"raw data"
            mock_storage_service.download_object.assert_called_once_with("path/to/file")

    @pytest.mark.asyncio
    async def test_download_with_encryption(self, processor):
        """Should decrypt when encrypted."""
        mock_storage_service = MagicMock()
        mock_storage_service.download_object.return_value = b"encrypted data"

        mock_encryption_service = MagicMock()
        mock_encryption_service.decrypt_asset.return_value = b"decrypted data"

        with patch("app.services.storage_service.get_storage_service", return_value=mock_storage_service):
            with patch("app.services.encryption_service.get_encryption_service", return_value=mock_encryption_service):
                result = await processor._download_and_decrypt(
                    storage_path="path/to/file",
                    workspace_id="ws-1",
                    is_encrypted=True,
                )

                assert result == b"decrypted data"
                mock_encryption_service.decrypt_asset.assert_called_once()


class TestGenerateThumbnailsFull:
    """Tests for _generate_thumbnails_full method."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_generates_and_uploads_thumbnails(self, processor):
        """Should generate thumbnails and upload to storage."""
        mock_thumbnail_service = MagicMock()
        mock_thumbnail_service.generate_thumbnails.return_value = {
            "thumbnail": b"thumb data",
            "preview": b"preview data",
            "lqip": b"lqip data",
        }
        mock_thumbnail_service.generate_lqip_base64.return_value = "data:image/webp;base64,abc123"

        mock_storage_service = MagicMock()
        mock_storage_service.upload_object.return_value = True

        with patch("app.services.thumbnail_service.get_thumbnail_service", return_value=mock_thumbnail_service):
            with patch("app.services.storage_service.get_storage_service", return_value=mock_storage_service):
                result = await processor._generate_thumbnails_full(
                    asset_id="asset-1",
                    workspace_id="ws-1",
                    image_data=b"original image",
                    mime_type="image/jpeg",
                )

                assert "thumbnail_key" in result
                assert "preview_key" in result
                assert "lqip_base64" in result
                mock_thumbnail_service.generate_thumbnails.assert_called_once()


class TestProcessVideoFull:
    """Tests for complete _process_video flow."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_process_video_full_success(self, processor):
        """Should process video through full workflow."""
        processor._download_and_decrypt = AsyncMock(return_value=b"video data")
        processor._update_asset_derivatives = AsyncMock()

        mock_video_service = MagicMock()
        mock_video_service.available = True
        mock_video_service.extract_first_frame.return_value = b"frame jpeg"
        mock_video_service.get_video_metadata.return_value = {
            "duration": 30.0,
            "width": 1920,
            "height": 1080,
            "codec": "h264",
        }

        mock_thumbnail_service = MagicMock()
        mock_thumbnail_service.generate_thumbnails.return_value = {
            "thumbnail": b"thumb",
            "preview": b"preview",
        }
        mock_thumbnail_service.generate_lqip_base64.return_value = "data:image/webp;base64,xyz"

        mock_storage_service = MagicMock()

        with patch("app.services.video_service.get_video_service", return_value=mock_video_service):
            with patch("app.services.thumbnail_service.get_thumbnail_service", return_value=mock_thumbnail_service):
                with patch("app.services.storage_service.get_storage_service", return_value=mock_storage_service):
                    result = await processor._process_video(
                        asset_id="asset-1",
                        workspace_id="ws-1",
                        storage_path="path/to/video.mp4",
                        mime_type="video/mp4",
                        is_encrypted=False,
                        encryption_key_id=None,
                    )

                    assert result["thumbnails_generated"] is True
                    assert result["video_duration"] == 30.0
                    assert result["video_width"] == 1920
                    assert result["video_height"] == 1080

    @pytest.mark.asyncio
    async def test_process_video_raises_on_error(self, processor):
        """Should raise on video processing error."""
        processor._download_and_decrypt = AsyncMock(side_effect=Exception("Video download failed"))

        mock_video_service = MagicMock()
        mock_video_service.available = True

        with patch("app.services.video_service.get_video_service", return_value=mock_video_service):
            with pytest.raises(Exception, match="Video download failed"):
                await processor._process_video(
                    asset_id="asset-1",
                    workspace_id="ws-1",
                    storage_path="path/to/video.mp4",
                    mime_type="video/mp4",
                    is_encrypted=False,
                    encryption_key_id=None,
                )


class TestExtractExifFull:
    """Tests for _extract_exif_full method."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_calls_exif_service(self, processor):
        """Should call exif service with image data."""
        mock_exif_service = MagicMock()
        mock_exif_service.extract_exif.return_value = {
            "camera_make": "Canon",
            "camera_model": "EOS R5",
            "iso": 100,
        }

        # Mock db session to raise an error after exif service is called,
        # this way we verify the service call happens
        with patch("app.services.exif_service.get_exif_service", return_value=mock_exif_service):
            with patch("app.consumers.asset_processor.get_db_session") as mock_db:
                mock_db.side_effect = Exception("DB mocked out")

                try:
                    await processor._extract_exif_full(
                        asset_id="asset-1",
                        image_data=b"image data",
                        mime_type="image/jpeg",
                    )
                except Exception:
                    pass  # Expected - DB is mocked out

                mock_exif_service.extract_exif.assert_called_once_with(
                    b"image data", "image/jpeg"
                )

    @pytest.mark.asyncio
    async def test_handles_exif_extraction_error(self, processor):
        """Should handle EXIF extraction errors gracefully."""
        mock_exif_service = MagicMock()
        mock_exif_service.extract_exif.side_effect = Exception("EXIF error")

        with patch("app.services.exif_service.get_exif_service", return_value=mock_exif_service):
            # Should log the error and not raise
            await processor._extract_exif_full(
                asset_id="asset-1",
                image_data=b"image data",
                mime_type="image/jpeg",
            )

            mock_exif_service.extract_exif.assert_called_once()


class TestDetectFacesFull:
    """Tests for _detect_faces_full database operations."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_stores_detected_faces(self, processor):
        """Should store Face records when faces are detected."""
        from contextlib import asynccontextmanager

        mock_face_service = MagicMock()
        mock_face_service.enabled = True
        mock_face_service.detect_faces = AsyncMock(return_value=[
            {
                "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 100},
                "confidence": 0.95,
                "landmarks": {},
                "attributes": {},
            }
        ])

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock()

        with patch("app.services.face_service.get_face_service", return_value=mock_face_service):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.Face") as mock_face_class:
                    mock_face_instance = MagicMock()
                    mock_face_instance.id = "face-123"
                    mock_face_class.return_value = mock_face_instance

                    with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
                        await processor._detect_faces_full(
                            asset_id="asset-1",
                            workspace_id="ws-1",
                            image_data=b"image data",
                        )

                        mock_session.add.assert_called()
                        mock_session.commit.assert_called()
                        mock_event_service.publish_event.assert_called()

    @pytest.mark.asyncio
    async def test_handles_event_publish_failure(self, processor):
        """Should not fail when face event publishing fails."""
        from contextlib import asynccontextmanager

        mock_face_service = MagicMock()
        mock_face_service.enabled = True
        mock_face_service.detect_faces = AsyncMock(return_value=[
            {
                "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 100},
                "confidence": 0.95,
            }
        ])

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock(side_effect=Exception("Event publish failed"))

        with patch("app.services.face_service.get_face_service", return_value=mock_face_service):
            with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
                with patch("app.consumers.asset_processor.Face") as mock_face_class:
                    mock_face_instance = MagicMock()
                    mock_face_instance.id = "face-123"
                    mock_face_class.return_value = mock_face_instance

                    with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
                        # Should not raise
                        await processor._detect_faces_full(
                            asset_id="asset-1",
                            workspace_id="ws-1",
                            image_data=b"image data",
                        )


class TestPublishEventsSuccess:
    """Tests for successful event publishing paths."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_publish_processing_event_success(self, processor):
        """Should successfully publish asset.processing event."""
        from datetime import datetime, timezone

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock()

        with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
            await processor._publish_asset_processing_event(
                asset_id="asset-1",
                workspace_id="ws-1",
                event_id="event-1",
                started_at=datetime.now(timezone.utc),
            )

            mock_event_service.publish_event.assert_called_once()
            call_kwargs = mock_event_service.publish_event.call_args[1]
            assert call_kwargs["topic"] == "asset.processing"
            assert call_kwargs["key"] == "ws-1"

    @pytest.mark.asyncio
    async def test_publish_processed_event_success(self, processor):
        """Should successfully publish asset.processed event."""
        from datetime import datetime, timezone

        mock_event_service = MagicMock()
        mock_event_service.publish_event = AsyncMock()

        now = datetime.now(timezone.utc)

        with patch("app.services.event_service.get_event_service", return_value=mock_event_service):
            await processor._publish_asset_processed_event(
                asset_id="asset-1",
                workspace_id="ws-1",
                event_id="event-1",
                processing_results={"thumbnails_generated": True},
                started_at=now,
                completed_at=now,
                processing_duration_ms=500,
            )

            mock_event_service.publish_event.assert_called_once()
            call_kwargs = mock_event_service.publish_event.call_args[1]
            assert call_kwargs["topic"] == "asset.processed"


class TestUpdateTaskStatusFields:
    """Tests for task status update with various fields."""

    @pytest.fixture
    def processor(self):
        """Create processor with mocked base."""
        with patch("app.consumers.asset_processor.BaseConsumer.__init__", return_value=None):
            from app.consumers.asset_processor import AssetProcessor
            return AssetProcessor()

    @pytest.mark.asyncio
    async def test_update_with_started_at(self, processor):
        """Should update task with started_at."""
        from app.models import TaskStatus
        from datetime import datetime, timezone
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            await processor._update_task_status(
                task_id="task-123",
                status=TaskStatus.PROCESSING,
                started_at=datetime.now(timezone.utc),
            )

            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_output_data(self, processor):
        """Should update task with output_data."""
        from app.models import TaskStatus
        from datetime import datetime, timezone
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            await processor._update_task_status(
                task_id="task-123",
                status=TaskStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                output_data={"thumbnail_key": "thumb.webp"},
            )

            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_error_message(self, processor):
        """Should update task with error_message."""
        from app.models import TaskStatus
        from datetime import datetime, timezone
        from contextlib import asynccontextmanager

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_db_session():
            yield mock_session

        with patch("app.consumers.asset_processor.get_db_session", mock_get_db_session):
            await processor._update_task_status(
                task_id="task-123",
                status=TaskStatus.FAILED,
                completed_at=datetime.now(timezone.utc),
                error_message="Processing failed due to corrupt image",
            )

            mock_session.execute.assert_called_once()
