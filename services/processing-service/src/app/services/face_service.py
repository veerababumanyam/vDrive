"""Face detection service using Google Cloud Vision API."""

import asyncio
import time
from typing import Optional, List, Dict

import structlog

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    vision = None

from ..core.config import settings
from ..core.metrics import (
    gcv_requests_total,
    gcv_request_duration_seconds,
    gcv_rate_limit_hits_total,
    faces_detected_total,
)

logger = structlog.get_logger()


class FaceService:
    """Detect faces using Google Cloud Vision API."""

    def __init__(self):
        """Initialize face detection service."""
        self.enabled = settings.GOOGLE_CLOUD_VISION_ENABLED and GOOGLE_VISION_AVAILABLE

        if not GOOGLE_VISION_AVAILABLE:
            logger.warning("google-cloud-vision not available - face detection disabled")
            return

        if not self.enabled:
            logger.info("Face detection disabled in configuration")
            return

        # Initialize Google Cloud Vision client
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision client initialized")
        except Exception as e:
            logger.error("Failed to initialize Google Cloud Vision client", error=str(e))
            self.enabled = False

        # Rate limiting
        self.rate_limit = settings.GOOGLE_CLOUD_VISION_RATE_LIMIT  # requests/minute
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window_start = time.time()

    async def detect_faces(self, image_data: bytes) -> List[Dict]:
        """
        Detect faces in image using Google Cloud Vision.

        Args:
            image_data: Image bytes

        Returns:
            List of face detection results with bounding boxes and confidence
        """
        if not self.enabled:
            logger.debug("Face detection disabled, skipping")
            return []

        try:
            # Rate limiting check
            await self._check_rate_limit()

            # Prepare image
            image = vision.Image(content=image_data)

            # Call Google Cloud Vision API
            start_time = time.time()

            response = self.client.face_detection(image=image)

            duration = time.time() - start_time

            # Update metrics
            gcv_request_duration_seconds.labels(operation="face_detection").observe(duration)
            gcv_requests_total.labels(operation="face_detection", status="success").inc()

            if response.error.message:
                logger.error(
                    "Google Cloud Vision API error",
                    error=response.error.message,
                )
                gcv_requests_total.labels(operation="face_detection", status="error").inc()
                return []

            # Parse face annotations
            faces = self._parse_face_annotations(response.face_annotations)

            faces_detected_total.inc(len(faces))

            logger.info("Faces detected", face_count=len(faces), duration_seconds=duration)

            return faces

        except Exception as e:
            logger.error("Failed to detect faces", error=str(e))
            gcv_requests_total.labels(operation="face_detection", status="error").inc()
            return []

    def _parse_face_annotations(self, annotations) -> List[Dict]:
        """
        Parse Google Cloud Vision face annotations.

        Args:
            annotations: Face annotations from API response

        Returns:
            List of face data dicts
        """
        faces = []

        for face in annotations:
            # Extract bounding box (normalized coordinates 0-1)
            vertices = face.bounding_poly.vertices
            if not vertices or len(vertices) < 4:
                continue

            # Normalize coordinates (assuming they're in pixels)
            # We'll store as fractions for database compatibility
            bounding_box = {
                "x_min": vertices[0].x if hasattr(vertices[0], 'x') else 0,
                "y_min": vertices[0].y if hasattr(vertices[0], 'y') else 0,
                "x_max": vertices[2].x if hasattr(vertices[2], 'x') else 0,
                "y_max": vertices[2].y if hasattr(vertices[2], 'y') else 0,
            }

            # Extract landmarks (eyes, nose, mouth)
            landmarks = self._parse_landmarks(face.landmarks)

            # Extract attributes
            attributes = {
                "joy_likelihood": self._likelihood_to_string(face.joy_likelihood),
                "sorrow_likelihood": self._likelihood_to_string(face.sorrow_likelihood),
                "anger_likelihood": self._likelihood_to_string(face.anger_likelihood),
                "surprise_likelihood": self._likelihood_to_string(face.surprise_likelihood),
                "under_exposed_likelihood": self._likelihood_to_string(face.under_exposed_likelihood),
                "blurred_likelihood": self._likelihood_to_string(face.blurred_likelihood),
                "headwear_likelihood": self._likelihood_to_string(face.headwear_likelihood),
            }

            faces.append({
                "bounding_box": bounding_box,
                "confidence": face.detection_confidence,
                "landmarks": landmarks,
                "attributes": attributes,
                "pan_angle": face.pan_angle,
                "tilt_angle": face.tilt_angle,
                "roll_angle": face.roll_angle,
            })

        return faces

    def _parse_landmarks(self, landmarks) -> Dict:
        """Parse facial landmarks."""
        landmark_dict = {}
        for landmark in landmarks:
            landmark_type = str(landmark.type_).replace("Type.", "")
            landmark_dict[landmark_type] = {
                "x": landmark.position.x,
                "y": landmark.position.y,
                "z": landmark.position.z if hasattr(landmark.position, 'z') else 0,
            }
        return landmark_dict

    def _likelihood_to_string(self, likelihood) -> str:
        """Convert likelihood enum to string."""
        likelihood_str = str(likelihood)
        # Remove enum prefix
        if "." in likelihood_str:
            return likelihood_str.split(".")[-1]
        return likelihood_str

    async def _check_rate_limit(self):
        """
        Check and enforce rate limiting.

        Implements token bucket algorithm with 1-minute windows.
        """
        current_time = time.time()

        # Reset window if 1 minute has passed
        if current_time - self.rate_limit_window_start >= 60:
            self.request_count = 0
            self.rate_limit_window_start = current_time

        # Check if rate limit exceeded
        if self.request_count >= self.rate_limit:
            # Calculate wait time until next window
            wait_time = 60 - (current_time - self.rate_limit_window_start)

            logger.warning(
                "Rate limit reached, waiting",
                wait_time_seconds=wait_time,
                current_count=self.request_count,
                rate_limit=self.rate_limit,
            )

            gcv_rate_limit_hits_total.inc()

            # Wait until next window
            await asyncio.sleep(wait_time)

            # Reset after waiting
            self.request_count = 0
            self.rate_limit_window_start = time.time()

        # Increment request count
        self.request_count += 1

    def generate_face_embedding(self, face_image: bytes) -> Optional[List[float]]:
        """
        Generate 512-dimensional face embedding for similarity matching.

        Uses FaceNet (InceptionResnetV1) pretrained on VGGFace2 dataset.

        Args:
            face_image: Cropped face image bytes (JPEG/PNG)

        Returns:
            512-dimensional embedding vector or None
        """
        try:
            from facenet_pytorch import InceptionResnetV1
            from PIL import Image
            import io
            import torch

            # Load model on first use (lazy initialization)
            if not hasattr(self, '_facenet_model'):
                self._facenet_model = InceptionResnetV1(pretrained='vggface2').eval()
                logger.info("FaceNet model loaded for embedding generation")

            # Load and preprocess face image
            img = Image.open(io.BytesIO(face_image)).convert('RGB')

            # Resize to 160x160 (FaceNet input size)
            img = img.resize((160, 160), Image.Resampling.LANCZOS)

            # Convert to tensor and normalize
            from torchvision import transforms
            preprocess = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ])
            img_tensor = preprocess(img).unsqueeze(0)  # Add batch dimension

            # Generate embedding
            with torch.no_grad():
                embedding = self._facenet_model(img_tensor)

            # Convert to list
            embedding_list = embedding.squeeze().tolist()

            logger.debug("Face embedding generated", embedding_dim=len(embedding_list))

            return embedding_list

        except ImportError:
            logger.warning("facenet-pytorch not installed - face embedding disabled")
            return None
        except Exception as e:
            logger.error("Failed to generate face embedding", error=str(e))
            return None


# Singleton instance
_face_service: Optional[FaceService] = None


def get_face_service() -> FaceService:
    """Get face detection service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceService()
    return _face_service
