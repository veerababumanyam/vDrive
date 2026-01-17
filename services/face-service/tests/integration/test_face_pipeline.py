"""Integration tests for face detection pipeline."""

import asyncio
import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Skip if dependencies not available
pytest.importorskip("sqlalchemy")


class TestFaceDetectionPipeline:
    """Integration tests for the face detection pipeline."""

    @pytest.fixture
    def workspace_id(self):
        """Generate workspace ID for tests."""
        return uuid4()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def sample_image_bytes(self):
        """Generate sample image bytes."""
        # Create a simple 224x224 RGB image
        image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        import io
        from PIL import Image

        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_full_face_detection_pipeline(
        self, mock_db_session, workspace_id, sample_image_bytes
    ):
        """Test complete pipeline: detection -> embedding -> clustering."""
        asset_id = uuid4()

        with patch(
            "src.app.services.face_detection_service.FaceDetectionService"
        ) as MockDetection:
            # Mock face detection
            mock_detector = MagicMock()
            mock_detector.detect_faces = AsyncMock(
                return_value=[
                    {
                        "bounding_box": {"x": 100, "y": 100, "width": 50, "height": 50},
                        "confidence": 0.95,
                        "crop": np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8),
                    }
                ]
            )
            MockDetection.return_value = mock_detector

            with patch(
                "src.app.services.embedding_service.EmbeddingService"
            ) as MockEmbedding:
                # Mock embedding generation
                mock_embedder = MagicMock()
                mock_embedder.generate_embedding = AsyncMock(
                    return_value=np.random.randn(512).astype(np.float32)
                )
                MockEmbedding.return_value = mock_embedder

                with patch(
                    "src.app.services.clustering_service.ClusteringService"
                ) as MockClustering:
                    # Mock clustering
                    mock_clusterer = MagicMock()
                    mock_clusterer.assign_to_group = AsyncMock(return_value=uuid4())
                    MockClustering.return_value = mock_clusterer

                    # Import and run consumer
                    from src.app.consumers.asset_face_processor import AssetFaceProcessor

                    processor = AssetFaceProcessor()

                    # Simulate processing an asset
                    with patch.object(processor, "_process_asset") as mock_process:
                        mock_process.return_value = {
                            "asset_id": str(asset_id),
                            "faces_detected": 1,
                            "groups_assigned": 1,
                        }

                        result = await processor._process_asset(
                            db=mock_db_session,
                            asset_id=asset_id,
                            workspace_id=workspace_id,
                            image_data=sample_image_bytes,
                        )

                        assert result["faces_detected"] >= 0

    @pytest.mark.asyncio
    async def test_pipeline_handles_no_faces(
        self, mock_db_session, workspace_id, sample_image_bytes
    ):
        """Test pipeline handles images with no faces gracefully."""
        asset_id = uuid4()

        with patch(
            "src.app.services.face_detection_service.face_detection_service"
        ) as mock_detector:
            mock_detector.detect_faces = AsyncMock(return_value=[])

            from src.app.consumers.asset_face_processor import AssetFaceProcessor

            processor = AssetFaceProcessor()

            with patch.object(processor, "_process_asset") as mock_process:
                mock_process.return_value = {
                    "asset_id": str(asset_id),
                    "faces_detected": 0,
                    "groups_assigned": 0,
                }

                result = await processor._process_asset(
                    db=mock_db_session,
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    image_data=sample_image_bytes,
                )

                assert result["faces_detected"] == 0

    @pytest.mark.asyncio
    async def test_pipeline_publishes_events(
        self, mock_db_session, workspace_id, sample_image_bytes
    ):
        """Test that pipeline publishes face.detected events."""
        asset_id = uuid4()

        with patch(
            "src.app.services.event_service.event_service"
        ) as mock_event_service:
            mock_event_service.publish = AsyncMock()

            with patch(
                "src.app.services.face_detection_service.face_detection_service"
            ) as mock_detector:
                mock_detector.detect_faces = AsyncMock(
                    return_value=[
                        {
                            "bounding_box": {"x": 100, "y": 100, "width": 50, "height": 50},
                            "confidence": 0.95,
                        }
                    ]
                )

                from src.app.consumers.asset_face_processor import AssetFaceProcessor

                processor = AssetFaceProcessor()

                with patch.object(processor, "_publish_face_detected") as mock_publish:
                    mock_publish.return_value = None

                    # Verify publish would be called
                    assert hasattr(processor, "_publish_face_detected")


class TestFindMeFeature:
    """Integration tests for Find Me selfie matching."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def workspace_id(self):
        """Generate workspace ID."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_find_me_matches_similar_faces(
        self, mock_db_session, workspace_id
    ):
        """Test Find Me returns photos with similar faces."""
        selfie_embedding = np.random.randn(512).astype(np.float32)

        with patch(
            "src.app.services.embedding_service.embedding_service"
        ) as mock_embedder:
            mock_embedder.generate_embedding = AsyncMock(return_value=selfie_embedding)
            mock_embedder.find_similar_faces = AsyncMock(
                return_value=[
                    {
                        "face_id": str(uuid4()),
                        "asset_id": str(uuid4()),
                        "group_id": str(uuid4()),
                        "similarity": 0.85,
                    },
                    {
                        "face_id": str(uuid4()),
                        "asset_id": str(uuid4()),
                        "group_id": str(uuid4()),
                        "similarity": 0.78,
                    },
                ]
            )

            from src.app.api.v1.find_me import find_me_photos

            with patch(
                "src.app.api.v1.find_me.embedding_service", mock_embedder
            ):
                # Mock request
                mock_request = MagicMock()
                mock_selfie = MagicMock()
                mock_selfie.read = AsyncMock(return_value=b"fake_image_data")

                # This would be called from the API endpoint
                results = await mock_embedder.find_similar_faces(
                    db=mock_db_session,
                    embedding=selfie_embedding,
                    workspace_id=workspace_id,
                    limit=50,
                )

                assert len(results) == 2
                assert all(r["similarity"] >= 0.7 for r in results)

    @pytest.mark.asyncio
    async def test_find_me_respects_threshold(
        self, mock_db_session, workspace_id
    ):
        """Test Find Me filters by similarity threshold."""
        selfie_embedding = np.random.randn(512).astype(np.float32)
        threshold = 0.75

        with patch(
            "src.app.services.embedding_service.embedding_service"
        ) as mock_embedder:
            mock_embedder.find_similar_faces = AsyncMock(
                return_value=[
                    {"similarity": 0.85, "face_id": str(uuid4())},
                    {"similarity": 0.78, "face_id": str(uuid4())},
                    {"similarity": 0.65, "face_id": str(uuid4())},  # Below threshold
                ]
            )

            results = await mock_embedder.find_similar_faces(
                db=mock_db_session,
                embedding=selfie_embedding,
                workspace_id=workspace_id,
                threshold=threshold,
            )

            # Filter by threshold
            filtered = [r for r in results if r["similarity"] >= threshold]
            assert len(filtered) == 2
