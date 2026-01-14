# AI & Face Detection Services — Documentation

> **Purpose**: Documentation for AI-powered features and face detection services that will integrate with galleries. These services are being developed separately and will be integrated once complete.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Face Service Architecture](#2-face-service-architecture)
3. [Face Detection](#3-face-detection)
4. [Face Recognition & People Management](#4-face-recognition--people-management)
5. [Find Me (Selfie Search)](#5-find-me-selfie-search)
6. [Emotion-Based Filtering](#6-emotion-based-filtering)
7. [AI-Powered Tagging](#7-ai-powered-tagging)
8. [Smart Curation](#8-smart-curation)
9. [Auto-Selection](#9-auto-selection)
10. [Gallery Integration Points](#10-gallery-integration-points)
11. [Configuration & Privacy](#11-configuration--privacy)
12. [API Endpoints](#12-api-endpoints)
13. [Data Models](#13-data-models)
14. [Performance & Scalability](#14-performance--scalability)
15. [Future Development](#15-future-development)

---

## 1. Overview

vDrive's AI services provide intelligent features for photo management, curation, and client experience enhancement. These services are designed as independent microservices that integrate with the gallery system.

### Goals

- Automatic face detection and recognition for photo organization
- "Find Me" selfie search for clients in galleries
- Emotion-based photo filtering and search
- AI-powered auto-tagging for searchability
- Smart curation and auto-selection assistance
- People management with automatic grouping

### Non-Goals (Phase 1)

- Real-time face tracking in video
- Face recognition training with custom models
- Enterprise-grade facial biometrics

### Dependencies

| Service | Purpose |
|---------|---------|
| **Google Cloud Vision API** | Face detection |
| **ArcFace ONNX Model** | 512-dimensional face embeddings |
| **Milvus / pgvector** | Vector similarity search |
| **Gemini Vision API** | AI-powered photo analysis |
| **CLIP Embeddings** | Semantic image search |

---

## 2. Face Service Architecture

### Service Overview (Port 8002)

The Face Service is a dedicated microservice handling all face-related operations:

```
┌─────────────────────────────────────────────────────────────┐
│                      Face Service                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Detection  │  │ Recognition │  │  People Management  │ │
│  │   (GCV)     │  │  (ArcFace)  │  │   (Auto-grouping)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────────────┐ │
│  │              Vector Database (Milvus/pgvector)         │ │
│  │              512-dimensional embeddings                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Scaling Configuration (KEDA)

```yaml
# Face Service: 2-50 replicas
triggers:
  - type: prometheus
    threshold: "50"   # 50 face detection requests per replica
  - type: kafka
    threshold: "100"  # Kafka lag for batch processing
```

---

## 3. Face Detection

### Process Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Asset     │───►│   Google    │───►│   Extract   │───►│   Store     │
│   Upload    │    │   Cloud     │    │   Face      │    │   Face      │
│   Complete  │    │   Vision    │    │   Regions   │    │   Regions   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Detection Response

| Field | Type | Description |
|-------|------|-------------|
| `face_id` | UUID | Unique face identifier |
| `asset_id` | UUID | Parent asset |
| `bounding_box` | JSONB | Face region coordinates |
| `confidence` | float | Detection confidence (0-1) |
| `landmarks` | JSONB | Facial landmark positions |
| `attributes` | JSONB | Detected attributes |

### Detected Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `joy` | float | Joy likelihood (0-1) |
| `sorrow` | float | Sorrow likelihood (0-1) |
| `anger` | float | Anger likelihood (0-1) |
| `surprise` | float | Surprise likelihood (0-1) |
| `under_exposed` | boolean | Lighting quality |
| `blurred` | boolean | Focus quality |
| `headwear` | boolean | Headwear detected |

---

## 4. Face Recognition & People Management

### Embedding Generation

Using ArcFace ONNX model:
- 512-dimensional face embeddings
- Trained on large-scale face datasets
- High accuracy for face matching

### People Grouping

```typescript
interface Person {
  person_id: UUID;
  workspace_id: UUID;
  gallery_id?: UUID;        // Optional gallery scope
  name?: string;            // Assigned name
  representative_face_id: UUID;
  face_count: number;
  created_at: datetime;
  updated_at: datetime;
}

interface PersonFace {
  person_id: UUID;
  face_id: UUID;
  confidence: float;        // Match confidence
  is_verified: boolean;     // Manual verification
}
```

### Auto-Grouping Algorithm

1. Extract face embedding for new face
2. Search for similar embeddings in workspace
3. If similarity > threshold (0.7): assign to existing person
4. If no match: create new person cluster
5. Staff can manually merge/split groups

---

## 5. Find Me (Selfie Search)

### Overview

"Find Me" allows gallery clients to upload a selfie and find all photos containing them.

### Process Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───►│   Detect    │───►│   Generate  │───►│   Search    │
│   Uploads   │    │   Face in   │    │   Embedding │    │   Similar   │
│   Selfie    │    │   Selfie    │    │   (ArcFace) │    │   Faces     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                      ┌─────────────────────────▼
                                      │   Return matching photos
                                      │   sorted by confidence
                                      └─────────────────────────────
```

### Configuration Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `findme_enabled` | boolean | Enable Find Me feature | true |
| `findme_confidence_threshold` | float | Minimum match confidence | 0.7 |
| `findme_max_results` | int | Maximum results returned | 100 |

### API Flow

1. `POST /api/v1/public/galleries/{id}/findme/upload` - Upload selfie
2. Face detection extracts face region
3. ArcFace generates 512-dim embedding
4. Vector search in gallery's face embeddings
5. Return ranked photo list with confidence scores

---

## 6. Emotion-Based Filtering

### Overview

Allow filtering gallery photos by detected emotions for curated viewing experiences.

### Emotion Categories

| Emotion | Description | Use Case |
|---------|-------------|----------|
| `joyful` | High joy score | Happy moments |
| `candid` | Natural expressions | Documentary style |
| `romantic` | Soft expressions | Couple shots |
| `energetic` | High surprise/joy | Party photos |
| `serene` | Calm expressions | Portrait selections |

### Filter Implementation

```typescript
interface EmotionFilter {
  emotions: string[];       // Filter by emotions
  threshold: number;        // Minimum score (0-1)
  combine: 'AND' | 'OR';   // Combination logic
}

// Example: Find joyful photos
const filter: EmotionFilter = {
  emotions: ['joyful'],
  threshold: 0.7,
  combine: 'OR'
};
```

### Gallery Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `emotion_filtering_enabled` | boolean | Enable emotion filters | true |
| `emotion_confidence_threshold` | float | Minimum confidence | 0.6 |

---

## 7. AI-Powered Tagging

### Overview

Automatic tag generation for photos using AI vision models.

### Tag Sources

| Source | Technology | Tags Generated |
|--------|------------|----------------|
| Scene Detection | Gemini Vision | landscape, indoor, outdoor, beach, etc. |
| Object Detection | Gemini Vision | car, cake, flowers, dress, etc. |
| Activity Detection | Gemini Vision | dancing, kissing, walking, etc. |
| Face Analysis | Google Cloud Vision | group_photo, portrait, candid |
| CLIP Embeddings | OpenAI CLIP | Semantic concepts |

### Tag Data Model

```typescript
interface AssetTag {
  tag_id: UUID;
  asset_id: UUID;
  tag: string;
  source: 'ai' | 'manual' | 'exif';
  confidence: float;
  created_at: datetime;
}
```

### Tag Management

- Tags are searchable in gallery text search
- Staff can remove/add tags manually
- AI tags can be regenerated on demand
- Per-gallery AI tag visibility toggle

---

## 8. Smart Curation

### Overview

AI-assisted photo curation to help photographers select the best shots.

### Quality Scoring

| Metric | Weight | Description |
|--------|--------|-------------|
| Technical Quality | 30% | Focus, exposure, noise |
| Composition | 25% | Rule of thirds, balance |
| Face Quality | 25% | Expression, eyes open |
| Uniqueness | 20% | Diversity from similar shots |

### Duplicate/Similar Detection

Using CLIP embeddings:
- Generate embedding for each photo
- Cluster similar photos together
- Rank within cluster by quality score
- Suggest best from each cluster

### Curation Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Analyze   │───►│   Score     │───►│   Cluster   │───►│   Rank &    │
│   All       │    │   Quality   │    │   Similar   │    │   Suggest   │
│   Photos    │    │   Metrics   │    │   Photos    │    │   Best      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 9. Auto-Selection

### Overview

AI-powered automatic selection of the best photos for proofing.

### Selection Criteria

| Criteria | Description |
|----------|-------------|
| Coverage | Ensure all key moments represented |
| Quality | Prioritize technically excellent shots |
| Variety | Avoid repetitive selections |
| Faces | Include photos of all key people |

### Auto-Select Algorithm

1. Cluster photos by time/scene
2. Score each photo in cluster
3. Select top N per cluster
4. Ensure face coverage (all people represented)
5. Final diversity pass

### Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `auto_select_enabled` | boolean | Enable auto-selection | true |
| `auto_select_count` | int | Target selection count | 50 |
| `auto_select_diversity` | float | Diversity weight (0-1) | 0.3 |

---

## 10. Gallery Integration Points

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Gallery Service                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      Gallery Feature Flags                       ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐││
│  │  │ FindMe    │  │ Emotion   │  │ AI Tags   │  │ Smart Curate  │││
│  │  │ Enabled   │  │ Filter    │  │ Search    │  │ Enabled       │││
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘││
│  └────────┼──────────────┼──────────────┼────────────────┼─────────┘│
│           │              │              │                │          │
│           ▼              ▼              ▼                ▼          │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                      Face Service (Port 8002)                   ││
│  │                      AI Provider APIs                           ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Feature Flags

Per-gallery control over AI features:

```typescript
interface GalleryAISettings {
  findme_enabled: boolean;
  findme_confidence_threshold: number;
  emotion_filtering_enabled: boolean;
  ai_tagging_enabled: boolean;
  smart_curate_enabled: boolean;
  auto_select_enabled: boolean;
}
```

### Client Portal Integration

| Feature | Client Portal UI | Integration |
|---------|------------------|-------------|
| Find Me | "Find My Photos" button | FaceDiscovery component |
| Emotion Filter | Filter dropdown | GalleryFilters component |
| AI Tags | Search suggestions | SearchBar component |
| People View | "People" tab | PeopleGallery component |

---

## 11. Configuration & Privacy

### AI Privacy Settings (Per-Gallery)

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `ai_analysis_enabled` | boolean | Allow AI processing | true |
| `face_detection_enabled` | boolean | Allow face detection | true |
| `face_recognition_enabled` | boolean | Allow face grouping | true |
| `ai_tags_visible_to_clients` | boolean | Show AI tags to clients | false |
| `findme_available` | boolean | Allow Find Me feature | true |

### Privacy Considerations

- Face data is workspace-scoped (never shared across workspaces)
- Clients' selfies are processed but not stored permanently
- GDPR compliance: face data can be deleted on request
- Opt-out: galleries can disable all AI features
- Data minimization: only store embeddings, not raw face images

### Admin Controls

- Queue unanalyzed photos for AI processing
- Re-analyze all photos (regenerate tags/embeddings)
- Clear all AI data for gallery
- Export face data for GDPR requests

---

## 12. API Endpoints

### Face Service Endpoints

```
# Face Detection
POST   /api/v1/faces/detect                    # Detect faces in image
GET    /api/v1/faces/{face_id}                 # Get face details

# People Management
GET    /api/v1/workspaces/{id}/people          # List people in workspace
POST   /api/v1/people                          # Create person
PATCH  /api/v1/people/{id}                     # Update person (name, etc.)
DELETE /api/v1/people/{id}                     # Delete person
POST   /api/v1/people/{id}/merge               # Merge people

# Find Me (Public)
POST   /api/v1/public/galleries/{id}/findme/upload   # Upload selfie
GET    /api/v1/public/galleries/{id}/findme/results  # Get results

# Gallery AI Integration
GET    /api/v1/galleries/{id}/faces            # List faces in gallery
GET    /api/v1/galleries/{id}/people           # List people in gallery
POST   /api/v1/galleries/{id}/ai/analyze       # Trigger AI analysis
POST   /api/v1/galleries/{id}/ai/auto-select   # Run auto-selection
```

### AI Tagging Endpoints

```
# Tag Management
GET    /api/v1/assets/{id}/tags                # Get asset tags
POST   /api/v1/assets/{id}/tags                # Add manual tag
DELETE /api/v1/assets/{id}/tags/{tag_id}       # Remove tag
POST   /api/v1/galleries/{id}/ai/regenerate-tags  # Regenerate AI tags
```

---

## 13. Data Models

### Face Detection

```python
class Face(BaseModel):
    face_id: UUID
    workspace_id: UUID
    asset_id: UUID
    bounding_box: dict      # {x, y, width, height}
    confidence: float
    landmarks: dict | None
    embedding: list[float]  # 512-dimensional vector
    attributes: dict        # emotions, quality, etc.
    created_at: datetime
```

### Person

```python
class Person(BaseModel):
    person_id: UUID
    workspace_id: UUID
    gallery_id: UUID | None  # None = workspace-wide
    name: str | None
    representative_face_id: UUID
    face_count: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime
```

### AI Tag

```python
class AssetTag(BaseModel):
    tag_id: UUID
    asset_id: UUID
    tag: str
    source: Literal['ai', 'manual', 'exif']
    confidence: float | None
    created_at: datetime
```

### Quality Score

```python
class AssetQualityScore(BaseModel):
    asset_id: UUID
    technical_score: float   # 0-1
    composition_score: float # 0-1
    face_score: float | None # 0-1, if faces present
    overall_score: float     # 0-1, weighted average
    computed_at: datetime
```

---

## 14. Performance & Scalability

### Processing Targets

| Operation | Target Latency | Throughput |
|-----------|----------------|------------|
| Face Detection | < 500ms | 100/min per replica |
| Embedding Generation | < 200ms | 200/min per replica |
| Similarity Search | < 100ms | 1000/min per replica |
| AI Tagging | < 2s | 50/min per replica |

### Vector Search Optimization

| Dataset Size | Index Type | Use Case |
|--------------|------------|----------|
| < 100K faces | HNSW (pgvector) | Small galleries |
| 100K - 10M | IVFFlat | Medium workspaces |
| > 10M | StreamingDiskANN | Large-scale |

### Batch Processing

- Async processing via Kafka queue
- Batch face detection (up to 100 images)
- Background embedding generation
- Scheduled re-analysis jobs

---

## 15. Future Development

### Planned Features

| Feature | Priority | Status |
|---------|----------|--------|
| Find Me in public galleries | HIGH | In Development |
| People view tab | HIGH | Planned |
| Emotion filtering UI | MEDIUM | Planned |
| Smart curation assistant | MEDIUM | Planned |
| Auto-selection suggestions | MEDIUM | Planned |
| Custom face recognition | LOW | Future |
| Video face tracking | LOW | Future |

### Integration Milestones

1. **Phase 1**: Face detection + Find Me (public galleries)
2. **Phase 2**: People management + grouping (staff UI)
3. **Phase 3**: Emotion filtering + AI tags (client portal)
4. **Phase 4**: Smart curation + auto-selection (staff tools)

### Open Questions

- Face recognition accuracy thresholds for production
- Storage costs for high-volume embeddings
- Client privacy consent workflow for Find Me
- Face data retention policies

---

## Related Documentation

### Technical References

- `services/face-service/` - Face service implementation
- `docs/Business_Features/028-faceid-microservice/` - Feature specification
- `infrastructure/kubernetes/base/keda/face-scaledobject.yaml` - Scaling config

### Integration Points

- `docs/Features/GALLERY_COMPREHENSIVE.md` - Gallery integration
- `docs/Features/CLIENT_FACING_FEATURES.md` - Client portal features
- `docs/Features/RBAC_AND_USER_MANAGEMENT.md` - Permissions

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-13 | 1.0.0 | Initial documentation extracted from gallery docs |

---

**Note:** This document covers AI and face detection features that will be developed separately and integrated with galleries once complete. See `GALLERY_COMPREHENSIVE.md` for core gallery functionality.
