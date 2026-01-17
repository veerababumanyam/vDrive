# Implementation Plan: Storage & Media Processing

**Branch**: `005-upload-media-processing` | **Date**: 2026-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-upload-media-processing/spec.md`

## Summary

Implement a TUS v1.0.0 compliant Upload Service (port 8008) with AES-256-GCM encryption, Cloudflare R2 storage, and Kafka event publishing. Processing is handled by Kafka consumers (not Celery) for thumbnail generation, EXIF extraction, and Google Cloud Vision face detection.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, tuspyserver, cryptography, Pillow, rawpy, ffmpeg-python, ExifRead, google-cloud-vision, aiokafka, boto3
**Storage**: PostgreSQL 16 (pgvector), Redis 7, Cloudflare R2
**Testing**: pytest, pytest-asyncio, pytest-cov
**Target Platform**: Linux containers (Docker/Kubernetes)
**Project Type**: Web microservices
**Performance Goals**: 1000 concurrent uploads, 30s processing time per asset
**Constraints**: <300ms upload endpoint latency, 10GB max file size
**Scale/Scope**: 10k workspaces, 1M assets

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Multi-tenancy | PASS | All entities include workspace_id FK, partition key in Kafka |
| Error Handling | PASS | All error cases documented, DLQ pattern for failed processing |
| Security | PASS | AES-256-GCM encryption, JWT auth, workspace isolation |
| Testing | PASS | Unit, integration, and load test requirements defined |
| Observability | PASS | Prometheus metrics, structured logging |

## Project Structure

### Documentation (this feature)

```text
specs/005-upload-media-processing/
├── plan.md              # This file
├── research.md          # Technology decisions (complete)
├── data-model.md        # Database schema (complete)
├── quickstart.md        # Development setup (complete)
├── contracts/           # API contracts
│   ├── upload-service-openapi.yaml   # TUS + REST API
│   └── kafka-events.yaml             # Event schemas
└── tasks.md             # Implementation tasks (via /speckit.tasks)
```

### Source Code (repository root)

```text
services/
├── upload-service/                    # NEW - TUS upload handling
│   ├── src/app/
│   │   ├── main.py                    # FastAPI app, TUS router
│   │   ├── core/
│   │   │   ├── config.py              # Settings (Pydantic)
│   │   │   ├── database.py            # SQLAlchemy async
│   │   │   ├── redis.py               # Upload state cache
│   │   │   └── logging.py             # Structlog
│   │   ├── api/v1/
│   │   │   ├── tus.py                 # TUS protocol endpoints
│   │   │   ├── uploads.py             # Upload management
│   │   │   └── assets.py              # Asset retrieval
│   │   ├── services/
│   │   │   ├── upload_service.py      # Upload orchestration
│   │   │   ├── encryption_service.py  # AES-256-GCM
│   │   │   ├── storage_service.py     # R2 multipart upload
│   │   │   └── event_service.py       # Kafka publishing
│   │   ├── models/
│   │   │   ├── upload.py              # Upload entity
│   │   │   ├── asset.py               # Asset entity
│   │   │   └── encryption_key.py      # Key rotation
│   │   └── schemas/
│   │       ├── upload.py              # Pydantic schemas
│   │       └── events.py              # Kafka event schemas
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── alembic/                       # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
└── processing-service/                # NEW - Kafka consumers
    ├── src/app/
    │   ├── main.py                    # Consumer runner
    │   ├── core/
    │   │   ├── config.py
    │   │   └── metrics.py             # Prometheus
    │   ├── consumers/
    │   │   ├── base_consumer.py       # Retry logic, DLQ
    │   │   ├── asset_processor.py     # Thumbnails, EXIF
    │   │   ├── face_detector.py       # GCV integration
    │   │   └── notification_sender.py
    │   └── services/
    │       ├── thumbnail_service.py   # Pillow/rawpy/ffmpeg
    │       ├── exif_service.py        # ExifRead
    │       └── face_service.py        # google-cloud-vision
    ├── tests/
    ├── requirements.txt
    └── Dockerfile
```

**Structure Decision**: Two separate microservices - upload-service handles HTTP/TUS protocol, processing-service handles async Kafka consumers. This separation allows independent scaling and deployment.

## Complexity Tracking

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|-------------------------------------|
| Kafka consumers over Celery | Aligns with existing event architecture | Celery would add dual-system complexity |
| Separate processing-service | Independent scaling of CPU-intensive tasks | Coupling processing to upload service would block uploads |
| Custom R2 storage backend | tuspyserver only supports local filesystem | No existing R2 TUS implementation available |

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](./research.md) | Complete |
| Data Model | [data-model.md](./data-model.md) | Complete |
| OpenAPI Spec | [contracts/upload-service-openapi.yaml](./contracts/upload-service-openapi.yaml) | Complete |
| Kafka Events | [contracts/kafka-events.yaml](./contracts/kafka-events.yaml) | Complete |
| Quickstart | [quickstart.md](./quickstart.md) | Complete |

## Key Decisions

### 1. TUS Protocol Implementation
- **Choice**: tuspyserver with custom R2 storage backend
- **Rationale**: FastAPI-native, full TUS v1.0.0 compliance
- **Trade-off**: Requires custom backend development (~2-3 days)

### 2. Background Processing
- **Choice**: Kafka consumers (not Celery)
- **Rationale**: Aligns with existing event-driven architecture
- **Trade-off**: Need to implement consumer service (existing Flower monitoring won't work)

### 3. Encryption
- **Choice**: AES-256-GCM with HKDF key derivation
- **Rationale**: Authenticated encryption, streaming support
- **Trade-off**: Key management complexity (mitigated by per-workspace versioned keys)

### 4. Image Processing
- **Choice**: Pillow + rawpy + ffmpeg-python
- **Rationale**: Covers JPEG, PNG, WebP, RAW formats, and video
- **Trade-off**: Multiple dependencies (but each is best-in-class for its domain)

## Integration Points

| System | Integration Method | Direction |
|--------|-------------------|-----------|
| Gallery Service | Kafka events (`asset.processed`) | Upload → Gallery |
| Frontend | TUS client (Uppy recommended) | Frontend → Upload |
| R2 Storage | boto3 multipart upload | Upload → R2 |
| Google Cloud Vision | REST API via client library | Processing → GCV |
| Prometheus | `/metrics` endpoint | Monitoring ← Services |

## Dependencies to Add

### upload-service/requirements.txt
```
# Core
fastapi[all]==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0

# TUS Protocol
tuspyserver==4.2.3

# Database
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.13.1

# Cache & Events
redis==5.0.1
aiokafka==0.10.0

# Storage & Encryption
boto3==1.34.0
cryptography==41.0.7

# Observability
prometheus-client==0.19.0
structlog==23.2.0
```

### processing-service/requirements.txt
```
# Core
pydantic==2.5.2
pydantic-settings==2.1.0

# Events
aiokafka==0.10.0
redis==5.0.1

# Image Processing
Pillow==10.1.0
rawpy==0.18.0
ffmpeg-python==0.2.0
ExifRead==3.0.0

# AI
google-cloud-vision==3.5.0

# Database (for storing results)
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0

# Storage & Encryption
boto3==1.34.0
cryptography==41.0.7

# Observability
prometheus-client==0.19.0
structlog==23.2.0
```

## Next Steps

Run `/speckit.tasks` to generate implementation tasks from this plan.
