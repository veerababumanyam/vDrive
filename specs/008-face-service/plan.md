# Implementation Plan: Face Service

**Branch**: `008-face-service` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-face-service/spec.md`

## Summary

The Face Service provides automatic face detection, recognition, and organization for RawDrive photography platform. Key capabilities:

- **Face Detection**: Google Cloud Vision API for detection, bounding boxes, landmarks
- **Face Embeddings**: 512-dim ArcFace vectors via DeepFace for similarity matching
- **Face Clustering**: DBSCAN algorithm for automatic person grouping
- **Find Me**: Selfie search for clients to find their photos
- **People Management**: View, name, merge, split person groups

**Implementation Status**: The service is substantially implemented in `services/face-service/`. This plan documents the existing architecture and identifies remaining work for production readiness.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI 0.109.0, DeepFace 0.0.79, google-cloud-vision 3.5.0, scikit-learn 1.4.0, aiokafka 0.10.0
**Storage**: PostgreSQL 16 + pgvector 0.2.4, Redis 7
**Testing**: pytest 7.4.4, pytest-asyncio 0.23.3
**Target Platform**: Linux containers (Docker/Kubernetes)
**Project Type**: Microservice (backend API + Kafka consumer)
**Performance Goals**: <30s face detection, <5s Find Me search, 1000 concurrent images
**Constraints**: <2GB memory per replica, 95%+ availability
**Scale/Scope**: 2-50 replicas via KEDA, up to 100K faces per workspace

## Constitution Check

*GATE: The project constitution is a template without specific gates. No violations.*

**Post-Design Check**: ✓ PASS
- Architecture follows RawDrive microservice patterns
- Multi-tenancy via workspace_id isolation
- Event-driven async processing
- Standard observability (Prometheus, Sentry)

## Project Structure

### Documentation (this feature)

```text
specs/008-face-service/
├── plan.md              # This file
├── research.md          # Technology decisions and best practices
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Development setup guide
├── contracts/
│   ├── face-service-openapi.yaml  # REST API contract
│   └── kafka-events.yaml          # Kafka event schemas
└── tasks.md             # Implementation tasks (via /speckit.tasks)
```

### Source Code (existing implementation)

```text
services/face-service/
├── src/app/
│   ├── api/v1/
│   │   ├── faces.py         # Face retrieval endpoints
│   │   ├── people.py        # Person group management
│   │   └── find_me.py       # Selfie search endpoint
│   ├── consumers/
│   │   └── asset_face_processor.py  # Kafka consumer
│   ├── core/
│   │   ├── config.py        # Service configuration
│   │   ├── database.py      # Async SQLAlchemy setup
│   │   └── circuit_breaker.py  # External API resilience
│   ├── models/
│   │   ├── face.py          # Face entity
│   │   ├── face_embedding.py # Vector storage
│   │   └── face_group.py    # Person groups
│   ├── schemas/
│   │   └── *.py             # Pydantic request/response models
│   ├── services/
│   │   ├── face_detection_service.py  # Google Vision API
│   │   ├── embedding_service.py       # ArcFace embeddings
│   │   └── clustering_service.py      # DBSCAN clustering
│   └── main.py              # FastAPI application
├── alembic/
│   └── versions/            # Database migrations
├── tests/
│   ├── unit/               # Unit tests with mocks
│   └── integration/        # E2E pipeline tests
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

**Structure Decision**: Microservice pattern - standalone Python service with API, Kafka consumer, and dedicated database tables. Follows existing RawDrive service conventions.

## Implementation Overview

### Implemented (Ready for Review)

| Component | Location | Status |
|-----------|----------|--------|
| Database Models | models/*.py | ✓ Complete |
| API Endpoints | api/v1/*.py | ✓ Complete |
| Face Detection | services/face_detection_service.py | ✓ Complete |
| Embeddings | services/embedding_service.py | ✓ Complete |
| Clustering | services/clustering_service.py | ✓ Complete |
| Kafka Consumer | consumers/asset_face_processor.py | ✓ Complete |
| Circuit Breaker | core/circuit_breaker.py | ✓ Complete |
| Unit Tests | tests/unit/*.py | ⚠ Partial |

### Gaps to Address

| Gap | Priority | Effort |
|-----|----------|--------|
| Integration tests with real Kafka/Redis | P1 | Medium |
| Processing status WebSocket endpoint | P2 | Medium |
| Group cohesion metrics | P3 | Low |
| Provider fallback (Gemini Flash) | P3 | Medium |
| HNSW migration path (>100K faces) | P4 | High |

## Key Design Decisions

### 1. Vector Storage

**Decision**: PostgreSQL pgvector with IVFFlat index (lists=100)
**Trade-off**: Slightly lower recall (~95%) vs faster queries
**Migration Path**: HNSW for >100K faces

### 2. Clustering Algorithm

**Decision**: DBSCAN with eps=0.5, min_samples=2
**Trade-off**: Current eps may be too loose (5% false merge risk)
**Recommendation**: A/B test eps=0.40 for stricter matching

### 3. External API Resilience

**Decision**: Custom circuit breaker (5 failures, 60s recovery)
**Enhancement**: Add Gemini Flash as fallback provider

### 4. Multi-Tenancy

**Decision**: workspace_id isolation at query level, Kafka partition key
**Enforcement**: All queries, indexes, and events include workspace_id

## Verification Plan

### Unit Tests
```bash
cd services/face-service
pytest tests/unit/ -v
```

### Integration Tests
```bash
# With Docker dependencies running
pytest tests/integration/ -v
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8002/health

# List people
curl "http://localhost:8002/api/v1/people?workspace_id=<ws>&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Kafka Event Testing
```bash
# Produce test event
docker compose exec kafka kafka-console-producer.sh \
  --broker-list localhost:9092 \
  --topic asset.processed
```

### Performance Testing
- Face detection: Target <30s per image
- Find Me: Target <5s for 10K photo gallery
- Concurrent load: 1000 images without degradation

## Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| PostgreSQL + pgvector | Yes | Face/embedding storage |
| Redis | Optional | Idempotency (graceful degradation) |
| Kafka | Yes | Event-driven processing |
| Google Cloud Vision | Yes* | Face detection (*can mock for dev) |
| Upload Service | Yes | Produces asset.processed events |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Google Vision rate limits | Medium | High | Circuit breaker + retry queue |
| Clustering false positives | Medium | Medium | Tunable eps, manual merge/split |
| Large workspace performance | Low | High | HNSW migration plan ready |
| Redis unavailability | Low | Low | Graceful degradation implemented |

## Next Steps

1. **Run `/speckit.tasks`** to generate detailed implementation tasks
2. **Review existing code** against spec requirements
3. **Add integration tests** for Kafka/Redis flows
4. **A/B test clustering** with eps=0.40 on sample dataset
5. **Document Find Me** in user-facing documentation

## References

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Technology decisions
- [data-model.md](./data-model.md) - Entity definitions
- [quickstart.md](./quickstart.md) - Development setup
- [contracts/face-service-openapi.yaml](./contracts/face-service-openapi.yaml) - API contract
- [contracts/kafka-events.yaml](./contracts/kafka-events.yaml) - Event schemas
