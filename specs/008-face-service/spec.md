# Feature Specification: Face Service

**Feature Branch**: `008-face-service`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "Face Service: Google Cloud Vision face detection, ArcFace 512-dimension embeddings, Find Me feature, People group management, with Google ADK (A2A Protocol) future integration"

## Overview

The Face Service is a microservice responsible for automatic face detection, recognition, and organization within the RawDrive photography platform. It enables photographers to automatically identify and group faces across their photo collections, and allows clients to find photos of themselves using a selfie ("Find Me" feature).

**Service Configuration**:

| Attribute         | Value                                    |
|-------------------|------------------------------------------|
| Port              | 8002                                     |
| Dependencies      | Backend API, Celery Workers, Kafka       |
| KEDA Scaler       | Kafka (face.detected lag) + Prometheus   |
| Min/Max Replicas  | 2 / 50                                   |
| Cooldown          | 120s (AI workloads)                      |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Face Detection on Upload (Priority: P1)

As a photographer, when I upload photos to a gallery, the system should automatically detect all faces in each image so that I don't have to manually identify faces.

**Why this priority**: This is the foundational capability that enables all other face-related features. Without automatic detection, photographers would need to manually identify every face, making the feature unusable at scale.

**Independent Test**: Upload a photo containing multiple faces and verify the system detects them within 30 seconds, displaying bounding boxes and confidence scores.

**Acceptance Scenarios**:

1. **Given** a photographer uploads a photo with 3 visible faces, **When** the upload completes, **Then** the system detects all 3 faces within 30 seconds with at least 70% confidence each.

2. **Given** a photographer uploads a photo with no faces, **When** processing completes, **Then** the system marks the asset as processed with zero faces detected.

3. **Given** the Google Cloud Vision API is temporarily unavailable, **When** a photo is uploaded, **Then** the system queues the photo for retry and notifies the user of delayed processing.

4. **Given** a photo has already been processed for faces, **When** it is re-uploaded or duplicated, **Then** the system skips re-processing (idempotent operation).

---

### User Story 2 - Automatic Face Grouping (Clustering) (Priority: P1)

As a photographer, I want the system to automatically group similar faces together so that I can easily view all photos of the same person.

**Why this priority**: Face grouping transforms raw detections into actionable "person" entities. Without this, photographers would see hundreds of individual faces rather than organized people.

**Independent Test**: Upload 5 photos of the same person and verify they are automatically grouped into a single "person" within 60 seconds.

**Acceptance Scenarios**:

1. **Given** multiple photos containing the same person's face are uploaded, **When** face clustering runs, **Then** those faces are grouped under a single person identifier.

2. **Given** a new photo is uploaded with a face matching an existing group, **When** processing completes, **Then** the face is assigned to the existing group (incremental clustering).

3. **Given** a new photo is uploaded with a completely new face, **When** processing completes, **Then** a new person group is created for that face.

4. **Given** the similarity threshold between two faces is borderline (near 0.5 cosine distance), **When** clustering runs, **Then** the system errs toward separate groups to avoid false merges.

---

### User Story 3 - People Management (View & Organize) (Priority: P2)

As a photographer, I want to view all detected people in my workspace, name them, and manually correct grouping mistakes so that I can accurately organize my photo collection.

**Why this priority**: Automatic clustering isn't perfect. Manual correction capabilities enable photographers to fix errors and add meaningful names to anonymous person groups.

**Independent Test**: View the people list, rename a person to "John Smith", and verify the name persists across page reloads.

**Acceptance Scenarios**:

1. **Given** a photographer has detected faces across multiple photos, **When** they view the People page, **Then** they see a list of person groups with representative photos, sorted by face count.

2. **Given** a person group has no assigned name, **When** displayed, **Then** the system shows a placeholder like "Person #abc123".

3. **Given** a photographer renames a person to "John Smith", **When** viewing any photo with that person, **Then** the name "John Smith" appears.

4. **Given** two person groups actually represent the same person, **When** the photographer merges them, **Then** all faces from both groups combine into one group.

5. **Given** a person group incorrectly contains a face from a different person, **When** the photographer splits that face, **Then** a new person group is created containing only that face.

---

### User Story 4 - Find Me (Client Selfie Search) (Priority: P2)

As a gallery client (event attendee), I want to upload a selfie and instantly find all photos of myself so that I can quickly download my photos from large events.

**Why this priority**: This feature directly improves client experience and differentiates RawDrive from competitors. It enables clients to find their photos in galleries with thousands of images.

**Independent Test**: Upload a selfie and verify the system returns matching photos within 5 seconds, sorted by similarity score.

**Acceptance Scenarios**:

1. **Given** a client uploads a clear selfie, **When** the Find Me search runs, **Then** matching photos are returned within 5 seconds with similarity scores above 60%.

2. **Given** a client uploads a selfie with no matches in the gallery, **When** the search completes, **Then** the system shows a friendly "No matches found" message with suggestions.

3. **Given** a client uploads an image without a detectable face, **When** validation runs, **Then** the system rejects the upload with a clear error message.

4. **Given** a client's selfie matches faces in 50+ photos, **When** results are displayed, **Then** they are paginated with the highest similarity matches first.

5. **Given** Find Me is disabled for a specific gallery by the photographer, **When** a client attempts to use it, **Then** the feature is hidden or shows an appropriate message.

---

### User Story 5 - Person Photo Browser (Priority: P3)

As a photographer, I want to click on a person and see all photos containing that person so that I can quickly curate photos for delivery or albums.

**Why this priority**: Builds on grouping functionality to provide practical navigation. Essential for efficient workflow but depends on accurate grouping first.

**Independent Test**: Select a person from the People page and verify all their photos are displayed with correct counts.

**Acceptance Scenarios**:

1. **Given** a person group contains faces from 25 photos, **When** the photographer views that person's photos, **Then** all 25 photos are displayed with pagination.

2. **Given** a photographer is viewing a person's photos, **When** they select multiple photos, **Then** they can add them to a gallery, album, or download in bulk.

---

### User Story 6 - Processing Status & Notifications (Priority: P3)

As a photographer, I want to see the face processing status for my uploads and be notified when processing is complete so that I know when faces are ready to browse.

**Why this priority**: Processing can take time for large batches. Status visibility prevents confusion and enables photographers to plan their workflow.

**Independent Test**: Upload 10 photos and verify a progress indicator shows processing status, with a notification when complete.

**Acceptance Scenarios**:

1. **Given** a photographer uploads 100 photos, **When** face processing begins, **Then** a progress indicator shows "Processing faces: 45/100".

2. **Given** all faces in a batch are processed, **When** complete, **Then** the photographer receives a notification "Face detection complete: 127 faces found in 100 photos".

3. **Given** some photos fail face processing, **When** viewing status, **Then** the photographer sees which photos failed with retry options.

---

### Edge Cases

- **Obscured faces**: Partially visible faces (profile, covered) are detected with lower confidence and may not cluster correctly.
- **Extreme lighting**: Very dark or overexposed photos may fail face detection entirely.
- **Duplicate uploads**: Same photo uploaded twice should not create duplicate faces (idempotency).
- **Large face counts**: Photos with 50+ faces (crowds) should still process but may be slower.
- **Very small faces**: Faces smaller than 5% of image area may not be detected reliably.
- **Sunglasses/masks**: Faces with occlusions have reduced embedding quality and may not match correctly.
- **Aging/appearance changes**: Same person at different ages or with significant appearance changes may create separate groups.
- **API rate limits**: Google Cloud Vision rate limiting triggers graceful degradation with retry queue.

## Requirements *(mandatory)*

### Functional Requirements

#### Face Detection
- **FR-001**: System MUST automatically detect faces in all uploaded images using Google Cloud Vision API.
- **FR-002**: System MUST extract bounding box coordinates (normalized 0-1 range) for each detected face.
- **FR-003**: System MUST record confidence scores for each detection, filtering out detections below 70% confidence by default.
- **FR-004**: System MUST extract facial landmarks (eyes, nose, mouth) when available.
- **FR-005**: System MUST process face detection asynchronously via Kafka events to avoid blocking uploads.

#### Face Embeddings
- **FR-006**: System MUST generate 512-dimensional face embeddings using DeepFace with ArcFace backbone.
- **FR-007**: System MUST normalize embeddings to unit vectors for cosine similarity calculations.
- **FR-008**: System MUST store embeddings using PostgreSQL pgvector extension for efficient similarity search.
- **FR-009**: System MUST use IVFFlat indexing for approximate nearest neighbor queries.

#### Face Clustering
- **FR-010**: System MUST automatically cluster similar faces into person groups using DBSCAN algorithm.
- **FR-011**: System MUST support incremental clustering when new faces are added (assign to existing groups or create new ones).
- **FR-012**: System MUST calculate and store a representative face for each person group (closest to cluster centroid).
- **FR-013**: System MUST allow manual merging of two or more person groups.
- **FR-014**: System MUST allow manual splitting of faces from a person group into a new group.

#### People Management
- **FR-015**: System MUST allow photographers to view all person groups in their workspace.
- **FR-016**: System MUST display person groups with their representative face and face count.
- **FR-017**: System MUST allow photographers to assign names to person groups.
- **FR-018**: System MUST show unnamed groups with a generated placeholder identifier.
- **FR-019**: System MUST allow filtering/searching people by name.

#### Find Me Feature
- **FR-020**: System MUST accept a selfie upload (max 5MB) and detect the face within it.
- **FR-021**: System MUST search for similar faces across the specified gallery/workspace.
- **FR-022**: System MUST return matches ranked by similarity score (cosine similarity).
- **FR-023**: System MUST filter matches below a configurable threshold (default 60% similarity).
- **FR-024**: System MUST allow photographers to enable/disable Find Me per gallery.
- **FR-025**: System MUST complete Find Me searches within 5 seconds for galleries up to 10,000 photos.

#### Multi-Tenancy & Security
- **FR-026**: System MUST isolate all face data by workspace_id (strict multi-tenancy).
- **FR-027**: System MUST validate JWT tokens for all photographer-facing endpoints.
- **FR-028**: Find Me endpoint MUST validate gallery access permissions before returning results.
- **FR-029**: System MUST NOT expose face data from one workspace to another.

#### Event Processing
- **FR-030**: System MUST consume `asset.processed` events from Kafka to trigger face detection.
- **FR-031**: System MUST publish `face.detected` events after processing each asset.
- **FR-032**: System MUST implement idempotent processing (Redis-based, 24-hour expiry).

#### Resilience
- **FR-033**: System MUST implement circuit breaker for Google Cloud Vision API calls.
- **FR-034**: System MUST queue failed processing attempts for automatic retry.
- **FR-035**: System MUST gracefully degrade when Redis is unavailable (non-blocking).

### Key Entities

- **Face**: Individual detected face with bounding box, confidence, landmarks, and reference to embedding and person group. Always scoped to workspace and linked to source asset.

- **FaceGroup (Person)**: Collection of faces identified as the same person. Contains optional user-assigned name, representative face ID, and denormalized face count. Supports merge and split operations.

- **FaceEmbedding**: 512-dimensional vector representation of a face, stored with pgvector for efficient similarity search. One-to-one relationship with Face.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Face detection completes within 30 seconds per image for 95% of uploads.
- **SC-002**: Find Me searches return results within 5 seconds for galleries up to 10,000 photos.
- **SC-003**: Face clustering achieves 90%+ accuracy when grouping faces of the same person (based on manual verification sample).
- **SC-004**: System handles concurrent processing of 1,000 images without degradation.
- **SC-005**: False merge rate (different people grouped together) stays below 5%.
- **SC-006**: Find Me match accuracy achieves 85%+ precision (correct matches / total matches returned).
- **SC-007**: Photographers can locate and view all photos of a specific person within 3 clicks from any gallery view.
- **SC-008**: System maintains 99.9% uptime for face detection pipeline (excluding external API outages).
- **SC-009**: Processing status updates display within 2 seconds of actual progress changes.
- **SC-010**: Memory usage stays below 2GB per service replica during normal operation.

## Assumptions

1. Google Cloud Vision API credentials are configured and have sufficient quota for expected volume.
2. PostgreSQL has the pgvector extension installed and configured.
3. Redis is available for idempotency tracking but the system degrades gracefully without it.
4. Kafka cluster is operational for async event processing.
5. DeepFace with ArcFace model is included in the service container image.
6. Photographers upload photos in standard formats (JPEG, PNG, WebP, HEIC).
7. Average face count per photo is 1-5 for typical photography use cases.
8. Workspace photo collections range from hundreds to hundreds of thousands of images.

## Out of Scope

1. Video face detection/tracking (images only).
2. Real-time camera feed processing.
3. Face detection training/model fine-tuning.
4. Emotion/sentiment analysis beyond basic metadata capture.
5. Age/gender estimation features.
6. Face verification for security/authentication purposes.
7. Cross-workspace face matching.
8. Google ADK (A2A Protocol) integration (marked as future enhancement).

## Dependencies

- **Upload Service**: Publishes `asset.processed` events that trigger face detection.
- **Gallery Service**: May consume `face.detected` events for face-based filtering.
- **Backend API**: Provides JWT validation and user context.
- **PostgreSQL + pgvector**: Primary storage for faces and embeddings.
- **Redis**: Idempotency tracking and caching.
- **Kafka**: Event-driven communication between services.
- **Google Cloud Vision API**: External dependency for face detection.
- **DeepFace/ArcFace**: ML model for embedding generation.

## Future Considerations

1. **Google ADK (A2A Protocol)**: Planned integration for agentic collaboration with Gallery and AI services. This will enable intelligent face-based workflows across services.
2. **Alternative detection providers**: Fallback to AWS Rekognition or local model if Google Vision unavailable.
3. **Face verification mode**: Allow photographers to manually verify auto-assigned faces for higher accuracy.
4. **Celebrity/public figure detection**: Option to identify known public figures in photos.
5. **Face search by attributes**: Find faces by glasses, beard, hair color, etc.
