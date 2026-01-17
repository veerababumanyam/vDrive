# Feature Specification: Storage & Media Processing

**Feature Branch**: `005-upload-media-processing`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "Phase 3: Storage & Media Processing - Upload Service with TUS protocol resumable uploads, chunked file handling, AES-256 encryption, Kafka events, Google Cloud Vision face detection, metadata extraction, WebP thumbnail generation, and Celery Workers for background task processing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resumable Large File Upload (Priority: P1)

A photographer uploads a high-resolution wedding photo album (50 RAW files, 2GB total) over an unstable mobile connection. When the connection drops at 60% progress, the upload automatically resumes from where it left off without re-uploading completed chunks. The photographer sees real-time progress and receives confirmation when all files are processed and ready in the gallery.

**Why this priority**: Resumable uploads are critical for professional photographers working with large files in field conditions. Without this, failed uploads result in wasted bandwidth, time, and frustrated users. This is the core value proposition of the Upload Service.

**Independent Test**: Can be fully tested by initiating a 500MB upload, simulating network interruption at 50%, reconnecting, and verifying the upload resumes and completes successfully. Delivers immediate value for photographers uploading from events.

**Acceptance Scenarios**:

1. **Given** a photographer initiates a 1GB file upload, **When** the connection drops at 40% completion, **Then** the system preserves upload state and resumes from byte 419,430,400 when reconnected
2. **Given** a TUS-compliant upload client, **When** the photographer starts an upload, **Then** the system returns an upload URL that remains valid for 24 hours
3. **Given** a multi-file upload batch of 100 photos, **When** the photographer uploads concurrently, **Then** the system handles up to 10 parallel chunk uploads per session
4. **Given** an upload in progress, **When** the photographer views progress, **Then** they see real-time byte-level progress updates via WebSocket or polling
5. **Given** upload chunks arrive out of order, **When** all chunks are received, **Then** the system assembles the complete file correctly

---

### User Story 2 - Secure File Encryption and Storage (Priority: P1)

A photographer uploads client photos that must be protected at rest. Each file is encrypted with AES-256 before storage in Cloudflare R2. The encryption key is derived from the workspace context, ensuring files are only decryptable by authorized workspace members. Original files are stored encrypted; WebP thumbnails are also encrypted for consistent security.

**Why this priority**: Data security is non-negotiable for a professional photography platform handling personal images. Encryption at rest protects against data breaches and meets enterprise compliance requirements. This must work correctly before any file is stored.

**Independent Test**: Can be tested by uploading a file, verifying the stored object in R2 is encrypted (not viewable without decryption), and confirming the gallery service can decrypt and serve the image via signed URLs. Delivers compliance value immediately.

**Acceptance Scenarios**:

1. **Given** a file upload completes, **When** the system stores the file in R2, **Then** the file is encrypted with AES-256-GCM using a workspace-derived key
2. **Given** an encrypted file in R2, **When** an unauthorized party accesses the bucket directly, **Then** they see only encrypted binary data, not the original image
3. **Given** gallery service requests an asset, **When** generating a signed URL, **Then** the decryption key context is included for authorized decryption
4. **Given** a workspace is deleted, **When** cleanup runs, **Then** all associated encrypted files become permanently inaccessible
5. **Given** encryption key rotation is triggered, **When** the process completes, **Then** existing files can still be decrypted with both old and new keys during transition

---

### User Story 3 - Automatic Thumbnail and WebP Generation (Priority: P1)

When a photographer uploads a high-resolution JPEG or RAW file, the system automatically generates three derivative images: a WebP thumbnail (300px), a WebP preview (1200px), and a Low Quality Image Placeholder (LQIP, 20px base64). These derivatives are encrypted and stored alongside the original, enabling fast gallery loading with blur-up effects.

**Why this priority**: Thumbnail generation is essential for gallery performance. Without optimized derivatives, galleries would load slowly and consume excessive bandwidth. This directly impacts the P1 user stories in the Gallery Service spec.

**Independent Test**: Can be tested by uploading a 20MB RAW file, waiting for processing (< 30 seconds), and verifying three derivative URLs are available with correct dimensions and WebP format. Delivers performance value for all gallery viewers.

**Acceptance Scenarios**:

1. **Given** a 50MP JPEG upload completes, **When** processing finishes, **Then** the system generates WebP thumbnail (300px longest edge), preview (1200px), and LQIP (20px)
2. **Given** processing creates WebP derivatives, **When** comparing file sizes, **Then** WebP files are at least 25% smaller than equivalent JPEG quality
3. **Given** an RAW file (CR2, NEF, ARW) is uploaded, **When** processing completes, **Then** the system extracts the embedded JPEG preview for derivative generation
4. **Given** a video file (MP4, MOV) is uploaded, **When** processing completes, **Then** the system generates a thumbnail from the first frame and a preview from a representative frame
5. **Given** processing queue has 500 pending items, **When** KEDA scaling triggers, **Then** Celery workers scale up to process the backlog within acceptable timeframes

---

### User Story 4 - Metadata Extraction and Indexing (Priority: P2)

A photographer uploads event photos, and the system automatically extracts EXIF metadata including camera model, lens, aperture, shutter speed, ISO, GPS coordinates, and capture timestamp. This metadata is indexed in the vector database for intelligent search and stored in PostgreSQL for display in photo details.

**Why this priority**: Metadata enrichment enables smart features like searching by camera settings, timeline views, and location mapping. While not blocking core functionality, this significantly enhances the platform's professional value proposition.

**Independent Test**: Can be tested by uploading a photo with complete EXIF data, querying the database for extracted metadata, and verifying all standard EXIF fields are correctly parsed and stored. Delivers search and organization value.

**Acceptance Scenarios**:

1. **Given** a JPEG with EXIF data is uploaded, **When** processing completes, **Then** the system extracts and stores camera make/model, lens, aperture, shutter speed, ISO, and timestamp
2. **Given** GPS coordinates in EXIF, **When** metadata is extracted, **Then** the system stores latitude/longitude and optionally reverse-geocodes to location name
3. **Given** extracted metadata, **When** stored in vector database, **Then** the metadata enables semantic search queries like "photos taken with 85mm lens"
4. **Given** a file without EXIF data, **When** processing completes, **Then** the system gracefully handles missing metadata and uses file creation date as fallback
5. **Given** sensitive EXIF data (GPS), **When** the gallery privacy settings require it, **Then** the system can strip location data from public-facing metadata

---

### User Story 5 - AI Face Detection and Recognition (Priority: P2)

When photos are uploaded, the system automatically detects faces using Google Cloud Vision API. Detected faces are stored with bounding box coordinates, confidence scores, and face embeddings. This enables features like "find all photos of person X" and automatic face grouping for client delivery.

**Why this priority**: Face detection enables powerful professional features like automatic guest identification at weddings. While enhancing the platform significantly, core upload and gallery functionality works without it.

**Independent Test**: Can be tested by uploading a group photo, verifying face detection returns bounding boxes for each face, and confirming face embeddings are stored for future matching. Delivers AI-powered organization value.

**Acceptance Scenarios**:

1. **Given** a photo with 5 visible faces is uploaded, **When** AI processing completes, **Then** the system detects all 5 faces with bounding box coordinates and confidence scores
2. **Given** detected faces, **When** embeddings are generated, **Then** faces can be matched across photos with 95%+ accuracy for frontal faces
3. **Given** a gallery with face detection enabled, **When** a client searches for "photos with me", **Then** they can identify themselves and find all matching photos
4. **Given** Google Cloud Vision API rate limits, **When** limits are approached, **Then** the system queues requests and processes within quota constraints
5. **Given** privacy regulations apply, **When** face detection is disabled per workspace, **Then** no face data is collected or stored for that workspace

---

### User Story 6 - Event-Driven Processing Pipeline (Priority: P1)

The upload service publishes Kafka events at key processing stages: `upload.initiated` when upload begins, `upload.completed` when chunks are assembled, and downstream services consume `asset.processing` and `asset.processed` events. This decoupled architecture enables reliable, scalable processing with exactly-once semantics.

**Why this priority**: The event-driven architecture is fundamental to system reliability and scalability. Without proper event publishing, downstream services (Gallery, Notifications) cannot react to uploads, breaking the end-to-end workflow.

**Independent Test**: Can be tested by uploading a file, consuming events from Kafka topics, and verifying the correct sequence of events with proper payloads and timing. Delivers system integration value.

**Acceptance Scenarios**:

1. **Given** a file upload begins, **When** the TUS POST request is received, **Then** the system publishes `upload.initiated` event with upload_id, workspace_id, filename, and expected_size
2. **Given** all chunks are received, **When** file assembly completes, **Then** the system publishes `upload.completed` event with asset_id, final_size, checksum, and storage_path
3. **Given** thumbnail generation completes, **When** all derivatives are stored, **Then** the system publishes `asset.processed` event with derivative URLs
4. **Given** Kafka broker is temporarily unavailable, **When** event publishing fails, **Then** the system retries with exponential backoff and stores events in dead-letter queue after max retries
5. **Given** duplicate events due to retry, **When** consumers process events, **Then** idempotency ensures assets are not processed multiple times

---

### User Story 7 - Background Task Processing with Celery (Priority: P1)

Resource-intensive operations (thumbnail generation, face detection, email delivery) are processed asynchronously by Celery workers. Different worker pools handle different task types: general workers for thumbnails, AI workers for face detection with GPU access, and beat scheduler for recurring cleanup jobs.

**Why this priority**: Asynchronous processing is essential for system responsiveness. Synchronous processing of heavy tasks would block uploads and degrade user experience. Celery provides the reliable task queue infrastructure.

**Independent Test**: Can be tested by submitting tasks to Celery queues, verifying workers process them correctly, and monitoring task completion via Flower dashboard. Delivers reliability and scalability value.

**Acceptance Scenarios**:

1. **Given** an upload completes, **When** thumbnail generation is triggered, **Then** a Celery task is queued and processed by general workers within 30 seconds
2. **Given** face detection is enabled, **When** AI processing is triggered, **Then** a Celery task is routed to AI workers with appropriate resource allocation
3. **Given** Celery beat scheduler is running, **When** scheduled cleanup time arrives, **Then** orphaned uploads older than 24 hours are automatically deleted
4. **Given** a Celery task fails, **When** retry logic triggers, **Then** the task is retried up to 3 times with exponential backoff before moving to dead-letter queue
5. **Given** high task queue depth (>1000 pending), **When** KEDA monitors Redis queue length, **Then** Celery workers scale up to process backlog efficiently

---

### Edge Cases

- What happens when an upload is abandoned before completion? (Cleanup after 24 hours via Celery beat)
- How does the system handle corrupted/truncated chunks? (Checksum validation per chunk, reject and request re-upload)
- What if encryption key derivation fails? (Fail upload with clear error, do not store unencrypted data)
- How does the system handle unsupported file formats? (Validate MIME type on first chunk, reject early with supported formats list)
- What if Google Cloud Vision API is unavailable? (Queue for retry, proceed with upload without face detection, backfill later)
- How are very large files (>10GB) handled? (Chunk size optimization, streaming processing, extended upload URL TTL)
- What if thumbnail generation produces corrupt output? (Retry with fallback parameters, store original-only if all attempts fail)

## Requirements *(mandatory)*

### Functional Requirements

**Upload Service (Port 8008)**

- **FR-001**: System MUST implement TUS v1.0.0 protocol for resumable uploads with HEAD, PATCH, POST, and DELETE methods
- **FR-002**: System MUST support chunked uploads with configurable chunk size (default 5MB, max 100MB)
- **FR-003**: System MUST validate file MIME type against allowlist (JPEG, PNG, WebP, HEIC, RAW formats, MP4, MOV, AVI)
- **FR-004**: System MUST encrypt all stored files using AES-256-GCM with workspace-derived keys
- **FR-005**: System MUST generate upload URLs with configurable TTL (default 24 hours)
- **FR-006**: System MUST publish `upload.initiated` and `upload.completed` events to Kafka
- **FR-007**: System MUST store uploaded files in Cloudflare R2 with structured object keys: `workspaces/{workspace_id}/assets/{asset_id}/{variant}.{ext}`
- **FR-008**: System MUST track upload progress and expose it via REST endpoint for client polling
- **FR-009**: System MUST support concurrent uploads (up to 10 parallel per workspace by default)
- **FR-010**: System MUST validate checksum (SHA-256) of assembled file against client-provided hash

**Media Processing**

- **FR-011**: System MUST generate WebP thumbnails at 300px longest edge with 80% quality
- **FR-012**: System MUST generate WebP preview images at 1200px longest edge with 85% quality
- **FR-013**: System MUST generate LQIP (Low Quality Image Placeholder) at 20px as base64-encoded WebP
- **FR-014**: System MUST extract EXIF metadata from supported image formats and store in PostgreSQL
- **FR-015**: System MUST support RAW format processing (CR2, NEF, ARW, DNG) via embedded preview extraction
- **FR-016**: System MUST generate video thumbnails from first frame and preview from representative frame
- **FR-017**: System MUST index extracted metadata in vector database for semantic search capabilities

**Face Detection**

- **FR-018**: System MUST integrate with Google Cloud Vision API for face detection
- **FR-019**: System MUST store face bounding boxes, confidence scores, and embeddings per detected face
- **FR-020**: System MUST respect workspace-level face detection enable/disable setting
- **FR-021**: System MUST handle API rate limits gracefully with queuing and backoff

**Celery Workers**

- **FR-022**: System MUST deploy three worker types: general, AI, and beat scheduler
- **FR-023**: General workers MUST process thumbnail generation, email delivery, and notifications
- **FR-024**: AI workers MUST process face detection, smart curation, and quality scoring tasks
- **FR-025**: Beat scheduler MUST execute cleanup jobs for orphaned uploads (>24 hours)
- **FR-026**: System MUST use Redis as Celery broker with task result backend
- **FR-027**: System MUST implement task retry with exponential backoff (max 3 retries)
- **FR-028**: System MUST expose worker metrics for Prometheus monitoring

**Event Integration**

- **FR-029**: System MUST consume no events (producer-only for upload service)
- **FR-030**: Celery workers MUST consume `upload.completed` events to trigger thumbnail generation
- **FR-031**: Celery workers MUST consume `asset.processing` events to trigger AI analysis
- **FR-032**: System MUST produce `asset.processed` event when all processing completes

### Key Entities

- **Upload**: Represents an in-progress or completed upload session (id, workspace_id, filename, expected_size, received_bytes, status, upload_url, expires_at, checksum)
- **Asset**: Represents a fully processed file (id, workspace_id, original_key, thumbnail_key, preview_key, lqip_base64, encryption_key_id, mime_type, file_size, metadata)
- **AssetMetadata**: Extracted EXIF and file metadata (camera_make, camera_model, lens, aperture, shutter_speed, iso, gps_lat, gps_lon, captured_at, dimensions)
- **Face**: Detected face in an asset (id, asset_id, bounding_box, confidence, embedding_vector, cluster_id)
- **ProcessingTask**: Celery task tracking (task_id, asset_id, task_type, status, started_at, completed_at, error_message, retry_count)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Photographers can resume interrupted uploads and complete them successfully 99% of the time
- **SC-002**: Large file uploads (>1GB) complete within 5 minutes on standard broadband connections
- **SC-003**: System processes 95% of uploaded photos (thumbnail + metadata extraction) within 30 seconds of upload completion
- **SC-004**: Face detection completes for 95% of photos within 60 seconds when enabled
- **SC-005**: System handles 1,000 concurrent uploads across all workspaces without degradation
- **SC-006**: Encrypted files in storage cannot be viewed without proper decryption authorization
- **SC-007**: WebP thumbnails reduce bandwidth by at least 25% compared to equivalent JPEG quality
- **SC-008**: LQIP placeholders enable perceived instant loading (blur appears within 50ms)
- **SC-009**: System maintains 99.9% uptime for upload endpoints during peak usage
- **SC-010**: Task queue backlog (>1000 tasks) is cleared within 10 minutes through auto-scaling
- **SC-011**: All Kafka events are delivered with at-least-once semantics and properly sequenced

## Assumptions

- Cloudflare R2 is the primary object storage and provides S3-compatible API access
- Google Cloud Vision API is available and the organization has appropriate API quotas
- Workspace encryption keys are managed by a separate key management system (assumed existing)
- The vector database (pgvector) is configured and available for metadata indexing
- Redis is deployed and accessible for Celery broker and caching
- Kafka cluster is operational with pre-created topics (upload.initiated, upload.completed, asset.processing, asset.processed)
- Gallery service is responsible for decryption and serving assets via signed URLs (integration point)
- Maximum single file size is 10GB; larger files require alternative workflows
- KEDA is configured in the Kubernetes cluster for auto-scaling based on queue depth
