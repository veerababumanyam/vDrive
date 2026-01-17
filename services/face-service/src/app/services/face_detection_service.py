"""Face detection service using Google Cloud Vision API."""

from typing import Optional
from dataclasses import dataclass
import io

import structlog
from PIL import Image

from ..core.config import settings
from ..core.circuit_breaker import circuit_breaker, CircuitOpenError

logger = structlog.get_logger()


@dataclass
class DetectedFace:
    """Represents a detected face with bounding box and confidence."""

    bounding_box: dict[str, float]  # {x, y, width, height} normalized 0-1
    confidence: float
    landmarks: Optional[dict[str, list[float]]] = None
    metadata: Optional[dict] = None


class FaceDetectionService:
    """
    Detects faces in images using Google Cloud Vision API.

    Features:
    - Circuit breaker for API resilience
    - Rate limiting support
    - Bounding box normalization
    """

    def __init__(self):
        self._client = None
        self._initialized = False

    def _get_client(self):
        """Lazy initialization of Vision API client."""
        if self._client is None and settings.GOOGLE_CLOUD_VISION_ENABLED:
            try:
                from google.cloud import vision

                self._client = vision.ImageAnnotatorClient()
                self._initialized = True
                logger.info("Google Cloud Vision client initialized")
            except Exception as e:
                logger.error("Failed to initialize Vision client", error=str(e))
                raise
        return self._client

    @circuit_breaker("google_vision")
    async def detect_faces(
        self,
        image_bytes: bytes,
        min_confidence: Optional[float] = None,
    ) -> list[DetectedFace]:
        """
        Detect faces in an image.

        Args:
            image_bytes: Raw image bytes
            min_confidence: Minimum detection confidence (default from settings)

        Returns:
            List of detected faces with normalized bounding boxes

        Raises:
            CircuitOpenError: If Vision API circuit breaker is open
        """
        if not settings.GOOGLE_CLOUD_VISION_ENABLED:
            logger.warning("Google Cloud Vision disabled, skipping face detection")
            return []

        min_conf = min_confidence or settings.FACE_DETECTION_MIN_CONFIDENCE

        try:
            from google.cloud import vision

            client = self._get_client()
            if not client:
                return []

            # Get image dimensions for normalization
            with Image.open(io.BytesIO(image_bytes)) as img:
                img_width, img_height = img.size

            # Create Vision API image
            image = vision.Image(content=image_bytes)

            # Call face detection
            response = client.face_detection(image=image)

            if response.error.message:
                logger.error("Vision API error", error=response.error.message)
                raise Exception(response.error.message)

            faces = []
            for face_annotation in response.face_annotations:
                # Convert detection confidence
                confidence = self._likelihood_to_confidence(
                    face_annotation.detection_confidence
                )

                if confidence < min_conf:
                    continue

                # Extract and normalize bounding box
                vertices = face_annotation.bounding_poly.vertices
                bounding_box = self._normalize_bounding_box(
                    vertices, img_width, img_height
                )

                # Extract landmarks
                landmarks = self._extract_landmarks(
                    face_annotation.landmarks, img_width, img_height
                )

                # Additional metadata
                metadata = {
                    "joy": self._likelihood_to_name(face_annotation.joy_likelihood),
                    "sorrow": self._likelihood_to_name(face_annotation.sorrow_likelihood),
                    "anger": self._likelihood_to_name(face_annotation.anger_likelihood),
                    "surprise": self._likelihood_to_name(face_annotation.surprise_likelihood),
                    "headwear": self._likelihood_to_name(face_annotation.headwear_likelihood),
                    "roll_angle": face_annotation.roll_angle,
                    "pan_angle": face_annotation.pan_angle,
                    "tilt_angle": face_annotation.tilt_angle,
                }

                faces.append(
                    DetectedFace(
                        bounding_box=bounding_box,
                        confidence=confidence,
                        landmarks=landmarks,
                        metadata=metadata,
                    )
                )

            logger.info(
                "Face detection complete",
                total_detected=len(response.face_annotations),
                above_threshold=len(faces),
            )

            return faces

        except CircuitOpenError:
            raise
        except Exception as e:
            logger.error("Face detection failed", error=str(e))
            raise

    def _normalize_bounding_box(
        self,
        vertices: list,
        img_width: int,
        img_height: int,
    ) -> dict[str, float]:
        """Normalize bounding box coordinates to 0-1 range."""
        if not vertices or len(vertices) < 4:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        # Get corners
        x_coords = [v.x for v in vertices if v.x is not None]
        y_coords = [v.y for v in vertices if v.y is not None]

        if not x_coords or not y_coords:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        return {
            "x": max(0, min_x / img_width),
            "y": max(0, min_y / img_height),
            "width": (max_x - min_x) / img_width,
            "height": (max_y - min_y) / img_height,
        }

    def _extract_landmarks(
        self,
        landmarks: list,
        img_width: int,
        img_height: int,
    ) -> Optional[dict[str, list[float]]]:
        """Extract and normalize facial landmarks."""
        if not landmarks:
            return None

        result = {}
        landmark_mapping = {
            "LEFT_EYE": "left_eye",
            "RIGHT_EYE": "right_eye",
            "NOSE_TIP": "nose_tip",
            "MOUTH_LEFT": "mouth_left",
            "MOUTH_RIGHT": "mouth_right",
            "LEFT_EAR_TRAGION": "left_ear",
            "RIGHT_EAR_TRAGION": "right_ear",
        }

        for landmark in landmarks:
            name = landmark_mapping.get(landmark.type_.name)
            if name:
                result[name] = [
                    landmark.position.x / img_width,
                    landmark.position.y / img_height,
                ]

        return result if result else None

    @staticmethod
    def _likelihood_to_confidence(likelihood_value: float) -> float:
        """Convert likelihood value to confidence score."""
        # Vision API returns values 0-5, convert to 0-1
        if hasattr(likelihood_value, "value"):
            return min(1.0, likelihood_value.value / 5.0)
        return min(1.0, float(likelihood_value))

    @staticmethod
    def _likelihood_to_name(likelihood) -> str:
        """Convert likelihood enum to string name."""
        likelihood_names = {
            0: "UNKNOWN",
            1: "VERY_UNLIKELY",
            2: "UNLIKELY",
            3: "POSSIBLE",
            4: "LIKELY",
            5: "VERY_LIKELY",
        }
        if hasattr(likelihood, "value"):
            return likelihood_names.get(likelihood.value, "UNKNOWN")
        return likelihood_names.get(int(likelihood), "UNKNOWN")


# Global service instance
face_detection_service = FaceDetectionService()
