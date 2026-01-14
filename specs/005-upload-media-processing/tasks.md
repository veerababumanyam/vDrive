# Tasks: Storage & Media Processing

**Input**: Design documents from `/specs/005-upload-media-processing/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Architecture Note**: Per research.md, this feature uses **Kafka consumers** (not Celery) to align with existing vDrive event-driven architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md, two microservices:
- **Upload Service**: `services/upload-service/src/app/`
- **Processing Service**: `services/processing-service/src/app/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for both microservices

- [ ] T001 [P] Create upload-service directory structure per plan.md: `services/upload-service/src/app/{api,core,models,schemas,services}/`
- [ ] T002 [P] Create processing-service directory structure per plan.md: `services/processing-service/src/app/{consumers,core,services}/`
- [ ] T003 [P] Create upload-service requirements.txt with dependencies from plan.md (fastapi, tuspyserver, cryptography, aiokafka, boto3)
- [ ] T004 [P] Create processing-service requirements.txt with dependencies from plan.md (Pillow, rawpy, ffmpeg-python, ExifRead, google-cloud-vision)
- [ ] T005 [P] Create upload-service Dockerfile based on existing gallery-service pattern
- [ ] T006 [P] Create processing-service Dockerfile with ffmpeg and rawpy build dependencies
- [ ] T007 Add upload-service and processing-service to `infrastructure/docker/docker-compose.yml` (ports 8008, 8010)
- [ ] T008 [P] Create `.env.example` entries for new services (R2 config, GCV credentials, encryption keys)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Migrations

- [ ] T009 Create alembic configuration for upload-service: `services/upload-service/alembic/`
- [ ] T010 [P] Create migration 001_create_uploads.py per data-model.md Upload entity
- [ ] T011 [P] Create migration 002_create_assets.py per data-model.md Asset entity
- [ ] T012 [P] Create migration 003_create_asset_metadata.py per data-model.md AssetMetadata entity
- [ ] T013 [P] Create migration 004_create_faces.py per data-model.md Face entity (requires pgvector)
- [ ] T014 [P] Create migration 005_create_processing_tasks.py per data-model.md ProcessingTask entity
- [ ] T015 [P] Create migration 006_create_encryption_keys.py per data-model.md EncryptionKey entity

### Core Infrastructure

- [ ] T016 [P] Implement config.py for upload-service: `services/upload-service/src/app/core/config.py` (Pydantic Settings)
- [ ] T017 [P] Implement config.py for processing-service: `services/processing-service/src/app/core/config.py`
- [ ] T018 [P] Implement database.py with async SQLAlchemy engine: `services/upload-service/src/app/core/database.py`
- [ ] T019 [P] Implement redis.py for upload state caching: `services/upload-service/src/app/core/redis.py`
- [ ] T020 [P] Implement logging.py with structlog: `services/upload-service/src/app/core/logging.py`
- [ ] T021 [P] Implement logging.py for processing-service: `services/processing-service/src/app/core/logging.py`
- [ ] T022 Implement metrics.py with Prometheus client: `services/processing-service/src/app/core/metrics.py`

### SQLAlchemy Models

- [ ] T023 [P] Create Upload model: `services/upload-service/src/app/models/upload.py` per data-model.md
- [ ] T024 [P] Create Asset model: `services/upload-service/src/app/models/asset.py` per data-model.md
- [ ] T025 [P] Create AssetMetadata model: `services/upload-service/src/app/models/asset_metadata.py`
- [ ] T026 [P] Create Face model with pgvector embedding: `services/upload-service/src/app/models/face.py`
- [ ] T027 [P] Create ProcessingTask model: `services/upload-service/src/app/models/processing_task.py`
- [ ] T028 [P] Create EncryptionKey model: `services/upload-service/src/app/models/encryption_key.py`
- [ ] T029 Create models __init__.py with all exports: `services/upload-service/src/app/models/__init__.py`

### Pydantic Schemas (from OpenAPI contracts)

- [ ] T030 [P] Create upload schemas per contracts/upload-service-openapi.yaml: `services/upload-service/src/app/schemas/upload.py`
- [ ] T031 [P] Create asset schemas per contracts/upload-service-openapi.yaml: `services/upload-service/src/app/schemas/asset.py`
- [ ] T032 [P] Create event schemas per contracts/kafka-events.yaml: `services/upload-service/src/app/schemas/events.py`
- [ ] T033 Create schemas __init__.py: `services/upload-service/src/app/schemas/__init__.py`

### FastAPI Application Shell

- [ ] T034 Create main.py for upload-service with FastAPI app, health/metrics endpoints: `services/upload-service/src/app/main.py`
- [ ] T035 Create main.py for processing-service with Kafka consumer runner: `services/processing-service/src/app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Resumable Large File Upload (Priority: P1) 🎯 MVP

**Goal**: Photographers can upload large files with automatic resume on connection loss

**Independent Test**: Initiate 500MB upload, simulate network drop at 50%, reconnect and verify resume

**Requirements**: FR-001, FR-002, FR-003, FR-005, FR-008, FR-009, FR-010

### Implementation for User Story 1

- [ ] T036 [US1] Implement custom R2 TUS storage backend: `services/upload-service/src/app/services/r2_tus_backend.py`
  - S3 multipart upload API via boto3
  - Part metadata tracking in Redis
  - Minimum 5MB part size for R2 compatibility
- [ ] T037 [US1] Implement upload_service.py orchestration: `services/upload-service/src/app/services/upload_service.py`
  - Create upload session
  - Track progress
  - Assemble chunks
  - Validate checksums
- [ ] T038 [US1] Implement TUS protocol endpoints per OpenAPI: `services/upload-service/src/app/api/v1/tus.py`
  - POST /files (createUpload)
  - HEAD /files/{uploadId} (getUploadOffset)
  - PATCH /files/{uploadId} (uploadChunk)
  - DELETE /files/{uploadId} (cancelUpload)
  - OPTIONS /files (tusOptions)
- [ ] T039 [US1] Implement upload management endpoints: `services/upload-service/src/app/api/v1/uploads.py`
  - GET /uploads/{uploadId}/status
  - GET /uploads (listUploads with pagination)
- [ ] T040 [US1] Add MIME type validation against allowlist (FR-003): `services/upload-service/src/app/services/validation_service.py`
- [ ] T041 [US1] Implement upload URL TTL management (24h default, FR-005)
- [ ] T042 [US1] Add concurrent upload limiting (10 parallel per workspace, FR-009)
- [ ] T043 [US1] Implement SHA-256 checksum validation (FR-010)
- [ ] T044 [US1] Register TUS router in main.py, configure tuspyserver with R2 backend

**Checkpoint**: Resumable uploads work end-to-end, files stored in R2

---

## Phase 4: User Story 2 - Secure File Encryption and Storage (Priority: P1)

**Goal**: All files encrypted with AES-256-GCM using workspace-derived keys before R2 storage

**Independent Test**: Upload file, verify R2 object is encrypted binary, verify gallery service can decrypt

**Requirements**: FR-004, FR-007

### Implementation for User Story 2

- [ ] T045 [US2] Implement encryption_service.py with AES-256-GCM: `services/upload-service/src/app/services/encryption_service.py`
  - HKDF-SHA256 key derivation from master key + workspace context
  - Streaming encryption for large files (8KB chunks per research.md)
  - IV and auth_tag generation/storage
- [ ] T046 [US2] Implement key rotation support in EncryptionKey model
  - Track active key per workspace
  - Support decryption with old keys during transition
- [ ] T047 [US2] Implement storage_service.py for R2 operations: `services/upload-service/src/app/services/storage_service.py`
  - Structured key generation: `workspaces/{workspace_id}/assets/{asset_id}/{variant}.{ext}`
  - Encrypted multipart upload
  - Presigned URL generation for decryption context
- [ ] T048 [US2] Integrate encryption into upload flow (encrypt before R2 storage)
- [ ] T049 [US2] Store encryption metadata (IV, auth_tag, key_id) in Asset record
- [ ] T050 [US2] Add encryption_key_id index for key rotation queries

**Checkpoint**: All uploads encrypted, encryption metadata tracked, key rotation supported

---

## Phase 5: User Story 6 - Event-Driven Processing Pipeline (Priority: P1)

**Goal**: Upload service publishes Kafka events; processing service consumes them

**Independent Test**: Upload file, verify correct Kafka events with proper payloads

**Requirements**: FR-006, FR-029, FR-030, FR-031, FR-032

### Implementation for User Story 6

- [ ] T051 [US6] Implement event_service.py for Kafka publishing: `services/upload-service/src/app/services/event_service.py`
  - aiokafka producer setup
  - Event serialization per kafka-events.yaml schemas
  - Retry with exponential backoff
  - Partition key = workspace_id for ordering
- [ ] T052 [US6] Publish `upload.initiated` event on TUS POST
- [ ] T053 [US6] Publish `upload.completed` event on successful assembly
- [ ] T054 [US6] Implement base_consumer.py with retry and DLQ logic: `services/processing-service/src/app/consumers/base_consumer.py`
  - Consumer group management
  - At-least-once delivery
  - Idempotency via asset_id
  - Dead-letter queue on max retries
- [ ] T055 [US6] Create asset_processor.py consumer skeleton: `services/processing-service/src/app/consumers/asset_processor.py`
  - Consume `upload.completed` events
  - Trigger processing pipeline
  - Produce `asset.processing` and `asset.processed` events
- [ ] T056 [US6] Implement Kafka consumer runner in processing-service main.py
- [ ] T057 [US6] Add Kafka broker unavailability handling (retry queue, DLQ)

**Checkpoint**: Events flow correctly between services, idempotent processing

---

## Phase 6: User Story 7 - Background Task Processing (Priority: P1)

**Goal**: Resource-intensive processing handled by Kafka consumers with KEDA scaling

**Independent Test**: Submit processing task, verify workers process correctly, check Prometheus metrics

**Requirements**: FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028

**Note**: Using Kafka consumers (per research.md decision), not Celery

### Implementation for User Story 7

- [ ] T058 [US7] Implement ProcessingTask status management in processing-service
- [ ] T059 [US7] Add task retry logic with exponential backoff (max 3 retries, FR-027)
- [ ] T060 [US7] Implement task result storage in output_data JSONB
- [ ] T061 [US7] Add Prometheus metrics for task processing: `services/processing-service/src/app/core/metrics.py`
  - tasks_processed_total (counter by task_type, status)
  - task_duration_seconds (histogram)
  - tasks_pending_gauge
- [ ] T062 [US7] Expose /metrics endpoint (port 8010, FR-028)
- [ ] T063 [US7] Create KEDA ScaledObject for processing-service: `infrastructure/kubernetes/keda/processing-scaledobject.yaml`
  - Scale on Kafka consumer lag > 100
- [ ] T064 [US7] Implement scheduled cleanup for expired uploads (>24h, FR-025)
  - Can use Kubernetes CronJob or periodic task in consumer

**Checkpoint**: Background processing works with scaling and monitoring

---

## Phase 7: User Story 3 - Automatic Thumbnail and WebP Generation (Priority: P1)

**Goal**: Generate WebP derivatives (thumbnail, preview, LQIP) for all uploaded assets

**Independent Test**: Upload 20MB RAW file, verify three derivatives with correct dimensions within 30s

**Requirements**: FR-011, FR-012, FR-013, FR-015, FR-016

### Implementation for User Story 3

- [ ] T065 [US3] Implement thumbnail_service.py: `services/processing-service/src/app/services/thumbnail_service.py`
  - Pillow-based WebP generation
  - Thumbnail: 300px longest edge, 80% quality
  - Preview: 1200px longest edge, 85% quality
  - LQIP: 20px, 60% quality, base64 encoded
- [ ] T066 [US3] Add RAW format support via rawpy (CR2, NEF, ARW, DNG)
  - Extract embedded JPEG preview
  - Fall back to full decode if no preview
- [ ] T067 [US3] Implement video thumbnail extraction via ffmpeg-python: `services/processing-service/src/app/services/video_service.py`
  - First frame for thumbnail
  - Representative frame (25% in) for preview
- [ ] T068 [US3] Integrate thumbnail generation into asset_processor.py consumer
- [ ] T069 [US3] Encrypt derivatives before R2 upload (reuse encryption_service)
- [ ] T070 [US3] Store derivative keys in Asset record (thumbnail_key, preview_key, lqip_base64)
- [ ] T071 [US3] Implement asset retrieval endpoint: `services/upload-service/src/app/api/v1/assets.py`
  - GET /assets/{assetId}
  - GET /assets/{assetId}/processing

**Checkpoint**: All uploads have derivatives, video support works

---

## Phase 8: User Story 4 - Metadata Extraction and Indexing (Priority: P2)

**Goal**: Extract EXIF metadata and index for search

**Independent Test**: Upload photo with EXIF, verify metadata in database and searchable

**Requirements**: FR-014, FR-017

### Implementation for User Story 4

- [ ] T072 [US4] Implement exif_service.py: `services/processing-service/src/app/services/exif_service.py`
  - ExifRead-based extraction
  - Parse camera, lens, settings (aperture, shutter, ISO)
  - Parse GPS coordinates
  - Handle missing/malformed EXIF gracefully
- [ ] T073 [US4] Map EXIF tags to AssetMetadata model fields
- [ ] T074 [US4] Integrate EXIF extraction into asset_processor.py
- [ ] T075 [US4] Store raw_exif JSONB for complete EXIF dump
- [ ] T076 [US4] Add captured_at index for timeline queries
- [ ] T077 [US4] Add GPS index for location-based queries
- [ ] T078 [US4] Implement metadata embedding for pgvector semantic search (FR-017)

**Checkpoint**: Metadata extracted and searchable

---

## Phase 9: User Story 5 - AI Face Detection and Recognition (Priority: P2)

**Goal**: Detect faces using Google Cloud Vision, store embeddings for matching

**Independent Test**: Upload group photo, verify face bounding boxes and confidence scores

**Requirements**: FR-018, FR-019, FR-020, FR-021

### Implementation for User Story 5

- [ ] T079 [US5] Implement face_service.py: `services/processing-service/src/app/services/face_service.py`
  - google-cloud-vision client setup
  - Face detection API call
  - Bounding box normalization (0-1 coordinates)
  - Confidence score extraction
- [ ] T080 [US5] Implement rate limiting for GCV API (FR-021)
  - Token bucket or sliding window
  - Queue requests when approaching limits
  - Exponential backoff on 429 responses
- [ ] T081 [US5] Create face_detector.py consumer: `services/processing-service/src/app/consumers/face_detector.py`
  - Separate consumer group for AI workload
  - Check workspace face_detection_enabled setting (FR-020)
- [ ] T082 [US5] Store Face records with bounding_box JSONB
- [ ] T083 [US5] Generate and store face embeddings in pgvector (512-dimension)
- [ ] T084 [US5] Publish `face.detected` event per kafka-events.yaml
- [ ] T085 [US5] Add IVF index for face embedding similarity search

**Checkpoint**: Faces detected and indexed for matching

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

### Documentation

- [ ] T086 [P] Update quickstart.md with actual tested commands
- [ ] T087 [P] Add API documentation to upload-service (FastAPI automatic docs)
- [ ] T088 [P] Document error codes and troubleshooting in docs/

### Testing

- [ ] T089 [P] Create unit tests for encryption_service.py
- [ ] T090 [P] Create unit tests for thumbnail_service.py
- [ ] T091 [P] Create integration tests for TUS upload flow
- [ ] T092 [P] Create contract tests for Kafka events
- [ ] T093 Create end-to-end test: upload → process → retrieve asset

### Security & Operations

- [ ] T094 Add JWT authentication to all endpoints (integrate with auth-service)
- [ ] T095 Add workspace_id validation and isolation in all queries
- [ ] T096 Implement request tracing with correlation IDs
- [ ] T097 Add alerting rules for Prometheus: `infrastructure/kubernetes/alertmanager/upload-alerts.yaml`
- [ ] T098 Create Grafana dashboard for upload/processing metrics

### Performance

- [ ] T099 Add Redis caching for upload status polling
- [ ] T100 Optimize large file processing with streaming
- [ ] T101 Tune KEDA scaling thresholds based on load testing

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ─────────────────────────────────────────────►
                                                              │
Phase 2: Foundational (BLOCKING) ──────────────────────────► │
                                                              │
              ┌──────────────────────────────────────────────┼────────────────────────────────────────────────┐
              │                                              │                                                │
              ▼                                              ▼                                                ▼
Phase 3: US1 (Upload)    Phase 4: US2 (Encryption)    Phase 5: US6 (Events)    Phase 6: US7 (Processing)
              │                    │                          │                          │
              │                    │                          │                          │
              └────────────────────┴──────────────────────────┴──────────────────────────┘
                                                              │
                                                              ▼
                                          Phase 7: US3 (Thumbnails) ── depends on US1, US2, US6
                                                              │
                                          ┌───────────────────┴───────────────────┐
                                          ▼                                       ▼
                                  Phase 8: US4 (Metadata)              Phase 9: US5 (Faces)
                                          │                                       │
                                          └───────────────────┬───────────────────┘
                                                              │
                                                              ▼
                                                    Phase 10: Polish
```

### User Story Dependencies

| Story | Depends On | Why |
|-------|------------|-----|
| US1 (Upload) | Foundational | Needs models, config, database |
| US2 (Encryption) | Foundational | Needs models, config |
| US6 (Events) | Foundational | Needs schemas, Kafka config |
| US7 (Processing) | Foundational | Needs models, metrics |
| US3 (Thumbnails) | US1, US2, US6 | Needs upload flow, encryption, events |
| US4 (Metadata) | US3 | Runs in same processing pipeline |
| US5 (Faces) | US3 | Runs in same processing pipeline |

### Parallel Opportunities

**Setup Phase** (all parallel):
```bash
# Launch all setup tasks together:
Task: T001, T002, T003, T004, T005, T006, T008
# T007 (docker-compose) should be last
```

**Foundational Phase** (models parallel, then schemas, then app):
```bash
# Launch all migrations in parallel:
Task: T010, T011, T012, T013, T014, T015

# Launch all models in parallel:
Task: T023, T024, T025, T026, T027, T028

# Launch all schemas in parallel:
Task: T030, T031, T032
```

**P1 Stories** (after foundational):
```bash
# These four P1 stories can start in parallel if team capacity allows:
# - US1 (Upload): T036-T044
# - US2 (Encryption): T045-T050
# - US6 (Events): T051-T057
# - US7 (Processing): T058-T064

# However, US3 (Thumbnails) depends on all of them completing first
```

---

## Implementation Strategy

### MVP First (Minimum Viable Upload)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 (Resumable Upload) - **Can upload files**
4. Complete Phase 4: US2 (Encryption) - **Files are secure**
5. **STOP and VALIDATE**: Test upload and encryption independently
6. Deploy MVP if acceptable

### Full P1 Delivery

1. MVP + Phase 5: US6 (Events) - **System integrated**
2. + Phase 6: US7 (Processing) - **Background tasks work**
3. + Phase 7: US3 (Thumbnails) - **Galleries can load fast**
4. **STOP and VALIDATE**: Full P1 feature set
5. Deploy for beta users

### Complete Feature

1. Full P1 + Phase 8: US4 (Metadata) - **Search enabled**
2. + Phase 9: US5 (Faces) - **AI features enabled**
3. + Phase 10: Polish - **Production ready**
4. Deploy for general availability

---

## Task Count Summary

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 8 | 7 |
| Foundational | 26 | 18 |
| US1 (Upload) | 9 | 0 |
| US2 (Encryption) | 6 | 0 |
| US6 (Events) | 7 | 0 |
| US7 (Processing) | 7 | 0 |
| US3 (Thumbnails) | 7 | 0 |
| US4 (Metadata) | 7 | 0 |
| US5 (Faces) | 7 | 0 |
| Polish | 16 | 9 |
| **Total** | **100** | **34** |

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story
- Per research.md: Kafka consumers (not Celery) for background processing
- Port 8008 for upload-service, 8010 for processing-service
- All files encrypted before R2 storage (never store unencrypted)
- Verify each checkpoint before proceeding
