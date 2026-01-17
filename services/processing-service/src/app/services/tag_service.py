"""Tag detection service using Google Cloud Vision API."""

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
from ..core.metrics import gcv_requests_total, gcv_request_duration_seconds

logger = structlog.get_logger()


class TagService:
    """Detect image labels/tags using Google Cloud Vision API."""

    def __init__(self):
        """Initialize tag detection service."""
        self.enabled = settings.GOOGLE_CLOUD_VISION_ENABLED and GOOGLE_VISION_AVAILABLE

        if not GOOGLE_VISION_AVAILABLE:
            logger.warning("google-cloud-vision not available - tag detection disabled")
            return

        if not self.enabled:
            logger.info("Tag detection disabled in configuration")
            return

        # Initialize Google Cloud Vision client
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision client initialized for tag detection")
        except Exception as e:
            logger.error("Failed to initialize Google Cloud Vision client", error=str(e))
            self.enabled = False

        # Configuration
        self.max_results = getattr(settings, 'TAG_DETECTION_MAX_RESULTS', 20)
        self.min_confidence = getattr(settings, 'TAG_DETECTION_MIN_CONFIDENCE', 0.7)

    async def detect_tags(self, image_data: bytes) -> List[Dict]:
        """
        Detect labels/tags in image using Google Cloud Vision.

        Args:
            image_data: Image bytes

        Returns:
            List of tag detection results with label and confidence
        """
        if not self.enabled:
            logger.debug("Tag detection disabled, skipping")
            return []

        try:
            # Prepare image
            image = vision.Image(content=image_data)

            # Call Google Cloud Vision API
            start_time = time.time()

            response = self.client.label_detection(
                image=image,
                max_results=self.max_results,
            )

            duration = time.time() - start_time

            # Update metrics
            gcv_request_duration_seconds.labels(operation="label_detection").observe(duration)
            gcv_requests_total.labels(operation="label_detection", status="success").inc()

            if response.error.message:
                logger.error(
                    "Google Cloud Vision API error",
                    error=response.error.message,
                )
                gcv_requests_total.labels(operation="label_detection", status="error").inc()
                return []

            # Parse label annotations
            tags = self._parse_label_annotations(response.label_annotations)

            logger.info("Tags detected", tag_count=len(tags), duration_seconds=duration)

            return tags

        except Exception as e:
            logger.error("Failed to detect tags", error=str(e))
            gcv_requests_total.labels(operation="label_detection", status="error").inc()
            return []

    def _parse_label_annotations(self, annotations) -> List[Dict]:
        """
        Parse Google Cloud Vision label annotations.

        Args:
            annotations: Label annotations from API response

        Returns:
            List of tag data dicts
        """
        tags = []

        for label in annotations:
            # Filter by minimum confidence
            if label.score < self.min_confidence:
                continue

            tags.append({
                "tag": label.description,
                "confidence": label.score,
                "mid": label.mid,  # Google Knowledge Graph ID
                "topicality": label.topicality,
            })

        return tags


# Singleton instance
_tag_service: Optional[TagService] = None


def get_tag_service() -> TagService:
    """Get tag detection service instance."""
    global _tag_service
    if _tag_service is None:
        _tag_service = TagService()
    return _tag_service
