# Tasks: Gallery Service Microservice

**Input**: Design documents from `/specs/001-gallery-service/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/gallery-api.yaml, quickstart.md

**Tests**: Tests are NOT explicitly requested in the specification. Focus on implementation tasks. Integration testing will be performed manually using examples from quickstart.md.

**Organization**: Tasks are grouped by user story (8 total) to enable independent implementation and testing of each story. Each story delivers standalone value.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US8)
- Include exact file paths in descriptions

## Path Conventions

Project type: **Web application (microservice backend)**
Base path: `services/gallery-service/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create gallery-service directory structure at services/gallery-service/
- [ ] T002 Create Dockerfile with Python 3.11-slim base image in services/gallery-service/Dockerfile
- [ ] T003 [P] Create requirements.txt with FastAPI, SQLAlchemy, asyncpg, Pillow, boto3, Redis, Kafka dependencies in services/gallery-service/requirements.txt
- [ ] T004 [P] Create pyproject.toml for Poetry configuration in services/gallery-service/pyproject.toml
- [ ] T005 [P] Create README.md documenting Gallery Service setup in services/gallery-service/README.md
- [ ] T006 [P] Create .dockerignore for Python build artifacts in services/gallery-service/.dockerignore
- [ ] T007 Create alembic.ini for database migration configuration in services/gallery-service/alembic.ini
- [ ] T008 [P] Create alembic/env.py for migration environment setup in services/gallery-service/alembic/env.py
- [ ] T009 [P] Create alembic/script.py.mako template in services/gallery-service/alembic/script.py.mako
- [ ] T010 Add gallery-service to docker-compose.yml at infrastructure/docker/docker-compose.yml (port 8004, Traefik routing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Create Alembic migration 001_create_galleries_schema.py with 7 tables (galleries, sub_galleries, share_links, gallery_assets, visitors, gallery_visitors, security_audit_log) + indexes + triggers + RLS policies in services/gallery-service/alembic/versions/001_create_galleries_schema.py
- [ ] T012 [P] Create config.py with Pydantic Settings for all environment variables in services/gallery-service/src/app/core/config.py
- [ ] T013 [P] Create database.py with PostgreSQL connection pool and session management in services/gallery-service/src/app/core/database.py
- [ ] T014 [P] Create redis.py with Redis connection pool and pub/sub setup in services/gallery-service/src/app/core/redis.py
- [ ] T015 [P] Create kafka.py with Kafka producer/consumer initialization in services/gallery-service/src/app/core/kafka.py
- [ ] T016 [P] Create auth.py with JWT verification and Magic Link token extraction middleware in services/gallery-service/src/app/core/auth.py
- [ ] T017 [P] Create metrics.py with Prometheus metrics definitions (http_requests_total, http_request_duration_seconds, websocket_active_connections, cache_hit_ratio) in services/gallery-service/src/app/core/metrics.py
- [ ] T018 [P] Create logging.py with structured JSON logging configuration for Loki in services/gallery-service/src/app/core/logging.py
- [ ] T019 Create main.py with FastAPI app, lifespan management, and router aggregation in services/gallery-service/src/app/main.py
- [ ] T020 [P] Create auth_middleware.py with JWT and Magic Link authentication logic in services/gallery-service/src/app/middleware/auth_middleware.py
- [ ] T021 [P] Create rate_limit_middleware.py with per-IP (200 req/min) and per-Magic-Link (100 req/min) rate limiting in services/gallery-service/src/app/middleware/rate_limit_middleware.py
- [ ] T022 [P] Create metrics_middleware.py with Prometheus metrics collection for requests in services/gallery-service/src/app/middleware/metrics_middleware.py
- [ ] T023 [P] Create error_middleware.py with consistent error response formatting in services/gallery-service/src/app/middleware/error_middleware.py
- [ ] T024 [P] Create cors_middleware.py with CORS configuration for frontend origins in services/gallery-service/src/app/middleware/cors_middleware.py
- [ ] T025 [P] Create security.py with Argon2id password hashing utilities in services/gallery-service/src/app/utils/security.py
- [ ] T026 [P] Create validation.py with RFC 5322 email validation and PIN format validation in services/gallery-service/src/app/utils/validation.py
- [ ] T027 [P] Create pagination.py with cursor-based pagination helpers (encode/decode cursor, O(1) performance) in services/gallery-service/src/app/utils/pagination.py
- [ ] T028 [P] Create cache.py with Redis caching helpers (get/set with TTL, invalidation patterns) in services/gallery-service/src/app/utils/cache.py
- [ ] T029 Create router.py aggregating all API routers in services/gallery-service/src/app/api/v1/router.py
- [ ] T030 Create health.py with /health (liveness) and /ready (readiness) endpoints and /metrics (Prometheus) in services/gallery-service/src/app/api/v1/health.py
- [ ] T031 Create conftest.py with pytest fixtures (test database, Redis, mocked dependencies) in services/gallery-service/tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Public Gallery Viewing via Magic Link (Priority: P1) 🎯 MVP

**Goal**: Enable clients to access galleries via Magic Links without authentication, view photos organized by sub-galleries, and download photos according to gallery permissions.

**Independent Test**: Generate a Magic Link via Backend API, access gallery through it, view photos across sub-galleries, verify permission-based downloads work correctly.

### Implementation for User Story 1

- [ ] T032 [P] [US1] Create Gallery SQLAlchemy model in services/gallery-service/src/app/models/gallery.py
- [ ] T033 [P] [US1] Create SubGallery SQLAlchemy model in services/gallery-service/src/app/models/sub_gallery.py
- [ ] T034 [P] [US1] Create ShareLink SQLAlchemy model in services/gallery-service/src/app/models/share_link.py
- [ ] T035 [P] [US1] Create GalleryAsset SQLAlchemy model in services/gallery-service/src/app/models/gallery_asset.py
- [ ] T036 [US1] Create Gallery Pydantic schemas (GalleryResponse, GalleryStats) in services/gallery-service/src/app/schemas/gallery.py
- [ ] T037 [US1] Create ShareLink Pydantic schemas (MagicLinkAccessResponse, VerifyLinkRequest) in services/gallery-service/src/app/schemas/share_link.py
- [ ] T038 [US1] Implement ShareLinkService with verify_magic_link (check status, expires_at, max_accesses, atomically increment access_count) in services/gallery-service/src/app/services/share_link_service.py
- [ ] T039 [US1] Implement GalleryService with get_gallery_metadata (fetch gallery + sub-galleries + stats from cache or DB) in services/gallery-service/src/app/services/gallery_service.py
- [ ] T040 [US1] Implement public_access.py with POST /public/verify-link endpoint (password verification with Argon2id, rate limiting 5 attempts/15 min) in services/gallery-service/src/app/api/v1/public_access.py
- [ ] T041 [US1] Implement gallery_viewing.py with GET /public/gallery/{gallery_id}/photos endpoint (cursor-based pagination, limit 50-100, LQIP + signed URLs) in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T042 [US1] Implement SignedUrlService with generate_thumbnail_url (R2 presigned URL, 4hr TTL) and generate_download_url (1hr TTL) using boto3 in services/gallery-service/src/app/services/signed_url_service.py
- [ ] T043 [US1] Add POST /public/photo/{asset_id}/verify-pin endpoint for PIN-protected photos in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T044 [US1] Add cache invalidation for gallery metadata on gallery updates in services/gallery-service/src/app/services/gallery_service.py
- [ ] T045 [US1] Add security audit logging for password attempts, PIN attempts, rate limit violations to security_audit_log table in services/gallery-service/src/app/utils/security.py

**Checkpoint**: User Story 1 complete - clients can access galleries via Magic Links, view photos, and download according to permissions

---

## Phase 4: User Story 2 - Real-Time Proofing and Collaboration (Priority: P1)

**Goal**: Enable real-time WebSocket updates for favorites, selections, and comments during live proofing sessions between photographers and clients.

**Independent Test**: Establish WebSocket connections from two clients, add favorites/selections from one client, verify instant updates appear on the other client's interface.

### Implementation for User Story 2

- [ ] T046 [P] [US2] Implement WebSocketConnectionManager with in-memory connection tracking, Redis pub/sub integration via Broadcaster in services/gallery-service/src/app/services/websocket_manager.py
- [ ] T047 [US2] Create websocket.py with WebSocket endpoint /ws/gallery/{gallery_id} (connection limits 500/pod, sequence number sync) in services/gallery-service/src/app/api/v1/websocket.py
- [ ] T048 [US2] Add broadcast_to_room method in WebSocketConnectionManager to publish events (favorite_added, selection_added, comment_added) to Redis channel gallery:{gallery_id}:proofing in services/gallery-service/src/app/services/websocket_manager.py
- [ ] T049 [US2] Add listen_to_room method in WebSocketConnectionManager to subscribe to Redis channel and forward messages to local WebSocket clients in services/gallery-service/src/app/services/websocket_manager.py
- [ ] T050 [US2] Implement graceful shutdown handler in main.py lifespan to drain WebSocket connections (30-second grace period) before pod termination in services/gallery-service/src/app/main.py
- [ ] T051 [US2] Add Prometheus gauge metric websocket_active_connections tracking per gallery_id in services/gallery-service/src/app/core/metrics.py
- [ ] T052 [US2] Add WebSocket message handler for favorite_add, selection_add, comment_add events with payload validation in services/gallery-service/src/app/api/v1/websocket.py
- [ ] T053 [US2] Add sync_response handler for reconnection with lastSeq parameter to send missed events in services/gallery-service/src/app/api/v1/websocket.py
- [ ] T054 [US2] Update GalleryAsset model to track favorites_count and selections_count (denormalized, updated via triggers) in services/gallery-service/src/app/models/gallery_asset.py
- [ ] T055 [US2] Add exponential backoff reconnection logic documentation in services/gallery-service/README.md for frontend clients

**Checkpoint**: User Story 2 complete - WebSocket real-time updates work across multiple clients and pods, KEDA scales when connection count exceeds 500

---

## Phase 5: User Story 3 - High-Performance Public Gallery Delivery (Priority: P1)

**Goal**: Deliver instant gallery page loads with LQIP placeholders, sub-100ms cached thumbnail delivery, prefetching for smooth scrolling, and support for 50,000 concurrent viewers.

**Independent Test**: Load test with 1,000 concurrent requests, measure P95 latency (<300ms target), verify LQIP placeholders appear instantly (<50ms), confirm cache hit rates exceed 80%.

### Implementation for User Story 3

- [ ] T056 [P] [US3] Implement LQIPService with generate_lqip method using Pillow (16x16 WebP, quality 70, base64 data URI) in services/gallery-service/src/app/services/lqip_service.py
- [ ] T057 [P] [US3] Add generate_lqip_async method for non-blocking LQIP generation in thread pool executor in services/gallery-service/src/app/services/lqip_service.py
- [ ] T058 [US3] Update gallery_viewing.py GET /public/gallery/{gallery_id}/photos to include LQIP data URIs in response with immutable cache headers (Cache-Control: private, max-age=14400, immutable) in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T059 [US3] Add Redis caching for gallery photos paginated responses (gallery:{gallery_id}:photos:page:{cursor}, 10-minute TTL) in services/gallery-service/src/app/services/gallery_service.py
- [ ] T060 [US3] Add Redis caching for gallery metadata (gallery:{gallery_id}:metadata, 5-minute TTL) in services/gallery-service/src/app/services/gallery_service.py
- [ ] T061 [US3] Add Redis caching for gallery stats (gallery:{gallery_id}:stats, 5-minute TTL) in services/gallery-service/src/app/services/gallery_service.py
- [ ] T062 [US3] Implement cursor-based pagination in gallery_viewing.py using base64-encoded (created_at|id) composite key for O(1) performance in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T063 [US3] Add prefetching logic documentation for frontend (next page at 75% scroll, lightbox neighbors N-1/N+1) in services/gallery-service/README.md
- [ ] T064 [US3] Create KEDA ScaledObject YAML with dual Prometheus triggers (HTTP RPS >100, WebSocket connections >500) in infrastructure/kubernetes/gallery-service/keda-scaledobject.yaml
- [ ] T065 [US3] Configure KEDA ScaledObject with minReplicaCount: 5, maxReplicaCount: 50, pollingInterval: 15s, cooldownPeriod: 60s in infrastructure/kubernetes/gallery-service/keda-scaledobject.yaml
- [ ] T066 [US3] Add Prometheus metrics http_requests_total and http_request_duration_seconds histograms to metrics_middleware.py in services/gallery-service/src/app/middleware/metrics_middleware.py
- [ ] T067 [US3] Add cache_hit_ratio gauge metric to cache.py for monitoring cache effectiveness in services/gallery-service/src/app/utils/cache.py
- [ ] T068 [US3] Update Dockerfile with health check (curl localhost:8004/health) and SIGTERM handling for graceful shutdown in services/gallery-service/Dockerfile

**Checkpoint**: User Story 3 complete - galleries load instantly with LQIP, P95 latency <300ms, KEDA autoscaling works, 50,000 concurrent viewers supported

---

## Phase 6: User Story 4 - Batch Operations for Staff Efficiency (Priority: P2)

**Goal**: Enable photographers to update visibility, sub-gallery assignments, privacy settings, or tags for up to 500 photos in a single atomic operation completing in under 30 seconds.

**Independent Test**: Select 100 photos, apply batch visibility toggle, verify all changes persist correctly, confirm operation completes in under 5 seconds.

### Implementation for User Story 4

- [ ] T069 [P] [US4] Create batch_operations.py router file in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T070 [P] [US4] Implement POST /staff/gallery/{gallery_id}/batch/visibility endpoint (up to 500 asset IDs, atomic transaction, 30s timeout) in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T071 [P] [US4] Implement POST /staff/gallery/{gallery_id}/batch/sub-gallery endpoint for batch reassignment with rollback on failure in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T072 [P] [US4] Implement POST /staff/gallery/{gallery_id}/batch/privacy endpoint for batch PIN protection (shared PIN, is_private flag) in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T073 [P] [US4] Implement POST /staff/gallery/{gallery_id}/batch/tags endpoint with add/remove/replace operations (max 50 tags, conflict detection) in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T074 [US4] Add batch_update_visibility method in GalleryService with atomic BEGIN/COMMIT transaction handling in services/gallery-service/src/app/services/gallery_service.py
- [ ] T075 [US4] Add validation for batch size (max 500 items) and return 400 error with suggestion to use background job for larger batches in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T076 [US4] Add 30-second timeout enforcement with 408 error response and rollback on timeout in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T077 [US4] Verify database triggers update gallery.photo_count, gallery.video_count after batch operations in Alembic migration in services/gallery-service/alembic/versions/001_create_galleries_schema.py
- [ ] T078 [US4] Add cache invalidation for affected galleries after batch operations in services/gallery-service/src/app/services/gallery_service.py

**Checkpoint**: User Story 4 complete - photographers can efficiently manage 500 photos at once with atomic operations and proper rollback

---

## Phase 7: User Story 5 - Sub-Gallery Organization and Navigation (Priority: P2)

**Goal**: Enable gallery organization with sub-galleries (tabs or continuous scroll mode), cover images, photo counts, and visibility controls for large galleries with 1,000+ photos.

**Independent Test**: Create gallery with 5 sub-galleries, verify tab navigation works, test continuous scroll mode, confirm cover images and counts display accurately.

### Implementation for User Story 5

- [ ] T079 [P] [US5] Create SubGallery Pydantic schemas (SubGalleryResponse, SubGalleryCreate) in services/gallery-service/src/app/schemas/gallery.py
- [ ] T080 [US5] Add sub-galleries array to GalleryResponse schema with cover_asset_id, photo_count, sort_order in services/gallery-service/src/app/schemas/gallery.py
- [ ] T081 [US5] Update get_gallery_metadata in GalleryService to fetch sub-galleries with LEFT JOIN on gallery_assets for cover images in services/gallery-service/src/app/services/gallery_service.py
- [ ] T082 [US5] Add sub_gallery_id filter parameter to GET /public/gallery/{gallery_id}/photos endpoint in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T083 [US5] Add layout_style field (tab | continuous_scroll) to Gallery model and response schema in services/gallery-service/src/app/models/gallery.py
- [ ] T084 [US5] Add visible field to SubGallery model to hide sub-galleries from clients while keeping them accessible to staff in services/gallery-service/src/app/models/sub_gallery.py
- [ ] T085 [US5] Create database trigger to create default "All Photos" sub-gallery when gallery is created in services/gallery-service/alembic/versions/001_create_galleries_schema.py
- [ ] T086 [US5] Add database trigger to update sub_gallery.photo_count when gallery_assets are added/removed/reassigned in services/gallery-service/alembic/versions/001_create_galleries_schema.py
- [ ] T087 [US5] Add sort_order field to SubGallery model with index for efficient ordering queries (gallery_id, sort_order) in services/gallery-service/src/app/models/sub_gallery.py
- [ ] T088 [US5] Document tab navigation and continuous scroll mode frontend implementation patterns in services/gallery-service/README.md

**Checkpoint**: User Story 5 complete - large galleries can be organized into sub-galleries with proper navigation modes and visibility controls

---

## Phase 8: User Story 6 - Asset Privacy and PIN Protection (Priority: P2)

**Goal**: Enable photographers to mark specific photos as private with PIN protection, showing locked thumbnails to clients who must enter a PIN to unlock and view.

**Independent Test**: Mark 50 photos as private with PIN, verify locked thumbnails display, test PIN entry flow with rate limiting, confirm unlocked photos remain accessible within session.

### Implementation for User Story 6

- [ ] T089 [P] [US6] Add is_private and pin_hash fields to GalleryAsset model in services/gallery-service/src/app/models/gallery_asset.py
- [ ] T090 [US6] Add pin_protected field to Gallery model to indicate if any photos have PIN protection in services/gallery-service/src/app/models/gallery.py
- [ ] T091 [US6] Update GET /public/gallery/{gallery_id}/photos to filter out is_private=true photos unless session unlocked in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T092 [US6] Implement POST /public/photo/{asset_id}/verify-pin endpoint with Argon2id PIN verification, rate limiting (5 attempts/15 min), progressive delays (1s, 2s, 4s, 8s, 16s) in services/gallery-service/src/app/api/v1/gallery_viewing.py
- [ ] T093 [US6] Add session state management for unlocked photo IDs (Redis with session token, 1-hour TTL) in services/gallery-service/src/app/utils/cache.py
- [ ] T094 [US6] Add security audit logging for PIN attempts (success/failure, IP address, user_agent) to security_audit_log table in services/gallery-service/src/app/utils/security.py
- [ ] T095 [US6] Update batch privacy endpoint to validate PIN format (4-6 digits) and hash with Argon2id before storing in services/gallery-service/src/app/api/v1/batch_operations.py
- [ ] T096 [US6] Add locked placeholder thumbnail generation (overlay lock icon on LQIP) in services/gallery-service/src/app/services/lqip_service.py
- [ ] T097 [US6] Update GalleryAsset Pydantic schema to include is_private and locked_thumbnail_url fields in services/gallery-service/src/app/schemas/gallery.py

**Checkpoint**: User Story 6 complete - private photos with PIN protection work with proper rate limiting and session management

---

## Phase 9: User Story 7 - Email Registration and Lead Capture (Priority: P3)

**Goal**: Capture visitor information (email, name, phone) via registration modal before gallery access, supporting lead generation and CRM workflows with GDPR/CCPA compliance.

**Independent Test**: Enable email registration on gallery, attempt access without registration, complete form, verify data captured in visitors table and modal skipped on return visits.

### Implementation for User Story 7

- [ ] T098 [P] [US7] Create Visitor SQLAlchemy model in services/gallery-service/src/app/models/visitor.py
- [ ] T099 [P] [US7] Create GalleryVisitor SQLAlchemy model (access log) in services/gallery-service/src/app/models/gallery_visitor.py
- [ ] T100 [US7] Create Visitor Pydantic schemas (VisitorCreate, VisitorResponse) in services/gallery-service/src/app/schemas/visitor.py
- [ ] T101 [US7] Implement VisitorService with register_visitor method (RFC 5322 email validation, upsert logic, optional disposable email blocking) in services/gallery-service/src/app/services/visitor_service.py
- [ ] T102 [US7] Create email_registration.py with POST /public/register-visitor endpoint (email, name, phone, address, metadata fields) in services/gallery-service/src/app/api/v1/email_registration.py
- [ ] T103 [US7] Add email_registration_required field to Gallery and ShareLink models in services/gallery-service/src/app/models/gallery.py and services/gallery-service/src/app/models/share_link.py
- [ ] T104 [US7] Add logic in MagicLinkAccessResponse to indicate if email_registration_required=true in services/gallery-service/src/app/schemas/share_link.py
- [ ] T105 [US7] Add check in verify_magic_link to skip registration if visitor email + gallery_id already exists in gallery_visitors table in services/gallery-service/src/app/services/share_link_service.py
- [ ] T106 [US7] Create GalleryVisitor entry on successful registration with visitor_id, gallery_id, link_id, ip_address, user_agent, referrer in services/gallery-service/src/app/services/visitor_service.py
- [ ] T107 [US7] Add GDPR/CCPA compliance notes in README.md for visitor data retention and deletion workflows in services/gallery-service/README.md
- [ ] T108 [US7] Add unique constraint on visitors (workspace_id, LOWER(email)) for case-insensitive email uniqueness in services/gallery-service/alembic/versions/001_create_galleries_schema.py

**Checkpoint**: User Story 7 complete - email registration captures leads before gallery access with proper validation and privacy compliance

---

## Phase 10: User Story 8 - QR Code Generation for Magic Links (Priority: P3)

**Goal**: Generate customizable QR codes for Magic Links that can be printed in wedding albums or thank-you cards, enabling instant gallery access by scanning with smartphones.

**Independent Test**: Generate Magic Link with QR code configuration, verify QR encodes correct URL, scan with mobile device, confirm successful gallery access.

### Implementation for User Story 8

- [ ] T109 [P] [US8] Implement QRCodeService with generate_qr_code method using qrcode[pil] library in services/gallery-service/src/app/services/qr_code_service.py
- [ ] T110 [US8] Add QR code customization parameters (size: 200/300/500/1000px, color: hex, logo_enabled: bool, error_correction: L/M/Q/H) to ShareLink model fields in services/gallery-service/src/app/models/share_link.py
- [ ] T111 [US8] Create qr_codes.py with GET /staff/share-link/{link_id}/qr-code endpoint (query params: size, color, logo, error_correction) returning PNG image in services/gallery-service/src/app/api/v1/qr_codes.py
- [ ] T112 [US8] Add logo embedding in QR code center (load workspace logo from R2, resize to fit, embed with PIL) in services/gallery-service/src/app/services/qr_code_service.py
- [ ] T113 [US8] Add error correction level validation (L: 7% recovery, M: 15%, Q: 25%, H: 30%) and default to M for balance in services/gallery-service/src/app/services/qr_code_service.py
- [ ] T114 [US8] Add QR code caching (qr:{link_id}:{size}:{color}:{logo}, 24-hour TTL) to avoid regenerating identical QR codes in services/gallery-service/src/app/utils/cache.py
- [ ] T115 [US8] Update ShareLink Pydantic schema to include qr_code_url field with endpoint URL in services/gallery-service/src/app/schemas/share_link.py
- [ ] T116 [US8] Document QR code size recommendations (300px for digital, 500-1000px for print) in services/gallery-service/README.md

**Checkpoint**: User Story 8 complete - QR codes can be generated with custom branding for print-to-digital workflows

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T117 [P] Create KEDA deployment YAML with terminationGracePeriodSeconds: 80 and preStop hook (sleep 30) in infrastructure/kubernetes/gallery-service/deployment.yaml
- [ ] T118 [P] Create Kubernetes Service YAML for gallery-service on port 8004 in infrastructure/kubernetes/gallery-service/service.yaml
- [ ] T119 [P] Add Traefik IngressRoute for gallery-service at /api/gallery/* path in infrastructure/kubernetes/gallery-service/ingressroute.yaml
- [ ] T120 [P] Create Prometheus ServiceMonitor for gallery-service metrics scraping in infrastructure/kubernetes/gallery-service/servicemonitor.yaml
- [ ] T121 [P] Create Grafana dashboard JSON for Gallery Service (request rate, latency, WebSocket connections, cache hit rate, error rate) in infrastructure/grafana/dashboards/gallery-service.json
- [ ] T122 [P] Add Prometheus alert rules for gallery-service (error rate >5%, P95 latency >500ms, pod restart rate >5/hour) in infrastructure/prometheus/alerts/gallery-service.yaml
- [ ] T123 [P] Update ARCHITECTURE_QUICK_REFERENCE.md with Gallery Service entry (port 8004, dependencies, KEDA config) in docs/ARCHITECTURE_QUICK_REFERENCE.md
- [ ] T124 [P] Update infrastructure/docker/.env.example with Gallery Service environment variables
- [ ] T125 Verify quickstart.md examples work end-to-end (Magic Link verification, gallery viewing, WebSocket connection, batch operations) per services/gallery-service/quickstart.md
- [ ] T126 Create load testing script with locust or k6 to simulate 1,000-10,000 concurrent viewers and verify KEDA scaling in infrastructure/load-tests/gallery-service-load-test.py
- [ ] T127 [P] Add code comments for complex algorithms (cursor pagination, WebSocket connection manager, LQIP generation) across services/gallery-service/src/app/
- [ ] T128 [P] Add error handling for R2 connection failures (fallback to database, degraded mode logging) in services/gallery-service/src/app/services/signed_url_service.py
- [ ] T129 [P] Add error handling for Redis connection failures (skip caching, log degraded mode) in services/gallery-service/src/app/utils/cache.py
- [ ] T130 Run Docker Compose build and verify Gallery Service starts on port 8004 with healthy status per infrastructure/docker/docker-compose.yml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational (Phase 2) completion
  - User stories can proceed in parallel if staffed
  - Or sequentially in priority order: US1 → US2 → US3 → US4 → US5 → US6 → US7 → US8
- **Polish (Phase 11)**: Depends on desired user stories being complete (minimum: US1-US3 for MVP)

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational - No dependencies on other stories. Core Magic Link access.
- **US2 (P1)**: Can start after Foundational - Independent WebSocket implementation. No US1 dependency.
- **US3 (P1)**: Can start after Foundational - Independent LQIP and caching. Enhances US1 but not blocking.
- **US4 (P2)**: Can start after Foundational - Batch operations use Gallery/GalleryAsset models from US1 but independently testable.
- **US5 (P2)**: Can start after Foundational - Sub-gallery navigation extends US1 but works independently.
- **US6 (P2)**: Can start after Foundational - PIN protection extends US1 but independently testable.
- **US7 (P3)**: Can start after Foundational - Email registration integrates with US1 but independently testable.
- **US8 (P3)**: Can start after Foundational - QR codes extend US1 Magic Links but independently testable.

### Within Each User Story

- Models before services (models define entities, services use them)
- Services before endpoints (endpoints call service methods)
- Core implementation before integration (build features, then connect)

### Parallel Opportunities

- **Phase 1 (Setup)**: T003, T004, T005, T006, T008, T009 can run in parallel (different files)
- **Phase 2 (Foundational)**: T012-T018, T020-T028 can run in parallel (different files)
- **US1 (Phase 3)**: T032-T035 (models) can run in parallel, then T036-T037 (schemas) in parallel
- **US2 (Phase 4)**: T046 and T051 can run in parallel with T047
- **US3 (Phase 5)**: T056-T057 (LQIP service) and T064-T065 (KEDA YAML) can run in parallel
- **US4 (Phase 6)**: T069-T073 (all batch endpoints) can run in parallel
- **US5 (Phase 7)**: T079-T080 (schemas) can run in parallel
- **US6 (Phase 8)**: T089-T090 (model updates) can run in parallel
- **US7 (Phase 9)**: T098-T100 (models and schemas) can run in parallel
- **US8 (Phase 10)**: T109-T110 can run in parallel
- **Phase 11 (Polish)**: T117-T124, T127-T129 can run in parallel (different files)

---

## Parallel Example: User Story 1 (Magic Link Access)

```bash
# Launch all models for US1 in parallel:
Task T032: "Create Gallery model in services/gallery-service/src/app/models/gallery.py"
Task T033: "Create SubGallery model in services/gallery-service/src/app/models/sub_gallery.py"
Task T034: "Create ShareLink model in services/gallery-service/src/app/models/share_link.py"
Task T035: "Create GalleryAsset model in services/gallery-service/src/app/models/gallery_asset.py"

# Then launch schemas in parallel (after models complete):
Task T036: "Create Gallery schemas in services/gallery-service/src/app/schemas/gallery.py"
Task T037: "Create ShareLink schemas in services/gallery-service/src/app/schemas/share_link.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only - All P1)

1. Complete **Phase 1**: Setup (T001-T010) → Project structure ready
2. Complete **Phase 2**: Foundational (T011-T031) → CRITICAL - blocks all stories
3. Complete **Phase 3**: User Story 1 (T032-T045) → Magic Link access working
4. **VALIDATE**: Test US1 independently via quickstart.md examples
5. Complete **Phase 4**: User Story 2 (T046-T055) → WebSocket real-time updates
6. **VALIDATE**: Test US2 independently with two WebSocket clients
7. Complete **Phase 5**: User Story 3 (T056-T068) → Performance optimization, KEDA
8. **VALIDATE**: Load test with 1,000 concurrent users, verify P95 <300ms
9. **STOP and REVIEW**: MVP delivers core value (gallery viewing, real-time collaboration, high performance)
10. Deploy to staging for acceptance testing

**MVP Scope**: Phases 1-5 (US1-US3) = 68 tasks

### Incremental Delivery (Add P2 Features)

After MVP validated:

11. Complete **Phase 6**: User Story 4 (T069-T078) → Batch operations for staff
12. **VALIDATE**: Test batch visibility toggle with 100 photos
13. Complete **Phase 7**: User Story 5 (T079-T088) → Sub-gallery organization
14. **VALIDATE**: Create gallery with 5 sub-galleries, test tab navigation
15. Complete **Phase 8**: User Story 6 (T089-T097) → PIN protection
16. **VALIDATE**: Mark 50 photos private, test PIN entry with rate limiting
17. Deploy P2 features to production

**P2 Scope**: Phases 6-8 (US4-US6) = 30 additional tasks

### Optional P3 Features (Business Growth)

If lead capture and print-to-digital workflows are priorities:

18. Complete **Phase 9**: User Story 7 (T098-T108) → Email registration
19. Complete **Phase 10**: User Story 8 (T109-T116) → QR code generation
20. **VALIDATE**: Test lead capture flow and QR code scanning
21. Deploy P3 features to production

**P3 Scope**: Phases 9-10 (US7-US8) = 19 additional tasks

### Final Polish

22. Complete **Phase 11**: Polish (T117-T130) → KEDA deployment, monitoring, documentation
23. **VALIDATE**: Run load tests (T126), verify Grafana dashboards (T121), test all quickstart examples (T125)
24. Production-ready deployment

**Polish Scope**: Phase 11 = 14 tasks

### Parallel Team Strategy

With 3 developers after Foundational phase (Phase 2) completes:

- **Developer A**: User Story 1 (Phase 3) → Magic Link access
- **Developer B**: User Story 2 (Phase 4) → WebSocket proofing
- **Developer C**: User Story 3 (Phase 5) → Performance optimization

All three stories can develop in parallel, then integrate for final testing.

---

## Task Summary

| Phase | User Story | Priority | Task Count | Cumulative |
|-------|------------|----------|------------|------------|
| Phase 1 | Setup | - | 10 | 10 |
| Phase 2 | Foundational | - | 21 | 31 |
| Phase 3 | US1: Magic Link Access | P1 | 14 | 45 |
| Phase 4 | US2: Real-Time Proofing | P1 | 10 | 55 |
| Phase 5 | US3: High Performance | P1 | 13 | 68 |
| Phase 6 | US4: Batch Operations | P2 | 10 | 78 |
| Phase 7 | US5: Sub-Gallery Navigation | P2 | 10 | 88 |
| Phase 8 | US6: PIN Protection | P2 | 9 | 97 |
| Phase 9 | US7: Email Registration | P3 | 11 | 108 |
| Phase 10 | US8: QR Code Generation | P3 | 8 | 116 |
| Phase 11 | Polish & Cross-Cutting | - | 14 | 130 |

**Total Tasks**: 130

**MVP Scope** (P1 only): 68 tasks (Setup + Foundational + US1 + US2 + US3)

**P2 Scope** (MVP + P2): 98 tasks (add US4 + US5 + US6)

**Full Feature Set**: 130 tasks (all user stories + polish)

**Parallel Opportunities**: 45 tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**: Each user story (US1-US8) has clear test criteria for standalone validation

---

## Notes

- **[P]** tasks = different files, no blocking dependencies, can run in parallel
- **[Story]** label = maps task to specific user story for traceability (US1-US8)
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included (not requested in specification) - validation via quickstart.md examples
- MVP delivers complete value with US1-US3 (Magic Link access, real-time proofing, high performance)
- Path structure: `services/gallery-service/` for all microservice code
- Database migrations: Single Alembic migration with all 7 tables (T011)
- KEDA autoscaling: Configured in Phase 5 (US3) for production Kubernetes deployment
- Monitoring: Prometheus metrics, Grafana dashboards, Loki logs configured in Foundational phase and Polish phase
