"""Unit tests for face detection service."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.app.services.face_service import FaceService, get_face_service


@pytest.fixture
def mock_settings():
    """Create mock settings for face service."""
    with patch("src.app.services.face_service.settings") as mock:
        mock.GOOGLE_CLOUD_VISION_ENABLED = True
        mock.GOOGLE_CLOUD_VISION_RATE_LIMIT = 60
        yield mock


@pytest.fixture
def face_service_with_mock_client(mock_settings, mock_gcv_client):
    """Create face service with mocked GCV client."""
    with patch("src.app.services.face_service.GOOGLE_VISION_AVAILABLE", True):
        with patch("src.app.services.face_service.vision") as mock_vision:
            mock_vision.ImageAnnotatorClient.return_value = mock_gcv_client
            mock_vision.Image = MagicMock()
            service = FaceService()
            service.client = mock_gcv_client
            service.enabled = True
            yield service


class TestFaceServiceInitialization:
    """Test face service initialization."""

    def test_disabled_when_gcv_not_available(self):
        """Should be disabled when google-cloud-vision not installed."""
        with patch("src.app.services.face_service.GOOGLE_VISION_AVAILABLE", False):
            with patch("src.app.services.face_service.settings") as mock_settings:
                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = True
                service = FaceService()

                assert service.enabled is False

    def test_disabled_when_config_disabled(self):
        """Should be disabled when config says disabled."""
        with patch("src.app.services.face_service.GOOGLE_VISION_AVAILABLE", True):
            with patch("src.app.services.face_service.settings") as mock_settings:
                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False
                service = FaceService()

                assert service.enabled is False


class TestFaceDetection:
    """Test face detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_faces_returns_list(
        self, face_service_with_mock_client, sample_jpeg_bytes
    ):
        """Should return list of detected faces."""
        result = await face_service_with_mock_client.detect_faces(sample_jpeg_bytes)

        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_detect_faces_returns_bounding_box(
        self, face_service_with_mock_client, sample_jpeg_bytes
    ):
        """Each face should have bounding box."""
        result = await face_service_with_mock_client.detect_faces(sample_jpeg_bytes)

        face = result[0]
        assert "bounding_box" in face
        assert "x_min" in face["bounding_box"]
        assert "y_min" in face["bounding_box"]
        assert "x_max" in face["bounding_box"]
        assert "y_max" in face["bounding_box"]

    @pytest.mark.asyncio
    async def test_detect_faces_returns_confidence(
        self, face_service_with_mock_client, sample_jpeg_bytes
    ):
        """Each face should have confidence score."""
        result = await face_service_with_mock_client.detect_faces(sample_jpeg_bytes)

        face = result[0]
        assert "confidence" in face
        assert isinstance(face["confidence"], (int, float))
        assert 0 <= face["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_detect_faces_returns_attributes(
        self, face_service_with_mock_client, sample_jpeg_bytes
    ):
        """Each face should have attributes."""
        result = await face_service_with_mock_client.detect_faces(sample_jpeg_bytes)

        face = result[0]
        assert "attributes" in face
        assert "joy_likelihood" in face["attributes"]

    @pytest.mark.asyncio
    async def test_detect_faces_when_disabled_returns_empty(self, mock_settings):
        """Should return empty list when service is disabled."""
        with patch("src.app.services.face_service.GOOGLE_VISION_AVAILABLE", True):
            with patch("src.app.services.face_service.vision") as mock_vision:
                mock_vision.ImageAnnotatorClient.return_value = MagicMock()
                service = FaceService()
                service.enabled = False

                result = await service.detect_faces(b"test image")

                assert result == []

    @pytest.mark.asyncio
    async def test_detect_faces_handles_api_error(
        self, face_service_with_mock_client
    ):
        """Should handle API errors gracefully."""
        # Make client raise exception
        face_service_with_mock_client.client.face_detection.side_effect = Exception(
            "API Error"
        )

        result = await face_service_with_mock_client.detect_faces(b"test image")

        assert result == []


class TestFaceAnnotationParsing:
    """Test face annotation parsing."""

    def test_parse_face_annotations_extracts_bounding_box(
        self, face_service_with_mock_client
    ):
        """Should extract bounding box from annotations."""
        # Create mock annotation
        mock_face = MagicMock()
        mock_face.detection_confidence = 0.9
        mock_face.pan_angle = 0.0
        mock_face.tilt_angle = 0.0
        mock_face.roll_angle = 0.0
        mock_face.joy_likelihood = 1
        mock_face.sorrow_likelihood = 5
        mock_face.anger_likelihood = 5
        mock_face.surprise_likelihood = 5
        mock_face.under_exposed_likelihood = 5
        mock_face.blurred_likelihood = 5
        mock_face.headwear_likelihood = 5
        mock_face.landmarks = []

        # Mock vertices
        mock_v1 = MagicMock()
        mock_v1.x = 10
        mock_v1.y = 20
        mock_v2 = MagicMock()
        mock_v2.x = 30
        mock_v2.y = 20
        mock_v3 = MagicMock()
        mock_v3.x = 30
        mock_v3.y = 40
        mock_v4 = MagicMock()
        mock_v4.x = 10
        mock_v4.y = 40

        mock_face.bounding_poly.vertices = [mock_v1, mock_v2, mock_v3, mock_v4]

        result = face_service_with_mock_client._parse_face_annotations([mock_face])

        assert len(result) == 1
        bbox = result[0]["bounding_box"]
        assert bbox["x_min"] == 10
        assert bbox["y_min"] == 20
        assert bbox["x_max"] == 30
        assert bbox["y_max"] == 40

    def test_parse_face_annotations_skips_invalid_bounding_box(
        self, face_service_with_mock_client
    ):
        """Should skip faces with invalid bounding boxes."""
        mock_face = MagicMock()
        mock_face.bounding_poly.vertices = []  # No vertices

        result = face_service_with_mock_client._parse_face_annotations([mock_face])

        assert len(result) == 0


class TestLandmarkParsing:
    """Test facial landmark parsing."""

    def test_parse_landmarks_returns_dict(self, face_service_with_mock_client):
        """Should parse landmarks into dict."""
        mock_landmark = MagicMock()
        mock_landmark.type_ = "LEFT_EYE"
        mock_landmark.position.x = 100.0
        mock_landmark.position.y = 200.0
        mock_landmark.position.z = 0.0

        result = face_service_with_mock_client._parse_landmarks([mock_landmark])

        assert isinstance(result, dict)
        assert "LEFT_EYE" in result
        assert result["LEFT_EYE"]["x"] == 100.0
        assert result["LEFT_EYE"]["y"] == 200.0


class TestLikelihoodConversion:
    """Test likelihood enum conversion."""

    def test_likelihood_to_string(self, face_service_with_mock_client):
        """Should convert likelihood enum to string."""
        mock_likelihood = "Likelihood.VERY_LIKELY"

        result = face_service_with_mock_client._likelihood_to_string(mock_likelihood)

        assert result == "VERY_LIKELY"


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(
        self, face_service_with_mock_client
    ):
        """Should reset rate limit counter after 60 seconds."""
        import time

        # Set window start to 61 seconds ago
        face_service_with_mock_client.rate_limit_window_start = time.time() - 61
        face_service_with_mock_client.request_count = 100

        # Should reset counter
        await face_service_with_mock_client._check_rate_limit()

        assert face_service_with_mock_client.request_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit_increments_counter(
        self, face_service_with_mock_client
    ):
        """Should increment request counter."""
        initial_count = face_service_with_mock_client.request_count

        await face_service_with_mock_client._check_rate_limit()

        assert face_service_with_mock_client.request_count == initial_count + 1


class TestFaceEmbedding:
    """Test face embedding generation."""

    def test_generate_face_embedding_not_implemented(
        self, face_service_with_mock_client
    ):
        """Should return None (not implemented yet)."""
        result = face_service_with_mock_client.generate_face_embedding(b"face image")

        assert result is None


class TestSingleton:
    """Test singleton pattern."""

    def test_get_face_service_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        # Reset singleton
        import src.app.services.face_service as module
        module._face_service = None

        with patch("src.app.services.face_service.GOOGLE_VISION_AVAILABLE", False):
            with patch("src.app.services.face_service.settings") as mock_settings:
                mock_settings.GOOGLE_CLOUD_VISION_ENABLED = False
                service1 = get_face_service()
                service2 = get_face_service()

                assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
