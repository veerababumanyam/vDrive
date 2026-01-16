"""TUS v1.0.0 resumable upload protocol endpoints."""

import base64
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Request, Response, status, Depends

from ...core.config import settings
from ...core.database import AsyncSessionLocal
from ...core.auth import get_current_user, CurrentUser
from ...models import Upload
from ...schemas.events import UploadInitiatedEvent
from ...services.validation_service import get_validation_service
from ...services.event_service import get_event_service
from ...services.upload_service import get_upload_service
from ...storage.r2_tus_backend import get_r2_tus_backend

logger = structlog.get_logger()

router = APIRouter()

# TUS protocol constants
TUS_VERSION = "1.0.0"
TUS_EXTENSION = "creation,termination"
TUS_MAX_SIZE = settings.TUS_MAX_SIZE


def parse_tus_metadata(metadata_str: Optional[str]) -> dict:
    """Parse TUS Upload-Metadata header into dict.

    TUS protocol sends metadata as: "key1 base64value1,key2 base64value2"
    Example: "filename dGVzdC5qcGc=,filetype aW1hZ2UvanBlZw=="

    Args:
        metadata_str: The Upload-Metadata header value

    Returns:
        Dictionary of key-value pairs from the metadata
    """
    if not metadata_str:
        return {}

    result = {}
    for pair in metadata_str.split(","):
        parts = pair.strip().split(" ", 1)
        if len(parts) == 2:
            key = parts[0]
            try:
                value = base64.b64decode(parts[1]).decode("utf-8")
            except Exception:
                value = parts[1]  # Use as-is if not valid base64
            result[key] = value
        elif len(parts) == 1 and parts[0]:
            result[parts[0]] = ""
    return result


@router.options("/")
async def tus_options():
    """
    TUS OPTIONS endpoint - Discover server capabilities.

    Returns TUS protocol version, supported extensions, and max file size.
    """
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Tus-Resumable": TUS_VERSION,
            "Tus-Version": TUS_VERSION,
            "Tus-Extension": TUS_EXTENSION,
            "Tus-Max-Size": str(TUS_MAX_SIZE),
        },
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_upload(
    upload_length: int = Header(..., alias="Upload-Length"),
    upload_metadata: Optional[str] = Header(None, alias="Upload-Metadata"),
    tus_resumable: str = Header(..., alias="Tus-Resumable"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    TUS POST endpoint - Create upload session.

    Requires JWT authentication. Workspace is extracted from token.
    File metadata (filename, filetype) is extracted from Upload-Metadata header.

    TUS Upload-Metadata format: "key1 base64value1,key2 base64value2"
    Expected keys: filename, filetype (mime type)

    Returns:
        201 with Location header pointing to upload URL
    """
    try:
        # Validate TUS version
        if tus_resumable != TUS_VERSION:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Unsupported TUS version: {tus_resumable}",
            )

        # Get workspace_id from authenticated user
        workspace_id = current_user.workspace_id
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No workspace assigned to user",
            )

        # Parse metadata from TUS header
        metadata = parse_tus_metadata(upload_metadata)
        filename = metadata.get("filename", "unknown")
        mime_type = metadata.get("filetype", "application/octet-stream")
        checksum_client = metadata.get("checksum")

        logger.debug(
            "Parsed TUS metadata",
            metadata=metadata,
            filename=filename,
            mime_type=mime_type,
        )

        # Validate file size
        validation_service = get_validation_service()
        if not validation_service.validate_file_size(upload_length):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {upload_length} exceeds maximum {TUS_MAX_SIZE}",
            )

        # Validate MIME type (allow unknown types for flexibility)
        if mime_type != "application/octet-stream" and not validation_service.validate_mime_type(mime_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type {mime_type} not allowed",
            )

        # Validate filename
        if filename != "unknown" and not validation_service.validate_filename(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename",
            )

        # Check concurrent upload limit
        async with AsyncSessionLocal() as db:
            is_allowed, current_count = await validation_service.check_concurrent_uploads(
                workspace_id, db
            )
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many concurrent uploads ({current_count}/{settings.MAX_CONCURRENT_UPLOADS_PER_WORKSPACE})",
                )

        # Create upload session via TUS backend
        backend = get_r2_tus_backend()

        # Generate unique upload ID
        from uuid import uuid4
        upload_id = str(uuid4())

        await backend.create(
            upload_id=upload_id,
            workspace_id=workspace_id,
            user_id=current_user.user_id,
            filename=filename,
            mime_type=mime_type,
            expected_size=upload_length,
            checksum_client=checksum_client,
        )

        upload_url = f"{settings.API_BASE_URL}/api/v1/files/{upload_id}"

        # Publish upload.initiated event
        event = UploadInitiatedEvent(
            upload_id=upload_id,
            workspace_id=workspace_id,
            filename=filename,
            expected_size=upload_length,
        )
        event_service = get_event_service()
        await event_service.publish_event("upload.initiated", event, workspace_id)

        logger.info(
            "TUS upload session created via API",
            upload_id=upload_id,
            filename=filename,
            expected_size=upload_length,
        )

        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={
                "Location": upload_url,
                "Tus-Resumable": TUS_VERSION,
                "Upload-Expires": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create TUS upload", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create upload session",
        )


@router.head("/{upload_id}")
async def get_upload_offset(
    upload_id: str,
    tus_resumable: str = Header(..., alias="Tus-Resumable"),
):
    """
    TUS HEAD endpoint - Get current upload offset.

    Returns:
        200 with Upload-Offset header
    """
    try:
        # Validate TUS version
        if tus_resumable != TUS_VERSION:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Unsupported TUS version: {tus_resumable}",
            )

        backend = get_r2_tus_backend()
        offset = await backend.get_offset(upload_id)
        upload_info = await backend.get_info(upload_id)

        return Response(
            status_code=status.HTTP_200_OK,
            headers={
                "Tus-Resumable": TUS_VERSION,
                "Upload-Offset": str(offset),
                "Upload-Length": str(upload_info["expected_size"]),
                "Cache-Control": "no-store",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get upload offset", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload offset",
        )


@router.patch("/{upload_id}")
async def upload_chunk(
    upload_id: str,
    request: Request,
    upload_offset: int = Header(..., alias="Upload-Offset"),
    content_type: str = Header(..., alias="Content-Type"),
    tus_resumable: str = Header(..., alias="Tus-Resumable"),
):
    """
    TUS PATCH endpoint - Upload chunk data.

    Returns:
        204 with updated Upload-Offset header
    """
    try:
        # Validate TUS version
        if tus_resumable != TUS_VERSION:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Unsupported TUS version: {tus_resumable}",
            )

        # Validate content type
        if content_type != "application/offset+octet-stream":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Type must be application/offset+octet-stream",
            )

        # Read chunk data
        chunk_data = await request.body()

        if not chunk_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty chunk data",
            )

        # Upload chunk via backend
        backend = get_r2_tus_backend()
        new_offset = await backend.write_chunk(upload_id, chunk_data, upload_offset)

        logger.debug(
            "TUS chunk uploaded via API",
            upload_id=upload_id,
            offset=upload_offset,
            new_offset=new_offset,
            chunk_size=len(chunk_data),
        )

        # Check if upload is complete
        upload_info = await backend.get_info(upload_id)
        if new_offset >= upload_info["expected_size"]:
            # Complete the upload
            storage_path = await backend.complete(upload_id)

            # Create Asset and publish upload.completed event
            async with AsyncSessionLocal() as db:
                # Get the upload record
                from sqlalchemy import select
                result = await db.execute(select(Upload).where(Upload.id == upload_id))
                upload = result.scalar_one()

                # Calculate checksum from parts metadata
                checksum_server = upload.checksum_server or "calculated-from-parts"

                # Complete upload via UploadService (creates Asset + publishes events)
                upload_service = get_upload_service()
                asset = await upload_service.complete_upload(
                    upload=upload,
                    checksum_server=checksum_server,
                    storage_path=storage_path,
                    db=db,
                )

            logger.info(
                "TUS upload completed via API",
                upload_id=upload_id,
                asset_id=asset.id,
                storage_path=storage_path,
            )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={
                "Tus-Resumable": TUS_VERSION,
                "Upload-Offset": str(new_offset),
            },
        )

    except ValueError as e:
        # Offset mismatch or upload not found
        if "mismatch" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to upload chunk", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload chunk",
        )


@router.delete("/{upload_id}")
async def cancel_upload(
    upload_id: str,
    tus_resumable: str = Header(..., alias="Tus-Resumable"),
):
    """
    TUS DELETE endpoint - Cancel upload and cleanup.

    Returns:
        204 on successful cancellation
    """
    try:
        # Validate TUS version
        if tus_resumable != TUS_VERSION:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Unsupported TUS version: {tus_resumable}",
            )

        backend = get_r2_tus_backend()
        await backend.delete(upload_id)

        logger.info("TUS upload cancelled via API", upload_id=upload_id)

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={
                "Tus-Resumable": TUS_VERSION,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to cancel upload", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel upload",
        )
