# Data Model: Face Service

**Feature**: 008-face-service
**Date**: 2026-01-16

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   FaceGroup     │     │        Face         │     │  FaceEmbedding   │
│    (Person)     │     │   (Detection)       │     │    (Vector)      │
├─────────────────┤     ├─────────────────────┤     ├──────────────────┤
│ id (PK)         │◄────┤ group_id (FK)       │────►│ face_id (FK, UK) │
│ workspace_id    │     │ id (PK)             │     │ id (PK)          │
│ name            │     │ workspace_id        │     │ embedding[512]   │
│ representative  │────►│ asset_id            │     │ model_name       │
│ _face_id (FK)   │     │ bounding_box (JSON) │◄────┤ created_at       │
│ face_count      │     │ confidence          │     └──────────────────┘
│ created_at      │     │ landmarks (JSON)    │
│ updated_at      │     │ embedding_id (FK)   │
└─────────────────┘     │ detection_metadata  │
         │              │ created_at          │
         │              │ updated_at          │
         ▼              └─────────────────────┘
    "Person #abc"                │
    display_name                 │
                                 ▼
                          External: Asset
                     (from upload-service)
```

## Entities

### Face

Represents a single detected face within an image asset.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| asset_id | UUID | NOT NULL, INDEX | Reference to source image asset |
| workspace_id | UUID | NOT NULL, INDEX | Multi-tenancy isolation |
| bounding_box | JSONB | NOT NULL | `{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}` normalized coordinates |
| confidence | NUMERIC(5,4) | NOT NULL | Detection confidence (0.0000-1.0000) |
| landmarks | JSONB | NULLABLE | `{"left_eye": [x,y], "right_eye": [x,y], "nose_tip": [x,y], ...}` |
| embedding_id | UUID | FK(face_embeddings), CASCADE | Reference to vector embedding |
| group_id | UUID | FK(face_groups), SET NULL, INDEX | Reference to person group |
| detection_metadata | JSONB | NULLABLE | `{"joy", "sorrow", "anger", "surprise", "headwear", "roll_angle", ...}` |
| created_at | TIMESTAMP WITH TZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TZ | AUTO UPDATE | Last modification timestamp |

**Indexes**:
- `ix_faces_asset_id` (asset_id)
- `ix_faces_workspace_id` (workspace_id)
- `ix_faces_group_id` (group_id)
- `ix_faces_workspace_asset` (workspace_id, asset_id) COMPOSITE
- `ix_faces_workspace_group` (workspace_id, group_id) COMPOSITE

**Relationships**:
- ONE-TO-ONE with FaceEmbedding (via embedding_id)
- MANY-TO-ONE with FaceGroup (via group_id)
- MANY-TO-ONE with Asset (external, via asset_id)

---

### FaceEmbedding

Stores the 512-dimensional vector representation for similarity search.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| face_id | UUID | FK(faces), CASCADE, UNIQUE, NOT NULL | Back-reference to face |
| embedding | VECTOR(512) | NOT NULL | 512-dim ArcFace embedding, L2-normalized |
| model_name | VARCHAR(100) | NULLABLE | Embedding model identifier (versioning) |
| created_at | TIMESTAMP WITH TZ | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `ix_face_embeddings_face_id` (face_id) UNIQUE
- `ix_face_embeddings_vector` (embedding) IVFFlat
  - Type: `ivfflat`
  - Operator class: `vector_cosine_ops`
  - Parameters: `lists = 100`

**Vector Operations**:
- Similarity metric: Cosine distance (`<=>` operator)
- Normalization: L2 unit vectors (magnitude = 1.0)
- Dimension: Fixed 512 (ArcFace standard)

---

### FaceGroup

Represents a person - a cluster of faces identified as the same individual.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| workspace_id | UUID | NOT NULL, INDEX | Multi-tenancy isolation |
| name | VARCHAR(255) | NULLABLE | User-assigned person name |
| representative_face_id | UUID | FK(faces), SET NULL | Best face for display (closest to centroid) |
| face_count | VARCHAR(10) | DEFAULT '0' | Denormalized count for performance |
| created_at | TIMESTAMP WITH TZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TZ | AUTO UPDATE | Last modification timestamp |

**Indexes**:
- `ix_face_groups_workspace_id` (workspace_id)
- `ix_face_groups_workspace_name` (workspace_id, name) COMPOSITE

**Computed Properties**:
- `display_name`: Returns `name` if set, otherwise `"Person #{id[:8]}"`

**Relationships**:
- ONE-TO-MANY with Face (inverse via group_id)
- ONE-TO-ONE with Face for representative (via representative_face_id)

---

## Validation Rules

### Face

| Field | Rule | Error |
|-------|------|-------|
| bounding_box.x | 0.0 ≤ x ≤ 1.0 | Invalid bounding box x coordinate |
| bounding_box.y | 0.0 ≤ y ≤ 1.0 | Invalid bounding box y coordinate |
| bounding_box.width | 0.0 < width ≤ 1.0 | Invalid bounding box width |
| bounding_box.height | 0.0 < height ≤ 1.0 | Invalid bounding box height |
| confidence | 0.0 ≤ confidence ≤ 1.0 | Invalid confidence score |
| workspace_id | Must exist in workspaces table | Invalid workspace |

### FaceEmbedding

| Field | Rule | Error |
|-------|------|-------|
| embedding | len(embedding) == 512 | Embedding must be 512 dimensions |
| embedding | \|embedding\| ≈ 1.0 (L2 norm) | Embedding must be normalized |
| face_id | Must be unique | Duplicate embedding for face |

### FaceGroup

| Field | Rule | Error |
|-------|------|-------|
| name | len(name) ≤ 255 | Name too long |
| representative_face_id | Must belong to same group | Representative face must be in group |
| face_count | Non-negative integer | Invalid face count |

---

## State Transitions

### Face Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐
│ DETECTED │────►│ EMBEDDED     │────►│ GROUPED       │
└──────────┘     └──────────────┘     └───────────────┘
     │                                        │
     │                                        │
     ▼                                        ▼
┌──────────┐                          ┌───────────────┐
│ FAILED   │                          │ MANUALLY_     │
│ (no face)│                          │ REASSIGNED    │
└──────────┘                          └───────────────┘
```

| State | Conditions |
|-------|------------|
| DETECTED | Face record created, bounding_box populated |
| EMBEDDED | embedding_id populated with 512-dim vector |
| GROUPED | group_id populated (auto or manual) |
| FAILED | Detection below confidence threshold |
| MANUALLY_REASSIGNED | User moved face between groups |

### FaceGroup Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐
│ CREATED  │────►│ NAMED        │────►│ MERGED        │
│ (auto)   │     │ (user)       │     │ (consolidated)│
└──────────┘     └──────────────┘     └───────────────┘
                        │
                        ▼
                 ┌───────────────┐
                 │ SPLIT         │
                 │ (refined)     │
                 └───────────────┘
```

---

## Multi-Tenancy

All entities enforce workspace isolation:

```sql
-- Every query includes workspace_id filter
SELECT * FROM faces
WHERE workspace_id = :workspace_id AND asset_id = :asset_id;

-- Cross-workspace access is forbidden
-- No FK relationship to workspaces (managed by backend)
-- Indexes optimized for workspace-first queries
```

---

## Data Retention

| Entity | Retention Policy |
|--------|-----------------|
| Face | Deleted when parent asset is deleted (CASCADE) |
| FaceEmbedding | Deleted when parent face is deleted (CASCADE) |
| FaceGroup | Deleted when all member faces are deleted (orphan cleanup) |

---

## Migration Notes

**Existing Migration**: `services/face-service/alembic/versions/001_initial_face_tables.py`

**pgvector Setup**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- IVFFlat index for similarity search
CREATE INDEX ix_face_embeddings_vector
ON face_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Index Tuning** (for >100K faces):
```sql
-- Increase lists parameter
DROP INDEX ix_face_embeddings_vector;
CREATE INDEX ix_face_embeddings_vector
ON face_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 500);
```
