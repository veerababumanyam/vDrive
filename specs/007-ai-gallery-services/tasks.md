# Tasks: Phase 4 - AI & Gallery Services

**Input**: Design documents from `/specs/007-ai-gallery-services/`
**Prerequisites**: plan.md (complete), spec.md (complete)

**Tests**: Tests are included for critical paths only. TDD is not explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Face Service**: `services/face-service/src/app/`
- **AI Search Service**: `services/ai-search-service/src/app/`
- **Gallery Service**: `services/gallery-service/src/app/` (existing, enhancements)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for two new microservices

- [ ] T001 Create face-service directory structure per plan in services/face-service/
- [ ] T002 Create ai-search-service directory structure per plan in services/ai-search-service/
- [ ] T003 [P] Create face-service requirements.txt with dependencies from plan in services/face-service/requirements.txt
- [ ] T004 [P] Create ai-search-service requirements.txt with dependencies from plan in services/ai-search-service/requirements.txt
- [ ] T005 [P] Create face-service Dockerfile based on processing-service pattern in services/face-service/Dockerfile
- [ ] T006 [P] Create ai-search-service Dockerfile based on processing-service pattern in services/ai-search-service/Dockerfile
- [ ] T007 Add face-service to docker-compose.yml (port 8002) in infrastructure/docker/docker-compose.yml
- [ ] T008 Add ai-search-service to docker-compose.yml (port 8009) in infrastructure/docker/docker-compose.yml
- [ ] T009 [P] Create Kafka topics for face.detected and asset.embedding.generated events

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Face Service Foundation

- [ ] T010 Create config.py with Pydantic settings in services/face-service/src/app/core/config.py
- [ ] T011 [P] Create database.py with async SQLAlchemy + pgvector in services/face-service/src/app/core/database.py
- [ ] T012 [P] Create redis.py for caching in services/face-service/src/app/core/redis.py
- [ ] T013 [P] Create circuit_breaker.py for AI API resilience in services/face-service/src/app/core/circuit_breaker.py
- [ ] T014 Create main.py with FastAPI app and lifespan management in services/face-service/src/app/main.py
- [ ] T015 Create event_service.py for Kafka publishing in services/face-service/src/app/services/event_service.py
- [ ] T016 Initialize Alembic for face-service migrations in services/face-service/alembic/

### AI Search Service Foundation

- [ ] T017 Create config.py with Pydantic settings in services/ai-search-service/src/app/core/config.py
- [ ] T018 [P] Create database.py with async SQLAlchemy + pgvector in services/ai-search-service/src/app/core/database.py
- [ ] T019 [P] Create llm.py with Gemini client initialization in services/ai-search-service/src/app/core/llm.py
- [ ] T020 Create main.py with FastAPI app and lifespan management in services/ai-search-service/src/app/main.py
- [ ] T021 Create event_service.py for Kafka publishing in services/ai-search-service/src/app/services/event_service.py
- [ ] T022 Initialize Alembic for ai-search-service migrations in services/ai-search-service/alembic/

### Gallery Service Foundation (Enhancements)

- [ ] T023 Add websockets dependency to gallery-service requirements.txt in services/gallery-service/requirements.txt
- [ ] T024 Create websocket_manager.py for connection management in services/gallery-service/src/app/services/websocket_manager.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Find Photos of a Specific Person (Priority: P1) MVP

**Goal**: Automatically detect and group photos by the people in them so photographers can quickly find all photos of a specific client

**Independent Test**: Upload photos with faces, verify system groups them by person, search for a specific person and retrieve their photos

### Models for User Story 1

- [ ] T025 [P] [US1] Create Face model with bounding_box, confidence, embedding (512-dim) in services/face-service/src/app/models/face.py
- [ ] T026 [P] [US1] Create FaceGroup model with name, workspace_id, representative_face_id in services/face-service/src/app/models/face_group.py
- [ ] T027 [P] [US1] Create FaceEmbedding model with pgvector Vector(512) column in services/face-service/src/app/models/face_embedding.py
- [ ] T028 [US1] Create Alembic migration for Face, FaceGroup, FaceEmbedding tables with IVFFlat index in services/face-service/alembic/versions/001_initial_face_tables.py

### Services for User Story 1

- [ ] T029 [US1] Implement face_detection_service.py using Google Cloud Vision API in services/face-service/src/app/services/face_detection_service.py
- [ ] T030 [US1] Implement embedding_service.py using DeepFace/ArcFace for 512-dim vectors in services/face-service/src/app/services/embedding_service.py
- [ ] T031 [US1] Implement clustering_service.py using DBSCAN with cosine distance in services/face-service/src/app/services/clustering_service.py

### Kafka Consumer for User Story 1

- [ ] T032 [US1] Create asset_face_processor.py consumer for asset.processed events in services/face-service/src/app/consumers/asset_face_processor.py
- [ ] T033 [US1] Implement face detection -> embedding -> clustering pipeline in asset_face_processor.py
- [ ] T034 [US1] Publish face.detected events after processing in asset_face_processor.py

### API Endpoints for User Story 1

- [ ] T035 [P] [US1] Create Pydantic schemas for Face, FaceGroup in services/face-service/src/app/schemas/face.py
- [ ] T036 [US1] Implement GET /api/v1/faces/{asset_id} endpoint in services/face-service/src/app/api/v1/faces.py
- [ ] T037 [US1] Implement GET /api/v1/people endpoint (list groups) in services/face-service/src/app/api/v1/people.py
- [ ] T038 [US1] Implement GET /api/v1/people/{group_id}/photos endpoint in services/face-service/src/app/api/v1/people.py

### Find Me Feature for User Story 1

- [ ] T039 [US1] Implement POST /api/v1/find-me endpoint for selfie matching in services/face-service/src/app/api/v1/find_me.py
- [ ] T040 [US1] Add similarity search using pgvector <=> operator for selfie matching in services/face-service/src/app/services/embedding_service.py

**Checkpoint**: User Story 1 should be fully functional - face detection, grouping, and Find Me working

---

## Phase 4: User Story 2 - Search Photos Using Natural Language (Priority: P1)

**Goal**: Search photo library using natural language queries to find photos without manual tagging

**Independent Test**: Upload photos, query with natural language like "bride throwing bouquet", verify relevant results returned

### Models for User Story 2

- [ ] T041 [P] [US2] Create PhotoEmbedding model with pgvector Vector(1536) for CLIP in services/ai-search-service/src/app/models/photo_embedding.py
- [ ] T042 [US2] Create Alembic migration for PhotoEmbedding table with HNSW index in services/ai-search-service/alembic/versions/001_initial_embedding_tables.py

### Services for User Story 2

- [ ] T043 [US2] Implement embedding_service.py using CLIP ViT-L/14 for 1536-dim vectors in services/ai-search-service/src/app/services/embedding_service.py
- [ ] T044 [US2] Implement search_service.py with pgvector semantic_search function in services/ai-search-service/src/app/services/search_service.py

### Kafka Consumer for User Story 2

- [ ] T045 [US2] Create asset_embedding_processor.py consumer for asset.processed events in services/ai-search-service/src/app/consumers/asset_embedding_processor.py
- [ ] T046 [US2] Implement CLIP embedding generation pipeline in asset_embedding_processor.py
- [ ] T047 [US2] Publish asset.embedding.generated events after processing in asset_embedding_processor.py

### API Endpoints for User Story 2

- [ ] T048 [P] [US2] Create Pydantic schemas for SearchQuery, SearchResult in services/ai-search-service/src/app/schemas/search.py
- [ ] T049 [US2] Implement POST /api/v1/search endpoint for semantic search in services/ai-search-service/src/app/api/v1/search.py
- [ ] T050 [US2] Implement GET /api/v1/similar/{asset_id} endpoint for finding similar photos in services/ai-search-service/src/app/api/v1/search.py

**Checkpoint**: User Story 2 should be fully functional - semantic search returning relevant results

---

## Phase 5: User Story 3 - Ask Questions About My Photos (Priority: P2)

**Goal**: Ask questions about photo library using natural conversation to get insights and recommendations

**Independent Test**: Query system with "What events did I shoot in December?" and verify contextually relevant answers

### Models for User Story 3

- [ ] T051 [P] [US3] Create Conversation model with workspace_id, messages JSONB in services/ai-search-service/src/app/models/conversation.py
- [ ] T052 [US3] Add Conversation table migration in services/ai-search-service/alembic/versions/002_conversation_table.py

### Services for User Story 3

- [ ] T053 [US3] Implement rag_service.py using LangChain + Gemini 2.5 Flash in services/ai-search-service/src/app/services/rag_service.py
- [ ] T054 [US3] Implement conversation context management in rag_service.py
- [ ] T055 [US3] Implement photo retrieval for RAG context using semantic search in rag_service.py

### API Endpoints for User Story 3

- [ ] T056 [P] [US3] Create Pydantic schemas for ChatRequest, ChatResponse in services/ai-search-service/src/app/schemas/chat.py
- [ ] T057 [US3] Implement POST /api/v1/chat endpoint for RAG conversations in services/ai-search-service/src/app/api/v1/chat.py
- [ ] T058 [US3] Implement GET /api/v1/chat/{conversation_id} endpoint for history in services/ai-search-service/src/app/api/v1/chat.py

**Checkpoint**: User Story 3 should be fully functional - RAG conversations working with context

---

## Phase 6: User Story 4 - View Public Gallery (Priority: P1)

**Goal**: View shared photo gallery without creating an account via magic links

**Independent Test**: Create gallery, publish with magic link, verify anonymous access works with real-time updates

**Note**: Gallery Service already exists - this phase adds WebSocket real-time updates

### Services for User Story 4

- [ ] T059 [US4] Implement gallery_update_handler.py consumer for gallery events in services/gallery-service/src/app/consumers/gallery_update_handler.py
- [ ] T060 [US4] Add Redis Pub/Sub integration to websocket_manager.py in services/gallery-service/src/app/services/websocket_manager.py

### API Endpoints for User Story 4

- [ ] T061 [P] [US4] Create Pydantic schemas for WebSocket messages in services/gallery-service/src/app/schemas/websocket.py
- [ ] T062 [US4] Implement WS /api/v1/ws/gallery/{gallery_id} endpoint in services/gallery-service/src/app/api/v1/websocket.py
- [ ] T063 [US4] Add authentication for WebSocket connections (magic link token) in services/gallery-service/src/app/api/v1/websocket.py
- [ ] T064 [US4] Implement real-time photo added/removed notifications in websocket_manager.py

**Checkpoint**: User Story 4 should be fully functional - real-time gallery updates via WebSocket

---

## Phase 7: User Story 5 - Receive Intelligent Caption Suggestions (Priority: P2)

**Goal**: Get AI-generated caption suggestions for photos to improve SEO and client delivery

**Independent Test**: Upload photos and verify system generates contextually appropriate caption suggestions

### Models for User Story 5

- [ ] T065 [P] [US5] Create Caption model with asset_id, suggestions JSONB, style in services/ai-search-service/src/app/models/caption.py
- [ ] T066 [US5] Add Caption table migration in services/ai-search-service/alembic/versions/003_caption_table.py

### Services for User Story 5

- [ ] T067 [US5] Implement caption_service.py using Gemini for caption generation in services/ai-search-service/src/app/services/caption_service.py
- [ ] T068 [US5] Add event context extraction for better captions (wedding, portrait, etc.) in caption_service.py

### API Endpoints for User Story 5

- [ ] T069 [P] [US5] Create Pydantic schemas for CaptionRequest, CaptionSuggestion in services/ai-search-service/src/app/schemas/caption.py
- [ ] T070 [US5] Implement POST /api/v1/captions/{asset_id} endpoint in services/ai-search-service/src/app/api/v1/captions.py
- [ ] T071 [US5] Add caption regeneration support for alternative suggestions in services/ai-search-service/src/app/api/v1/captions.py

**Checkpoint**: User Story 5 should be fully functional - caption suggestions generated for photos

---

## Phase 8: User Story 6 - Manage People Groups (Priority: P2)

**Goal**: Manage and merge people groups to correct misidentified faces and organize contacts

**Independent Test**: View people groups, perform merge/split operations, verify changes persist

### Services for User Story 6

- [ ] T072 [US6] Add merge_groups() method to clustering_service.py in services/face-service/src/app/services/clustering_service.py
- [ ] T073 [US6] Add split_group() method to clustering_service.py in services/face-service/src/app/services/clustering_service.py

### API Endpoints for User Story 6

- [ ] T074 [P] [US6] Create Pydantic schemas for MergeRequest, SplitRequest in services/face-service/src/app/schemas/people.py
- [ ] T075 [US6] Implement POST /api/v1/people/merge endpoint in services/face-service/src/app/api/v1/people.py
- [ ] T076 [US6] Implement POST /api/v1/people/split endpoint in services/face-service/src/app/api/v1/people.py
- [ ] T077 [US6] Implement PATCH /api/v1/people/{group_id} for naming groups in services/face-service/src/app/api/v1/people.py

**Checkpoint**: User Story 6 should be fully functional - merge/split/name operations working

---

## Phase 9: User Story 7 - Preview Client Gallery (Priority: P2)

**Goal**: Preview how clients will see a gallery before publishing

**Independent Test**: Enter preview mode and verify view matches client experience

### Services for User Story 7

- [ ] T078 [US7] Implement preview_service.py for preview state management in services/gallery-service/src/app/services/preview_service.py

### API Endpoints for User Story 7

- [ ] T079 [P] [US7] Create Pydantic schemas for PreviewRequest, PreviewResponse in services/gallery-service/src/app/schemas/preview.py
- [ ] T080 [US7] Implement GET /api/v1/preview/{gallery_id} endpoint in services/gallery-service/src/app/api/v1/preview.py
- [ ] T081 [US7] Implement POST /api/v1/preview/{gallery_id}/toggle endpoint in services/gallery-service/src/app/api/v1/preview.py

**Checkpoint**: User Story 7 should be fully functional - preview mode toggling works

---

## Phase 10: User Story 8 - Batch Operations on Gallery Photos (Priority: P3)

**Goal**: Perform batch operations on gallery photos for efficient management of large galleries

**Independent Test**: Select multiple photos, perform batch download/move/delete, verify operations complete

### Services for User Story 8

- [ ] T082 [US8] Implement batch_service.py for batch operation orchestration in services/gallery-service/src/app/services/batch_service.py
- [ ] T083 [US8] Add batch download with ZIP packaging in batch_service.py
- [ ] T084 [US8] Add batch move between galleries in batch_service.py
- [ ] T085 [US8] Add batch delete with confirmation in batch_service.py

### API Endpoints for User Story 8

- [ ] T086 [P] [US8] Create Pydantic schemas for BatchRequest, BatchProgress in services/gallery-service/src/app/schemas/batch.py
- [ ] T087 [US8] Implement POST /api/v1/batch/download endpoint in services/gallery-service/src/app/api/v1/batch.py
- [ ] T088 [US8] Implement POST /api/v1/batch/move endpoint in services/gallery-service/src/app/api/v1/batch.py
- [ ] T089 [US8] Implement DELETE /api/v1/batch endpoint in services/gallery-service/src/app/api/v1/batch.py
- [ ] T090 [US8] Add WebSocket progress notifications for batch operations in batch_service.py

**Checkpoint**: User Story 8 should be fully functional - all batch operations working

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Observability

- [ ] T091 [P] Add Prometheus metrics to face-service in services/face-service/src/app/core/metrics.py
- [ ] T092 [P] Add Prometheus metrics to ai-search-service in services/ai-search-service/src/app/core/metrics.py
- [ ] T093 [P] Add Sentry integration to face-service in services/face-service/src/app/main.py
- [ ] T094 [P] Add Sentry integration to ai-search-service in services/ai-search-service/src/app/main.py

### Kubernetes & Scaling

- [ ] T095 [P] Create face-service Kubernetes deployment in infrastructure/kubernetes/base/services/face-service/deployment.yaml
- [ ] T096 [P] Create ai-search-service Kubernetes deployment in infrastructure/kubernetes/base/services/ai-search-service/deployment.yaml
- [ ] T097 [P] Create KEDA ScaledObject for face-service in infrastructure/kubernetes/keda/face-service-scaledobject.yaml
- [ ] T098 [P] Create KEDA ScaledObject for ai-search-service in infrastructure/kubernetes/keda/ai-search-service-scaledobject.yaml
- [ ] T099 Update gallery-service KEDA config for WebSocket scaling in infrastructure/kubernetes/base/keda/scaledobjects.yaml

### Testing & Documentation

- [ ] T100 [P] Create unit tests for embedding_service.py in services/face-service/tests/unit/test_embedding_service.py
- [ ] T101 [P] Create unit tests for clustering_service.py in services/face-service/tests/unit/test_clustering_service.py
- [ ] T102 [P] Create unit tests for search_service.py in services/ai-search-service/tests/unit/test_search_service.py
- [ ] T103 [P] Create integration test for face detection pipeline in services/face-service/tests/integration/test_face_pipeline.py
- [ ] T104 [P] Create integration test for semantic search in services/ai-search-service/tests/integration/test_search.py
- [ ] T105 Validate quickstart.md test scenarios work end-to-end

---

## Summary

| Category | Count |
|----------|-------|
| **Total Tasks** | 105 |
| **Setup Tasks** | 9 |
| **Foundational Tasks** | 15 |
| **US1 Tasks (P1)** | 16 |
| **US2 Tasks (P1)** | 10 |
| **US3 Tasks (P2)** | 8 |
| **US4 Tasks (P1)** | 6 |
| **US5 Tasks (P2)** | 7 |
| **US6 Tasks (P2)** | 6 |
| **US7 Tasks (P2)** | 4 |
| **US8 Tasks (P3)** | 9 |
| **Polish Tasks** | 15 |
| **Parallel Opportunities** | 38 tasks marked [P] |

**MVP Scope**: 56 tasks (Setup + Foundation + US1 + US2 + US4)
