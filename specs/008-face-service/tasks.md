# Tasks: Face Service

**Input**: Design documents from `/specs/008-face-service/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Implementation Status**: The Face Service is **substantially implemented** in `services/face-service/`. These tasks focus on identified gaps and production readiness improvements, not reimplementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing implementation and prepare test infrastructure

- [ ] T001 Verify face-service Docker container builds successfully: `docker compose build face-service`
- [ ] T002 [P] Verify database migrations are up-to-date: `alembic upgrade head` in services/face-service/
- [ ] T003 [P] Verify pgvector extension is installed with IVFFlat index
- [ ] T004 Create test fixtures for Kafka events in services/face-service/tests/fixtures/kafka_events.json

---

## Phase 2: Foundational - Integration Test Infrastructure (P1)

**Purpose**: Build robust integration test framework for Kafka/Redis flows

**Gap Addressed**: "Integration tests with real Kafka/Redis" (P1 priority)

- [ ] T005 Create pytest fixtures for Kafka producer/consumer in services/face-service/tests/conftest.py
- [ ] T006 [P] Create pytest fixtures for Redis connection in services/face-service/tests/conftest.py
- [ ] T007 [P] Create test database fixtures with pgvector in services/face-service/tests/conftest.py
- [ ] T008 Configure docker-compose.test.yml for isolated integration testing environment
- [ ] T009 Create helper utilities for event assertions in services/face-service/tests/utils/kafka_helpers.py

**Checkpoint**: Integration test infrastructure is ready for all user story tests

---

## Phase 3: User Story 1 - Face Detection (Priority: P1)

**Goal**: Ensure face detection works reliably with proper integration testing

**Independent Test**: Publish asset.processed event, verify face.detected event is produced

### Integration Tests for US1

- [ ] T010 [P] [US1] Create integration test for face detection Kafka flow in services/face-service/tests/integration/test_face_detection_pipeline.py
- [ ] T011 [P] [US1] Create integration test for idempotency with Redis in services/face-service/tests/integration/test_idempotency.py
- [ ] T012 [US1] Create integration test for circuit breaker behavior in services/face-service/tests/integration/test_circuit_breaker.py

### Implementation Verification for US1

- [ ] T013 [US1] Verify face detection consumer handles edge cases (no faces, many faces, invalid images) in services/face-service/src/app/consumers/asset_face_processor.py
- [ ] T014 [US1] Add retry queue integration for failed detections in services/face-service/src/app/services/retry_service.py

**Checkpoint**: Face detection pipeline is fully tested with Kafka/Redis integration

---

## Phase 4: User Story 2 - Face Clustering (Priority: P1)

**Goal**: Validate clustering accuracy and add cohesion metrics

**Independent Test**: Upload 5 photos of same person, verify automatic grouping

### Integration Tests for US2

- [ ] T015 [P] [US2] Create integration test for incremental clustering in services/face-service/tests/integration/test_clustering_pipeline.py
- [ ] T016 [P] [US2] Create unit tests for DBSCAN parameter tuning (eps=0.40 vs 0.50) in services/face-service/tests/unit/test_clustering_accuracy.py

### Implementation for US2 - Group Cohesion Metrics (P3 Gap)

- [ ] T017 [US2] Implement group cohesion score calculation in services/face-service/src/app/services/cohesion_service.py
- [ ] T018 [US2] Add cohesion_score field to FaceGroup model in services/face-service/src/app/models/face_group.py
- [ ] T019 [US2] Create Alembic migration for cohesion_score column in services/face-service/alembic/versions/
- [ ] T020 [US2] Add cohesion score to GET /people response in services/face-service/src/app/api/v1/people.py
- [ ] T021 [US2] Add Prometheus metric for average cohesion score per workspace

**Checkpoint**: Clustering is tested and includes cohesion metrics for quality monitoring

---

## Phase 5: User Story 3 - People Management (Priority: P2)

**Goal**: Ensure merge/split operations work correctly

**Independent Test**: Merge two person groups, verify faces are combined

### Integration Tests for US3

- [ ] T022 [P] [US3] Create integration test for merge operation in services/face-service/tests/integration/test_people_merge.py
- [ ] T023 [P] [US3] Create integration test for split operation in services/face-service/tests/integration/test_people_split.py
- [ ] T024 [US3] Create integration test for name persistence in services/face-service/tests/integration/test_people_naming.py

### Implementation Verification for US3

- [ ] T025 [US3] Verify representative face updates after merge/split in services/face-service/src/app/services/clustering_service.py
- [ ] T026 [US3] Add face count denormalization trigger validation

**Checkpoint**: People management operations are fully tested

---

## Phase 6: User Story 4 - Find Me (Priority: P2)

**Goal**: Ensure Find Me search performs within 5s for large galleries

**Independent Test**: Upload selfie, verify matching photos returned within 5 seconds

### Integration Tests for US4

- [ ] T027 [P] [US4] Create integration test for Find Me search in services/face-service/tests/integration/test_find_me.py
- [ ] T028 [P] [US4] Create performance test for 10K photo gallery in services/face-service/tests/performance/test_find_me_performance.py

### Implementation for US4 - Provider Fallback (P3 Gap)

- [ ] T029 [US4] Create Gemini Flash face detection provider in services/face-service/src/app/services/providers/gemini_provider.py
- [ ] T030 [US4] Implement provider abstraction interface in services/face-service/src/app/services/providers/base_provider.py
- [ ] T031 [US4] Refactor face_detection_service.py to use provider abstraction
- [ ] T032 [US4] Add automatic fallback logic when Google Vision circuit breaker opens
- [ ] T033 [US4] Add GEMINI_API_KEY environment variable to config in services/face-service/src/app/core/config.py

**Checkpoint**: Find Me is tested and has fallback provider for resilience

---

## Phase 7: User Story 5 - Person Photo Browser (Priority: P3)

**Goal**: Enable efficient browsing of photos by person

**Independent Test**: Select a person, verify all their photos are returned with pagination

### Integration Tests for US5

- [ ] T034 [P] [US5] Create integration test for person photo listing in services/face-service/tests/integration/test_person_photos.py
- [ ] T035 [US5] Create test for large person groups (100+ photos) pagination

### Implementation for US5

- [ ] T036 [US5] Add GET /people/{group_id}/photos endpoint in services/face-service/src/app/api/v1/people.py
- [ ] T037 [US5] Add cursor-based pagination for photo listing
- [ ] T038 [US5] Add photos count to person group response schema

**Checkpoint**: Person photo browser is functional and tested

---

## Phase 8: User Story 6 - Processing Status (Priority: P3)

**Goal**: Provide real-time processing status updates

**Independent Test**: Upload 10 photos, verify progress updates in real-time

### Implementation for US6 - WebSocket Endpoint (P2 Gap)

- [ ] T039 [US6] Create WebSocket endpoint for processing status in services/face-service/src/app/api/v1/websocket.py
- [ ] T040 [US6] Create processing status schema in services/face-service/src/app/schemas/processing_status.py
- [ ] T041 [US6] Implement status tracking in Redis with workspace/batch keys
- [ ] T042 [US6] Publish status updates from Kafka consumer to WebSocket
- [ ] T043 [US6] Add connection manager for WebSocket sessions in services/face-service/src/app/core/websocket_manager.py

### Integration Tests for US6

- [ ] T044 [P] [US6] Create WebSocket integration test in services/face-service/tests/integration/test_websocket_status.py
- [ ] T045 [US6] Create test for batch processing status updates

**Checkpoint**: Processing status WebSocket is functional and tested

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, documentation, and performance

### Documentation

- [ ] T046 [P] Update quickstart.md with WebSocket usage examples
- [ ] T047 [P] Add provider fallback documentation to research.md
- [ ] T048 [P] Update OpenAPI spec with new endpoints (photos, websocket) in contracts/face-service-openapi.yaml

### Performance & Monitoring

- [ ] T049 [P] Add Prometheus metrics for processing pipeline latency
- [ ] T050 [P] Add Prometheus metrics for provider fallback events
- [ ] T051 Create performance baseline test suite in services/face-service/tests/performance/

### Future-Proofing (P4 - HNSW Migration)

- [ ] T052 [P] Document HNSW migration strategy in research.md
- [ ] T053 Create migration script template for IVFFlat to HNSW in services/face-service/scripts/migrate_to_hnsw.py
- [ ] T054 Add index type configuration to environment variables

### Security Hardening

- [ ] T055 [P] Verify workspace isolation in all new endpoints
- [ ] T056 [P] Add rate limiting to Find Me endpoint
- [ ] T057 Validate JWT tokens on WebSocket connections

### Final Validation

- [ ] T058 Run full integration test suite: `pytest tests/integration/ -v`
- [ ] T059 Run quickstart.md validation manually
- [ ] T060 Verify all success criteria from spec.md can be measured

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user story tests
- **User Stories (Phases 3-8)**: All depend on Phase 2 completion
  - US1 (Phase 3) and US2 (Phase 4) can run in parallel
  - US3 and US4 can start after Phase 2
  - US5 depends on People endpoints (Phase 5)
  - US6 (WebSocket) is independent
- **Phase 9 (Polish)**: Depends on all user stories being complete

### Within Each User Story

- Integration tests should verify existing implementation
- Gap implementations (cohesion, WebSocket, provider fallback) are new work
- Models before services before endpoints
- Tests before implementation for new features

### Parallel Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003 |
| Phase 2 | T005, T006, T007 |
| Phase 3 | T010, T011 |
| Phase 4 | T015, T016 |
| Phase 5 | T022, T023 |
| Phase 6 | T027, T028 |
| Phase 7 | T034 |
| Phase 8 | T039-T043 (sequential), T044 |
| Phase 9 | T046, T047, T048, T049, T050, T052, T055, T056 |

---

## Implementation Strategy

### Recommended Order (MVP Focus)

1. **Week 1**: Complete Phases 1-2 (test infrastructure)
2. **Week 2**: Complete Phases 3-4 (P1 user stories - Detection & Clustering)
3. **Week 3**: Complete Phases 5-6 (P2 user stories - People & Find Me)
4. **Week 4**: Complete Phases 7-8 (P3 user stories - Browser & Status)
5. **Week 5**: Complete Phase 9 (Polish)

### Gap Priority

| Gap | Phase | Priority | Impact |
|-----|-------|----------|--------|
| Integration tests | 2-8 | P1 | Production confidence |
| WebSocket status | 8 | P2 | User experience |
| Group cohesion metrics | 4 | P3 | Quality monitoring |
| Provider fallback | 6 | P3 | Resilience |
| HNSW migration | 9 | P4 | Future scale |

---

## Notes

- Most core functionality already exists - focus on testing and gaps
- [P] tasks can run in parallel within their phase
- Commit after each task or logical group
- Run `pytest tests/unit/` after each implementation change
- Success criteria from spec.md should be verifiable after Phase 9
