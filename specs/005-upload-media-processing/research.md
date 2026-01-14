# Research: Storage & Media Processing

**Feature**: 005-upload-media-processing
**Date**: 2026-01-14
**Status**: Complete

## Executive Summary

This document captures technology decisions and research findings for the Upload Service and Celery Workers implementation. All critical questions have been resolved.

---

## 1. TUS Protocol Implementation

### Decision: tuspyserver with Custom R2 Backend

**Rationale**:
- `tuspyserver==4.2.3` is lightweight, FastAPI-native, and TUS v1.0.0 compliant
- Requires custom storage backend for Cloudflare R2 (default is local filesystem only)
- Alternative `fastapi-tusd` has lower adoption and incomplete extensions

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| tuspyserver | FastAPI-native, maintained, full TUS v1.0.0 | No R2 backend | **Selected** (with custom backend) |
| fastapi-tusd | S3 mentioned | Low adoption, incomplete | Rejected |
| Custom implementation | Full control | 4-6 weeks dev time | Rejected |

**Implementation Pattern**:
- Use S3 multipart upload API (R2 is S3-compatible)
- Track offset in PostgreSQL + Redis (hybrid for durability + speed)
- Part size: minimum 5MB for R2 compatibility
- Upload URL TTL: 24 hours (per spec requirement)

**Key Dependencies**:
```
tuspyserver==4.2.3
boto3==1.34.0 (already present)
```

---

## 2. Background Task Processing

### Decision: Kafka Consumers (Not Celery)

**Rationale**:
- vDrive already uses Kafka for event-driven architecture
- Kafka topics pre-created: `upload.initiated`, `upload.completed`, `asset.processing`, `asset.processed`
- Single event bus simplifies operations vs dual systems (Kafka + Celery)
- Better ordering guarantees with partition key = `workspace_id`
- KEDA already has Kafka scaler configured

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Kafka consumers | Aligns with existing architecture, single event bus | New consumer service needed | **Selected** |
| Celery + Redis | Well-documented, Flower ready | Dual systems, complexity | Rejected |
| BullMQ (Node.js) | Simple queue semantics | Different runtime | Rejected |

**Architecture**:
```
services/
├── upload-service/        # TUS protocol, produces events
├── processing-service/    # Kafka consumer (new)
│   ├── consumers/
│   │   ├── asset_processor.py    # Thumbnails, EXIF
│   │   ├── face_detector.py      # AI processing
│   │   └── notification_sender.py
│   └── main.py                   # Consumer group runner
```

**Task Routing**:
- Partition key: `workspace_id` (ensures ordering per tenant)
- Consumer groups: `asset-processor-group`, `face-detector-group`
- Dead Letter Queue: `webhook.dlq` for failed messages

**KEDA Scaling**:
```yaml
triggers:
  - type: kafka
    metadata:
      consumerGroup: asset-processor-group
      topic: asset.processing
      lagThreshold: "100"  # Scale when 100+ messages lag
```

---

## 3. File Encryption

### Decision: AES-256-GCM with HKDF Key Derivation

**Rationale**:
- `cryptography==41.0.7` already in gallery-service requirements
- AES-256-GCM provides authenticated encryption (prevents tampering)
- HKDF-SHA256 for workspace-aware key derivation
- Streaming encryption for large files (constant memory usage)

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| AES-256-GCM + HKDF | Authenticated, NIST-approved, streaming | Slightly complex | **Selected** |
| AES-256-CBC | Simpler | No authentication, padding oracle risk | Rejected |
| ChaCha20-Poly1305 | Fast on mobile | Less common in Python | Rejected |

**Key Management**:
```
Master Key (env: ENCRYPTION_MASTER_KEY)
    └─ HKDF(master, salt=workspace_id, info="asset:{asset_id}")
        └─ Per-asset AES-256 key
```

**Storage Pattern**:
- Encrypt file stream before R2 upload
- Store IV (16 bytes) and auth_tag (16 bytes) in database
- Reference `encryption_key_id` for key rotation support

**Performance**:
- 100MB file: ~280ms encryption + ~1.5s R2 upload
- Memory: ~10KB constant (streaming, 8KB chunks)

---

## 4. Image Processing

### Decision: Pillow + rawpy for RAW support

**Rationale**:
- `Pillow==10.1.0` already in gallery-service requirements
- WebP output natively supported
- `rawpy` for RAW format extraction (CR2, NEF, ARW, DNG)
- `ffmpeg-python` for video thumbnail extraction

**Derivatives Generated**:
| Type | Size | Quality | Format | Use Case |
|------|------|---------|--------|----------|
| Thumbnail | 300px longest | 80% | WebP | Gallery grid |
| Preview | 1200px longest | 85% | WebP | Lightbox view |
| LQIP | 20px | 60% | WebP (base64) | Blur placeholder |

**Processing Pipeline**:
1. Detect file type (MIME validation)
2. For RAW: Extract embedded JPEG preview
3. Generate derivatives with Pillow
4. Encrypt each derivative
5. Upload to R2 with structured keys

**Additional Dependencies**:
```
rawpy==0.18.0        # RAW file support
ffmpeg-python==0.2.0 # Video thumbnails
```

---

## 5. Metadata Extraction

### Decision: ExifRead + pgvector for Search

**Rationale**:
- `exifread` is lightweight and handles all common EXIF formats
- `pgvector` already configured in vDrive for semantic search
- Store structured metadata in PostgreSQL, embeddings in pgvector

**Fields Extracted**:
| Category | Fields |
|----------|--------|
| Camera | make, model, lens_model |
| Settings | aperture, shutter_speed, iso, focal_length |
| Time | date_taken, timezone |
| Location | gps_latitude, gps_longitude |
| Image | width, height, orientation |

**Additional Dependencies**:
```
ExifRead==3.0.0
```

---

## 6. Face Detection

### Decision: Google Cloud Vision API

**Rationale**:
- Per spec requirement (FR-018)
- High accuracy for frontal faces (95%+)
- Rate limiting with queuing and backoff
- Workspace-level enable/disable setting

**Integration Pattern**:
- Async API calls via `google-cloud-vision` library
- Store face bounding boxes, confidence, and embeddings in PostgreSQL
- Respect workspace `face_detection_enabled` setting
- Queue requests to stay within quota

**Additional Dependencies**:
```
google-cloud-vision==3.5.0
```

---

## 7. Object Storage Structure

### Decision: Structured R2 Keys with Encryption

**Key Format**:
```
workspaces/{workspace_id}/assets/{asset_id}/
    ├── original.{ext}      # Encrypted original
    ├── thumbnail.webp      # Encrypted thumbnail (300px)
    ├── preview.webp        # Encrypted preview (1200px)
    └── metadata.json       # IV, auth_tag, EXIF summary
```

**R2 Configuration**:
- Bucket: `vdrive` (from settings)
- Endpoint: Cloudflare R2 (S3-compatible)
- Access: boto3 with S3v4 signature

---

## 8. Service Port Allocation

| Service | Port | Protocol |
|---------|------|----------|
| Upload Service | 8008 | HTTP (TUS) |
| Processing Service | 8010 | HTTP (metrics only) |

**Port Selection Rationale**:
- 8008: Per spec requirement, next available after 8006 (onboarding)
- 8010: Metrics endpoint for Prometheus scraping

---

## 9. Docker Compose Integration

**New Services**:
```yaml
upload-service:
  build: ../../services/upload-service
  ports: ["8008:8008"]
  depends_on: [postgres, redis, kafka]

processing-service:
  build: ../../services/processing-service
  ports: ["8010:8010"]
  depends_on: [postgres, kafka, redis]
  environment:
    KAFKA_CONSUMER_GROUP: asset-processor-group
```

---

## 10. Technology Stack Summary

| Component | Technology | Version | Status |
|-----------|------------|---------|--------|
| Upload Protocol | tuspyserver | 4.2.3 | New dependency |
| Task Processing | Kafka consumers | aiokafka 0.10.0 | Existing |
| Encryption | cryptography | 41.0.7 | Existing |
| Image Processing | Pillow | 10.1.0 | Existing |
| RAW Processing | rawpy | 0.18.0 | New dependency |
| Video Processing | ffmpeg-python | 0.2.0 | New dependency |
| Metadata Extraction | ExifRead | 3.0.0 | New dependency |
| Face Detection | google-cloud-vision | 3.5.0 | New dependency |
| Object Storage | boto3 | 1.34.0 | Existing |
| Database | SQLAlchemy + asyncpg | 2.0.23 | Existing |
| Cache | Redis | 5.0.1 | Existing |
| Events | Kafka | aiokafka 0.10.0 | Existing |

---

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| TUS library choice | tuspyserver with custom R2 backend |
| Task queue choice | Kafka consumers (aligns with existing architecture) |
| Encryption algorithm | AES-256-GCM with HKDF key derivation |
| Key rotation support | Via `encryption_key_id` column + 90-day cycle |
| RAW file support | rawpy for embedded preview extraction |
| Video thumbnail | ffmpeg-python for frame extraction |
| Face detection API | Google Cloud Vision (per spec) |
