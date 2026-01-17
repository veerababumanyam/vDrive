"""Asset processing consumer for upload.completed events."""

import structlog
from datetime import datetime, timezone
from sqlalchemy import select, update
from decimal import Decimal

from .base_consumer import BaseConsumer
from ..core.metrics import tasks_processed_total
from ..core.database import get_db_session
from ..models import Asset, AssetMetadata, Face, ProcessingTask, TaskType, TaskStatus

logger = structlog.get_logger()


class AssetProcessor(BaseConsumer):
    """
    Processes upload.completed events to generate thumbnails, extract EXIF, and detect faces.

    Consumes from: upload.completed topic
    Produces: asset.processing, asset.processed events
    """

    def __init__(self):
        """Initialize AssetProcessor consumer."""
        super().__init__(
            topics=["upload.completed"],
            consumer_group="asset-processor",
            max_retries=3,
            auto_commit=False,
        )

    async def process_event(self, event: dict):
        """
        Process upload.completed event.

        Workflow:
        1. Verify event schema
        2. Create ProcessingTask record
        3. Download encrypted asset from R2
        4. Decrypt asset
        5. Generate thumbnails (WebP)
        6. Extract EXIF metadata
        7. Detect faces (if enabled for workspace)
        8. Update Asset record with derivatives
        9. Publish asset.processed event

        Args:
            event: upload.completed event data
        """
        try:
            # Extract event fields
            event_type = event.get("event_type")
            upload_id = event.get("upload_id")
            workspace_id = event.get("workspace_id")
            asset_id = event.get("asset_id")
            filename = event.get("filename")
            mime_type = event.get("mime_type")
            file_size = event.get("file_size")
            storage_path = event.get("storage_path")
            is_encrypted = event.get("is_encrypted", True)
            encryption_key_id = event.get("encryption_key_id")

            logger.info(
                "Processing asset",
                asset_id=asset_id,
                filename=filename,
                mime_type=mime_type,
                file_size=file_size,
            )

            # Validate event
            if event_type != "upload.completed":
                raise ValueError(f"Unexpected event type: {event_type}")

            if not all([upload_id, workspace_id, asset_id, storage_path]):
                raise ValueError("Missing required fields in upload.completed event")

            # Create ProcessingTask record
            task = await self._create_processing_task(
                asset_id=asset_id,
                workspace_id=workspace_id,
                task_type=TaskType.THUMBNAIL_GENERATION,
                input_data={
                    "upload_id": upload_id,
                    "filename": filename,
                    "mime_type": mime_type,
                    "file_size": file_size,
                    "storage_path": storage_path,
                    "is_encrypted": is_encrypted,
                },
            )

            # Update task status to PROCESSING
            await self._update_task_status(
                task.id, TaskStatus.PROCESSING, started_at=datetime.now(timezone.utc)
            )

            # Process based on MIME type
            processing_results = {}
            if mime_type.startswith("image/"):
                processing_results = await self._process_image(
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    storage_path=storage_path,
                    mime_type=mime_type,
                    is_encrypted=is_encrypted,
                    encryption_key_id=encryption_key_id,
                )
            elif mime_type.startswith("video/"):
                processing_results = await self._process_video(
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    storage_path=storage_path,
                    mime_type=mime_type,
                    is_encrypted=is_encrypted,
                    encryption_key_id=encryption_key_id,
                )
            else:
                logger.warning("Unsupported MIME type for processing", mime_type=mime_type)

            # Mark task as completed with results
            await self._update_task_status(
                task.id,
                TaskStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                output_data=processing_results,
            )

            # Update metrics
            tasks_processed_total.labels(
                task_type="asset_processing",
                status="completed",
            ).inc()

            logger.info("Asset processing completed", asset_id=asset_id, task_id=task.id)

        except Exception as e:
            logger.error(
                "Failed to process asset",
                asset_id=event.get("asset_id"),
                error=str(e),
            )

            # Mark task as failed if it was created
            if 'task' in locals() and task:
                await self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    completed_at=datetime.now(timezone.utc),
                    error_message=str(e),
                )

            # Update metrics
            tasks_processed_total.labels(
                task_type="asset_processing",
                status="failed",
            ).inc()

            raise

    async def _process_image(
        self,
        asset_id: str,
        workspace_id: str,
        storage_path: str,
        mime_type: str,
        is_encrypted: bool,
        encryption_key_id: str,
    ):
        """
        Process image asset.

        Steps:
        1. Download from R2
        2. Decrypt if encrypted
        3. Generate thumbnails (300px, 1200px, 20px LQIP)
        4. Extract EXIF metadata
        5. Detect faces (if enabled)
        6. Upload derivatives to R2
        7. Update Asset record
        """
        logger.info("Processing image", asset_id=asset_id, mime_type=mime_type)

        try:
            # Download and decrypt image
            image_data = await self._download_and_decrypt(
                storage_path=storage_path,
                workspace_id=workspace_id,
                is_encrypted=is_encrypted,
            )

            # Generate thumbnails
            thumbnail_keys = await self._generate_thumbnails_full(
                asset_id=asset_id,
                workspace_id=workspace_id,
                image_data=image_data,
                mime_type=mime_type,
            )

            # Extract EXIF metadata
            await self._extract_exif_full(
                asset_id=asset_id,
                image_data=image_data,
                mime_type=mime_type,
            )

            # Detect faces (optional)
            await self._detect_faces_full(
                asset_id=asset_id,
                workspace_id=workspace_id,
                image_data=image_data,
            )

            # Detect tags/labels (optional)
            await self._detect_tags_full(
                asset_id=asset_id,
                image_data=image_data,
            )

            # Update Asset record with derivative keys
            await self._update_asset_derivatives(asset_id, thumbnail_keys)

            logger.info("Image processing completed", asset_id=asset_id)

            # Return processing results
            return {
                "thumbnails_generated": True,
                "thumbnail_key": thumbnail_keys.get("thumbnail_key"),
                "preview_key": thumbnail_keys.get("preview_key"),
                "lqip_generated": thumbnail_keys.get("lqip_base64") is not None,
                "exif_extracted": True,
                "faces_detected": True,
                "tags_detected": True,
                "processing_time_ms": 0,  # TODO: Track actual time
            }

        except Exception as e:
            logger.error("Image processing failed", asset_id=asset_id, error=str(e))
            raise

    async def _process_video(
        self,
        asset_id: str,
        workspace_id: str,
        storage_path: str,
        mime_type: str,
        is_encrypted: bool,
        encryption_key_id: str,
    ):
        """
        Process video asset.

        Steps:
        1. Extract video thumbnail (first frame)
        2. Extract video metadata (duration, codec, resolution)
        """
        logger.info("Processing video", asset_id=asset_id, mime_type=mime_type)

        try:
            from ..services.video_service import get_video_service
            from ..services.thumbnail_service import get_thumbnail_service
            from ..services.storage_service import get_storage_service

            # Download and decrypt video
            video_data = await self._download_and_decrypt(
                storage_path=storage_path,
                workspace_id=workspace_id,
                is_encrypted=is_encrypted,
            )

            video_service = get_video_service()

            if not video_service.available:
                logger.warning("ffmpeg not available, skipping video processing")
                return

            # Extract first frame
            frame_jpeg = video_service.extract_first_frame(video_data)

            # Generate thumbnails from frame
            thumbnail_service = get_thumbnail_service()
            thumbnails = thumbnail_service.generate_thumbnails(frame_jpeg, "image/jpeg")

            # Upload thumbnails to R2
            storage_service = get_storage_service()

            thumbnail_key = f"workspaces/{workspace_id}/assets/{asset_id}/thumbnail.webp"
            storage_service.upload_object(
                key=thumbnail_key,
                data=thumbnails["thumbnail"],
                content_type="image/webp",
            )

            preview_key = f"workspaces/{workspace_id}/assets/{asset_id}/preview.webp"
            storage_service.upload_object(
                key=preview_key,
                data=thumbnails["preview"],
                content_type="image/webp",
            )

            # Generate LQIP
            lqip_base64 = thumbnail_service.generate_lqip_base64(frame_jpeg, "image/jpeg")

            # Extract video metadata
            video_metadata = video_service.get_video_metadata(video_data)

            # Update Asset record with derivatives
            derivative_keys = {
                "thumbnail_key": thumbnail_key,
                "preview_key": preview_key,
                "lqip_base64": lqip_base64,
            }
            await self._update_asset_derivatives(asset_id, derivative_keys)

            logger.info(
                "Video processing completed",
                asset_id=asset_id,
                duration=video_metadata.get("duration"),
                resolution=f"{video_metadata.get('width')}x{video_metadata.get('height')}",
            )

            # Return processing results
            return {
                "thumbnails_generated": True,
                "thumbnail_key": thumbnail_key,
                "preview_key": preview_key,
                "lqip_generated": True,
                "video_duration": video_metadata.get("duration"),
                "video_width": video_metadata.get("width"),
                "video_height": video_metadata.get("height"),
                "video_codec": video_metadata.get("codec"),
            }

        except Exception as e:
            logger.error("Video processing failed", asset_id=asset_id, error=str(e))
            raise

    async def _download_and_decrypt(
        self, storage_path: str, workspace_id: str, is_encrypted: bool
    ) -> bytes:
        """Download asset from R2 and decrypt if needed."""
        from ..services.storage_service import get_storage_service
        from ..services.encryption_service import get_encryption_service

        storage_service = get_storage_service()

        # Download from R2
        encrypted_data = storage_service.download_object(storage_path)

        if not is_encrypted:
            return encrypted_data

        # Decrypt
        encryption_service = get_encryption_service()

        # TODO: Get IV and parts metadata from Asset record
        # For now, use placeholder IV
        iv_hex = "000000000000000000000000"  # This should come from Asset.parts_metadata

        decrypted_data = encryption_service.decrypt_asset(
            encrypted_data=encrypted_data,
            workspace_id=workspace_id,
            iv_hex=iv_hex,
        )

        return decrypted_data

    async def _generate_thumbnails_full(
        self, asset_id: str, workspace_id: str, image_data: bytes, mime_type: str
    ) -> dict:
        """Generate WebP thumbnails and upload to R2."""
        from ..services.thumbnail_service import get_thumbnail_service
        from ..services.storage_service import get_storage_service

        thumbnail_service = get_thumbnail_service()
        storage_service = get_storage_service()

        logger.debug("Generating thumbnails", asset_id=asset_id)

        # Generate all variants
        thumbnails = thumbnail_service.generate_thumbnails(image_data, mime_type)

        # Upload to R2
        thumbnail_keys = {}

        # Upload thumbnail (300px)
        thumbnail_key = f"workspaces/{workspace_id}/assets/{asset_id}/thumbnail.webp"
        storage_service.upload_object(
            key=thumbnail_key,
            data=thumbnails["thumbnail"],
            content_type="image/webp",
        )
        thumbnail_keys["thumbnail_key"] = thumbnail_key

        # Upload preview (1200px)
        preview_key = f"workspaces/{workspace_id}/assets/{asset_id}/preview.webp"
        storage_service.upload_object(
            key=preview_key,
            data=thumbnails["preview"],
            content_type="image/webp",
        )
        thumbnail_keys["preview_key"] = preview_key

        # Generate LQIP base64
        lqip_base64 = thumbnail_service.generate_lqip_base64(image_data, mime_type)
        thumbnail_keys["lqip_base64"] = lqip_base64

        logger.info("Thumbnails uploaded to R2", asset_id=asset_id)

        return thumbnail_keys

    async def _extract_exif_full(
        self, asset_id: str, image_data: bytes, mime_type: str
    ):
        """Extract EXIF metadata and store in database."""
        from ..services.exif_service import get_exif_service

        logger.debug("Extracting EXIF", asset_id=asset_id)

        try:
            exif_service = get_exif_service()
            metadata = exif_service.extract_exif(image_data, mime_type)

            # Store metadata in database
            async with get_db_session() as db:
                # Check if metadata already exists
                result = await db.execute(
                    select(AssetMetadata).where(AssetMetadata.asset_id == asset_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing record
                    await db.execute(
                        update(AssetMetadata)
                        .where(AssetMetadata.asset_id == asset_id)
                        .values(
                            camera_make=metadata.get("camera_make"),
                            camera_model=metadata.get("camera_model"),
                            lens_model=metadata.get("lens_model"),
                            aperture=Decimal(str(metadata["aperture"])) if metadata.get("aperture") else None,
                            shutter_speed=metadata.get("shutter_speed"),
                            shutter_speed_seconds=Decimal(str(metadata["shutter_speed_seconds"])) if metadata.get("shutter_speed_seconds") else None,
                            iso=metadata.get("iso"),
                            focal_length=Decimal(str(metadata["focal_length"])) if metadata.get("focal_length") else None,
                            focal_length_35mm=Decimal(str(metadata["focal_length_35mm"])) if metadata.get("focal_length_35mm") else None,
                            exposure_compensation=Decimal(str(metadata["exposure_compensation"])) if metadata.get("exposure_compensation") else None,
                            flash_fired=metadata.get("flash_fired"),
                            orientation=metadata.get("orientation"),
                            color_space=metadata.get("color_space"),
                            white_balance=metadata.get("white_balance"),
                            software=metadata.get("software"),
                            gps_latitude=Decimal(str(metadata["gps_latitude"])) if metadata.get("gps_latitude") else None,
                            gps_longitude=Decimal(str(metadata["gps_longitude"])) if metadata.get("gps_longitude") else None,
                            gps_altitude=Decimal(str(metadata["gps_altitude"])) if metadata.get("gps_altitude") else None,
                            captured_at=metadata.get("captured_at"),
                            raw_exif=metadata.get("raw_exif", {}),
                        )
                    )
                else:
                    # Create new record
                    asset_metadata = AssetMetadata(
                        asset_id=asset_id,
                        camera_make=metadata.get("camera_make"),
                        camera_model=metadata.get("camera_model"),
                        lens_model=metadata.get("lens_model"),
                        aperture=Decimal(str(metadata["aperture"])) if metadata.get("aperture") else None,
                        shutter_speed=metadata.get("shutter_speed"),
                        shutter_speed_seconds=Decimal(str(metadata["shutter_speed_seconds"])) if metadata.get("shutter_speed_seconds") else None,
                        iso=metadata.get("iso"),
                        focal_length=Decimal(str(metadata["focal_length"])) if metadata.get("focal_length") else None,
                        focal_length_35mm=Decimal(str(metadata["focal_length_35mm"])) if metadata.get("focal_length_35mm") else None,
                        exposure_compensation=Decimal(str(metadata["exposure_compensation"])) if metadata.get("exposure_compensation") else None,
                        flash_fired=metadata.get("flash_fired"),
                        orientation=metadata.get("orientation"),
                        color_space=metadata.get("color_space"),
                        white_balance=metadata.get("white_balance"),
                        software=metadata.get("software"),
                        gps_latitude=Decimal(str(metadata["gps_latitude"])) if metadata.get("gps_latitude") else None,
                        gps_longitude=Decimal(str(metadata["gps_longitude"])) if metadata.get("gps_longitude") else None,
                        gps_altitude=Decimal(str(metadata["gps_altitude"])) if metadata.get("gps_altitude") else None,
                        captured_at=metadata.get("captured_at"),
                        raw_exif=metadata.get("raw_exif", {}),
                    )
                    db.add(asset_metadata)

                await db.commit()

            logger.info(
                "EXIF metadata stored",
                asset_id=asset_id,
                camera=metadata.get("camera_model"),
                captured_at=metadata.get("captured_at"),
            )

        except Exception as e:
            logger.error("Failed to extract EXIF", asset_id=asset_id, error=str(e))
            # Don't raise - EXIF extraction is not critical

    async def _detect_faces_full(
        self, asset_id: str, workspace_id: str, image_data: bytes
    ):
        """Detect faces using Google Cloud Vision and generate embeddings."""
        from ..services.face_service import get_face_service
        from PIL import Image
        import io

        logger.debug("Detecting faces", asset_id=asset_id)

        try:
            face_service = get_face_service()

            if not face_service.enabled:
                logger.debug("Face detection disabled, skipping")
                return

            # Detect faces
            faces = await face_service.detect_faces(image_data)

            if not faces:
                logger.debug("No faces detected", asset_id=asset_id)
                return

            # Load original image for cropping faces
            original_image = Image.open(io.BytesIO(image_data))
            img_width, img_height = original_image.size

            # Store Face records in database
            async with get_db_session() as db:
                face_ids = []

                for face_data in faces:
                    # Crop face from original image for embedding
                    bbox = face_data["bounding_box"]
                    face_crop = original_image.crop((
                        bbox.get("x_min", 0),
                        bbox.get("y_min", 0),
                        bbox.get("x_max", img_width),
                        bbox.get("y_max", img_height),
                    ))

                    # Encode cropped face to JPEG bytes
                    face_buffer = io.BytesIO()
                    face_crop.save(face_buffer, format="JPEG", quality=90)
                    face_bytes = face_buffer.getvalue()

                    # Generate face embedding
                    embedding = face_service.generate_face_embedding(face_bytes)

                    face = Face(
                        asset_id=asset_id,
                        workspace_id=workspace_id,
                        bounding_box=face_data["bounding_box"],
                        confidence=Decimal(str(face_data["confidence"])),
                        landmarks=face_data.get("landmarks"),
                        attributes=face_data.get("attributes", {}),
                        detection_source="google_vision",
                        embedding=embedding,
                    )
                    db.add(face)
                    face_ids.append(face.id)

                    if embedding:
                        logger.debug("Face embedding generated", face_id=face.id)

                await db.commit()

            # Publish face.detected events
            try:
                from ..services.event_service import get_event_service

                event_service = get_event_service()
                for face_id in face_ids:
                    event_data = {
                        "event_type": "face.detected",
                        "asset_id": asset_id,
                        "workspace_id": workspace_id,
                        "face_id": face_id,
                        "face_count": len(faces),
                    }
                    await event_service.publish_event(
                        topic="face.detected",
                        event=event_data,
                        key=workspace_id,
                    )

                logger.debug("Published face.detected events", count=len(face_ids))

            except Exception as e:
                logger.warning("Failed to publish face.detected events", error=str(e))
                # Don't fail processing if event publishing fails

            logger.info("Faces stored", asset_id=asset_id, face_count=len(faces))

        except Exception as e:
            logger.error("Failed to detect faces", asset_id=asset_id, error=str(e))
            # Don't raise - face detection is optional

    async def _detect_tags_full(self, asset_id: str, image_data: bytes):
        """Detect image tags/labels using Google Cloud Vision."""
        from ..services.tag_service import get_tag_service
        from ..models import AssetTag

        logger.debug("Detecting tags", asset_id=asset_id)

        try:
            tag_service = get_tag_service()

            if not tag_service.enabled:
                logger.debug("Tag detection disabled, skipping")
                return

            # Detect tags
            tags = await tag_service.detect_tags(image_data)

            if not tags:
                logger.debug("No tags detected", asset_id=asset_id)
                return

            # Store AssetTag records in database
            async with get_db_session() as db:
                for tag_data in tags:
                    asset_tag = AssetTag(
                        asset_id=asset_id,
                        tag=tag_data["tag"],
                        confidence=tag_data["confidence"],
                        source="google_vision",
                        mid=tag_data.get("mid"),
                        topicality=tag_data.get("topicality"),
                    )
                    db.add(asset_tag)

                await db.commit()

            logger.info("Tags stored", asset_id=asset_id, tag_count=len(tags))

        except Exception as e:
            logger.error("Failed to detect tags", asset_id=asset_id, error=str(e))
            # Don't raise - tag detection is optional

    async def _update_asset_derivatives(self, asset_id: str, derivative_keys: dict):
        """Update Asset record with derivative keys."""
        try:
            async with get_db_session() as db:
                await db.execute(
                    update(Asset)
                    .where(Asset.id == asset_id)
                    .values(
                        thumbnail_key=derivative_keys.get("thumbnail_key"),
                        preview_key=derivative_keys.get("preview_key"),
                        lqip_base64=derivative_keys.get("lqip_base64"),
                    )
                )
                await db.commit()

            logger.info(
                "Asset derivatives updated",
                asset_id=asset_id,
                thumbnail_key=derivative_keys.get("thumbnail_key"),
                preview_key=derivative_keys.get("preview_key"),
            )

        except Exception as e:
            logger.error(
                "Failed to update asset derivatives",
                asset_id=asset_id,
                error=str(e),
            )
            raise
    async def _create_processing_task(
        self,
        asset_id: str,
        workspace_id: str,
        task_type: TaskType,
        input_data: dict,
        priority: int = 5,
    ) -> ProcessingTask:
        """Create ProcessingTask record in database."""
        async with get_db_session() as db:
            task = ProcessingTask(
                asset_id=asset_id,
                workspace_id=workspace_id,
                task_type=task_type.value,
                status=TaskStatus.PENDING.value,
                priority=priority,
                input_data=input_data,
                kafka_topic="upload.completed",
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            logger.debug(
                "ProcessingTask created",
                task_id=task.id,
                asset_id=asset_id,
                task_type=task_type.value,
            )

            return task

    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        started_at: datetime = None,
        completed_at: datetime = None,
        output_data: dict = None,
        error_message: str = None,
    ):
        """Update ProcessingTask status and metadata."""
        async with get_db_session() as db:
            update_values = {"status": status.value}

            if started_at:
                update_values["started_at"] = started_at
            if completed_at:
                update_values["completed_at"] = completed_at
            if output_data:
                update_values["output_data"] = output_data
            if error_message:
                update_values["error_message"] = error_message

            await db.execute(
                update(ProcessingTask)
                .where(ProcessingTask.id == task_id)
                .values(**update_values)
            )
            await db.commit()

            logger.debug("ProcessingTask updated", task_id=task_id, status=status.value)
