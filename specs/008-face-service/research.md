# Research: Face Service

**Feature**: 008-face-service
**Date**: 2026-01-16
**Status**: Complete

## Executive Summary

The Face Service is substantially implemented in `services/face-service/`. This research documents the existing architecture, validates design decisions against industry best practices, and identifies optimization opportunities.

## Technology Decisions

### 1. Face Detection Provider

**Decision**: Google Cloud Vision API
**Rationale**:
- High accuracy for face detection
- Provides bounding boxes, landmarks, and emotional attributes
- Scalable and reliable enterprise service
- Already integrated in RawDrive

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| AWS Rekognition | Higher latency, less accurate landmarks |
| Local DeepFace | Higher infrastructure cost, maintenance burden |
| Gemini Flash | Planned as fallback (Phase 2) |

### 2. Face Embeddings

**Decision**: ArcFace via DeepFace library, 512 dimensions
**Rationale**:
- Industry standard for face recognition (99%+ accuracy)
- Optimal balance of accuracy vs storage (2KB per face)
- L2-normalized for efficient cosine similarity
- Well-supported in production environments

**Configuration**:
```
FACE_EMBEDDING_DIMENSION=512
Model: ArcFace backbone
Normalization: L2 (unit vectors)
```

### 3. Vector Storage & Indexing

**Decision**: PostgreSQL pgvector with IVFFlat index (lists=100)
**Rationale**:
- Native integration with existing PostgreSQL stack
- IVFFlat provides 95-98% recall with fast queries
- Consistent with RawDrive's database architecture
- lists=100 optimal for up to 100K faces

**Scaling Path**:
| Dataset Size | Index Strategy |
|--------------|----------------|
| < 100K faces | IVFFlat (current) |
| 100K - 1M | Increase lists to 200-500 |
| > 1M faces | Migrate to HNSW |

### 4. Face Clustering

**Decision**: DBSCAN with cosine distance
**Rationale**:
- Handles variable-size clusters naturally
- No need to pre-specify cluster count
- Identifies noise/outliers
- Supports incremental assignment

**Parameters**:
```
DBSCAN_EPS=0.5         # Cosine distance threshold (~50% similarity)
DBSCAN_MIN_SAMPLES=2   # Minimum faces for a group
```

**Tuning Recommendations**:
| Use Case | eps Value | Trade-off |
|----------|-----------|-----------|
| High precision (fewer false merges) | 0.35-0.40 | More manual merging needed |
| Balanced (current) | 0.45-0.50 | Good default |
| High recall (fewer missed matches) | 0.55-0.60 | More false positives |

**Note**: Consider A/B testing eps=0.40 for stricter grouping.

### 5. Event Processing

**Decision**: Kafka for async face processing
**Rationale**:
- Decouples upload from processing (non-blocking)
- Enables horizontal scaling with KEDA
- Partition by workspace_id for multi-tenancy
- Reliable delivery with manual commit

**Events**:
| Event | Direction | Topic |
|-------|-----------|-------|
| asset.processed | Consumed | asset.processed |
| face.detected | Published | face.detected |

### 6. Circuit Breaker Pattern

**Decision**: Custom async circuit breaker for external APIs
**Rationale**:
- Prevents cascade failures from Google Vision outages
- Auto-recovery with half-open state testing
- Per-API circuit isolation

**Configuration**:
```
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60s
```

**Enhancement (Phase 2)**: Add Gemini Flash as fallback provider.

## Key Implementation Details

### Database Schema

**Tables**:
1. `faces` - Individual face detections
2. `face_embeddings` - 512-dim vectors with IVFFlat index
3. `face_groups` - Person clusters with denormalized counts

**Multi-tenancy**: All tables include `workspace_id` with composite indexes.

### API Structure

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| Faces | /api/v1/faces | Get faces by asset/workspace |
| People | /api/v1/people | CRUD for person groups, merge/split |
| Find Me | /api/v1/find-me | Selfie search via file upload |

### Performance Characteristics

| Metric | Target | Design |
|--------|--------|--------|
| Face detection | < 30s | Async Kafka processing |
| Find Me search | < 5s | IVFFlat ANN search |
| Concurrent images | 1,000+ | KEDA autoscaling (2-50 replicas) |

### Resilience Patterns

1. **Idempotency**: Redis-based with 24-hour expiry
2. **Circuit breaker**: Failure threshold 5, recovery 60s
3. **Graceful degradation**: Service continues without Redis
4. **Manual commit**: Kafka messages committed after processing

## Existing Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Database models | Complete | services/face-service/src/app/models/ |
| API endpoints | Complete | services/face-service/src/app/api/v1/ |
| Face detection | Complete | services/face-service/src/app/services/face_detection_service.py |
| Embedding generation | Complete | services/face-service/src/app/services/embedding_service.py |
| Clustering | Complete | services/face-service/src/app/services/clustering_service.py |
| Kafka consumer | Complete | services/face-service/src/app/consumers/ |
| Circuit breaker | Complete | services/face-service/src/app/core/circuit_breaker.py |
| Unit tests | Partial | services/face-service/tests/ |

## Identified Gaps & Enhancements

### Gap 1: Integration Testing
**Current**: Basic unit tests with mocks
**Needed**: End-to-end integration tests with real Kafka/Redis

### Gap 2: Provider Fallback
**Current**: Single provider (Google Vision)
**Needed**: Gemini Flash as fallback when circuit opens

### Gap 3: Cluster Quality Metrics
**Current**: No cohesion tracking
**Needed**: Metrics to identify low-quality clusters for user review

### Gap 4: Processing Status API
**Current**: No real-time progress endpoint
**Needed**: WebSocket or polling endpoint for batch progress

## Dependencies (versions from requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.0 | Web framework |
| aiokafka | 0.10.0 | Async Kafka client |
| pgvector | 0.2.4 | Vector storage |
| deepface | 0.0.79 | Face embeddings |
| google-cloud-vision | 3.5.0 | Face detection |
| scikit-learn | 1.4.0 | DBSCAN clustering |
| redis | 5.0.1 | Idempotency cache |

## Recommendations

### Immediate (This Sprint)
1. Document existing API contracts in OpenAPI format
2. Add integration test coverage
3. Validate DBSCAN eps=0.5 against sample dataset

### Short-term (Next Quarter)
1. Implement group cohesion metrics
2. Add processing status WebSocket endpoint
3. A/B test stricter clustering (eps=0.40)

### Long-term (This Year)
1. Add Gemini Flash as fallback provider
2. Plan HNSW migration for >100K faces
3. Implement online learning from user corrections

## References

- Existing docs: docs/Features/FaceDetectionIdentification.md
- Requirements: docs/Features/FaceRecognizationRequiremtns.md
- API contracts: docs/Plan/contracts/faces.yaml
