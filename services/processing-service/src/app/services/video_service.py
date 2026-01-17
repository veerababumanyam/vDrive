"""Video processing service using ffmpeg."""

import subprocess
import tempfile
from typing import Optional

import structlog


logger = structlog.get_logger()


class VideoService:
    """Extract video thumbnails and metadata using ffmpeg."""

    def __init__(self):
        """Initialize video service."""
        # Check if ffmpeg is available
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("ffmpeg not available")
            logger.info("ffmpeg available")
        except Exception as e:
            logger.warning("ffmpeg not available - video processing disabled", error=str(e))
            self.available = False
            return

        self.available = True

    def extract_thumbnail(self, video_data: bytes, seek_position: str = "00:00:00") -> bytes:
        """
        Extract frame from video at specified position.

        Args:
            video_data: Video file bytes
            seek_position: Time position in format "HH:MM:SS" or "00:00:01"

        Returns:
            JPEG image bytes of extracted frame
        """
        if not self.available:
            raise RuntimeError("ffmpeg not available")

        try:
            # Create temporary files for input and output
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as output_file:
                output_path = output_file.name

            # Extract frame using ffmpeg
            # -ss: seek to position
            # -i: input file
            # -vframes 1: extract only 1 frame
            # -q:v 2: high quality JPEG (1-31, lower is better)
            cmd = [
                "ffmpeg",
                "-ss", seek_position,
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y",  # Overwrite output
                output_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(
                    "ffmpeg failed",
                    stderr=result.stderr.decode("utf-8"),
                    returncode=result.returncode,
                )
                raise RuntimeError(f"ffmpeg extraction failed: {result.stderr.decode('utf-8')}")

            # Read extracted frame
            with open(output_path, "rb") as f:
                frame_data = f.read()

            # Cleanup
            import os
            os.unlink(video_path)
            os.unlink(output_path)

            logger.debug("Video frame extracted", seek_position=seek_position, size=len(frame_data))

            return frame_data

        except Exception as e:
            logger.error("Failed to extract video frame", error=str(e))
            raise

    def extract_first_frame(self, video_data: bytes) -> bytes:
        """
        Extract first frame from video.

        Args:
            video_data: Video file bytes

        Returns:
            JPEG image bytes
        """
        return self.extract_thumbnail(video_data, seek_position="00:00:01")

    def extract_representative_frame(self, video_data: bytes) -> bytes:
        """
        Extract representative frame from video (25% through duration).

        Args:
            video_data: Video file bytes

        Returns:
            JPEG image bytes
        """
        try:
            # Get video duration first
            duration = self.get_video_duration(video_data)
            if not duration:
                # Fallback to first frame if duration unknown
                return self.extract_first_frame(video_data)

            # Calculate 25% position
            seek_seconds = int(duration * 0.25)
            hours = seek_seconds // 3600
            minutes = (seek_seconds % 3600) // 60
            seconds = seek_seconds % 60
            seek_position = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            return self.extract_thumbnail(video_data, seek_position=seek_position)

        except Exception as e:
            logger.warning("Failed to extract representative frame, using first frame", error=str(e))
            return self.extract_first_frame(video_data)

    def get_video_duration(self, video_data: bytes) -> Optional[int]:
        """
        Get video duration in seconds.

        Args:
            video_data: Video file bytes

        Returns:
            Duration in seconds or None if unknown
        """
        if not self.available:
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name

            # Use ffprobe to get duration
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
            )

            # Cleanup
            import os
            os.unlink(video_path)

            if result.returncode == 0:
                duration_str = result.stdout.decode("utf-8").strip()
                return int(float(duration_str))

            return None

        except Exception as e:
            logger.debug("Failed to get video duration", error=str(e))
            return None

    def get_video_metadata(self, video_data: bytes) -> dict:
        """
        Extract video metadata (codec, resolution, duration).

        Args:
            video_data: Video file bytes

        Returns:
            dict with video metadata
        """
        if not self.available:
            return {}

        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name

            # Use ffprobe to get detailed metadata
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,duration,bit_rate",
                "-show_entries", "format=duration,size,bit_rate",
                "-of", "json",
                video_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
            )

            # Cleanup
            import os
            os.unlink(video_path)

            if result.returncode == 0:
                import json
                metadata = json.loads(result.stdout.decode("utf-8"))

                # Parse metadata
                video_stream = metadata.get("streams", [{}])[0]
                format_data = metadata.get("format", {})

                return {
                    "codec": video_stream.get("codec_name"),
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "duration": float(format_data.get("duration", 0)),
                    "bitrate": int(format_data.get("bit_rate", 0)),
                    "size": int(format_data.get("size", 0)),
                }

            return {}

        except Exception as e:
            logger.error("Failed to extract video metadata", error=str(e))
            return {}


# Singleton instance
_video_service: Optional[VideoService] = None


def get_video_service() -> VideoService:
    """Get video service instance."""
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
