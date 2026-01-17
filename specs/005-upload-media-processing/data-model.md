# Data Model: Storage & Media Processing

**Feature**: 005-upload-media-processing
**Date**: 2026-01-14
**Database**: PostgreSQL 16 with pgvector extension

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Workspace    │       │     Upload      │       │     Asset       │
│  (existing)     │◄──────│                 │──────►│                 │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ EncryptionKey   │       │ ProcessingTask  │       │  AssetMetadata  │
│                 │       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │      Face       │
                                                    │                 │
                                                    └─────────────────┘
```

---

## 1. Upload

Represents an in-progress or completed resumable upload session (TUS protocol).

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique upload identifier |
| workspace_id | UUID | FK → Workspace, NOT NULL, INDEX | Tenant isolation |
| user_id | UUID | FK → User, NOT NULL | Upload initiator |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| mime_type | VARCHAR(100) | NOT NULL | Validated MIME type |
| expected_size | BIGINT | NOT NULL, CHECK > 0 | Total file size in bytes |
| received_bytes | BIGINT | NOT NULL, DEFAULT 0 | Current upload offset |
| status | VARCHAR(20) | NOT NULL, INDEX | Upload state |
| upload_url | VARCHAR(500) | UNIQUE | TUS upload endpoint |
| storage_path | VARCHAR(500) | NULLABLE | Temp storage location |
| checksum_client | VARCHAR(64) | NULLABLE | Client-provided SHA-256 |
| checksum_server | VARCHAR(64) | NULLABLE | Server-computed SHA-256 |
| multipart_upload_id | VARCHAR(100) | NULLABLE | S3/R2 multipart ID |
| parts_metadata | JSONB | DEFAULT '[]' | Multipart part ETags |
| expires_at | TIMESTAMPTZ | NOT NULL, INDEX | Upload URL expiration |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

### Status Values

| Status | Description |
|--------|-------------|
| `created` | Upload session initialized, awaiting chunks |
| `uploading` | Receiving chunks, in progress |
| `assembling` | All chunks received, assembling file |
| `completed` | Successfully completed |
| `failed` | Processing failed |
| `expired` | Upload URL expired (cleanup pending) |
| `cancelled` | User cancelled upload |

### Indexes

```sql
CREATE INDEX idx_upload_workspace_status ON uploads(workspace_id, status);
CREATE INDEX idx_upload_expires ON uploads(expires_at) WHERE status IN ('created', 'uploading');
CREATE INDEX idx_upload_user ON uploads(user_id, created_at DESC);
```

### Validation Rules

- `expected_size` must be ≤ 10GB (10,737,418,240 bytes)
- `mime_type` must be in allowlist: `image/jpeg`, `image/png`, `image/webp`, `image/heic`, `image/x-canon-cr2`, `image/x-nikon-nef`, `image/x-sony-arw`, `image/x-adobe-dng`, `video/mp4`, `video/quicktime`, `video/x-msvideo`
- `received_bytes` must be ≤ `expected_size`
- `upload_url` must be unique across all active uploads

---

## 2. Asset

Represents a fully processed file with all derivatives.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique asset identifier |
| workspace_id | UUID | FK → Workspace, NOT NULL, INDEX | Tenant isolation |
| upload_id | UUID | FK → Upload, UNIQUE | Source upload |
| original_key | VARCHAR(500) | NOT NULL | R2 object key for original |
| thumbnail_key | VARCHAR(500) | NULLABLE | R2 object key for 300px thumbnail |
| preview_key | VARCHAR(500) | NULLABLE | R2 object key for 1200px preview |
| lqip_base64 | TEXT | NULLABLE | Base64-encoded 20px placeholder |
| mime_type | VARCHAR(100) | NOT NULL | File MIME type |
| file_size | BIGINT | NOT NULL | Original file size |
| width | INTEGER | NULLABLE | Image width in pixels |
| height | INTEGER | NULLABLE | Image height in pixels |
| duration_seconds | DECIMAL(10,2) | NULLABLE | Video duration |
| is_encrypted | BOOLEAN | NOT NULL, DEFAULT TRUE | Encryption status |
| encryption_key_id | VARCHAR(100) | INDEX | Reference to encryption key version |
| encryption_iv | BYTEA | NULLABLE | AES-GCM initialization vector |
| encryption_tag | BYTEA | NULLABLE | AES-GCM authentication tag |
| processing_status | VARCHAR(20) | NOT NULL, INDEX | Processing state |
| processing_error | TEXT | NULLABLE | Error message if failed |
| checksum | VARCHAR(64) | NOT NULL, UNIQUE | SHA-256 hash |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

### Processing Status Values

| Status | Description |
|--------|-------------|
| `pending` | Awaiting processing |
| `processing` | Generating derivatives |
| `completed` | All derivatives ready |
| `failed` | Processing failed |
| `partial` | Some derivatives failed (degraded) |

### Indexes

```sql
CREATE INDEX idx_asset_workspace_created ON assets(workspace_id, created_at DESC);
CREATE INDEX idx_asset_processing ON assets(processing_status) WHERE processing_status != 'completed';
CREATE UNIQUE INDEX idx_asset_checksum ON assets(checksum);
```

### Validation Rules

- `checksum` must be unique within workspace (prevents duplicates)
- `original_key` must follow pattern: `workspaces/{workspace_id}/assets/{asset_id}/original.*`
- `encryption_iv` and `encryption_tag` must both be present or both be null

---

## 3. AssetMetadata

Extracted EXIF and technical metadata from asset files.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique metadata identifier |
| asset_id | UUID | FK → Asset, UNIQUE, ON DELETE CASCADE | Parent asset |
| camera_make | VARCHAR(100) | NULLABLE | Camera manufacturer |
| camera_model | VARCHAR(100) | NULLABLE, INDEX | Camera model name |
| lens_model | VARCHAR(200) | NULLABLE | Lens identifier |
| aperture | DECIMAL(4,1) | NULLABLE | f-stop value |
| shutter_speed | VARCHAR(20) | NULLABLE | Shutter speed (e.g., "1/250") |
| shutter_speed_seconds | DECIMAL(10,6) | NULLABLE | Shutter speed in seconds |
| iso | INTEGER | NULLABLE | ISO sensitivity |
| focal_length | DECIMAL(6,1) | NULLABLE | Focal length in mm |
| focal_length_35mm | DECIMAL(6,1) | NULLABLE | 35mm equivalent |
| exposure_compensation | DECIMAL(4,2) | NULLABLE | EV compensation |
| flash_fired | BOOLEAN | NULLABLE | Flash used |
| orientation | INTEGER | NULLABLE | EXIF orientation (1-8) |
| gps_latitude | DECIMAL(10,7) | NULLABLE | GPS latitude |
| gps_longitude | DECIMAL(10,7) | NULLABLE | GPS longitude |
| gps_altitude | DECIMAL(8,2) | NULLABLE | GPS altitude in meters |
| captured_at | TIMESTAMPTZ | NULLABLE, INDEX | Original capture time |
| color_space | VARCHAR(20) | NULLABLE | Color space (sRGB, AdobeRGB) |
| white_balance | VARCHAR(50) | NULLABLE | White balance mode |
| software | VARCHAR(100) | NULLABLE | Processing software |
| raw_exif | JSONB | DEFAULT '{}' | Full EXIF dump |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Extraction timestamp |

### Indexes

```sql
CREATE INDEX idx_metadata_camera ON asset_metadata(camera_model, lens_model);
CREATE INDEX idx_metadata_captured ON asset_metadata(captured_at);
CREATE INDEX idx_metadata_gps ON asset_metadata(gps_latitude, gps_longitude)
    WHERE gps_latitude IS NOT NULL;
```

### Validation Rules

- `aperture` must be > 0 if present
- `iso` must be between 50 and 102400 if present
- `gps_latitude` must be between -90 and 90
- `gps_longitude` must be between -180 and 180

---

## 4. Face

Detected face in an asset with bounding box and embedding.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique face identifier |
| asset_id | UUID | FK → Asset, NOT NULL, INDEX, ON DELETE CASCADE | Parent asset |
| workspace_id | UUID | FK → Workspace, NOT NULL, INDEX | Tenant isolation (denormalized) |
| bounding_box | JSONB | NOT NULL | Face region coordinates |
| confidence | DECIMAL(5,4) | NOT NULL | Detection confidence (0-1) |
| embedding | vector(512) | NULLABLE, INDEX | Face embedding for matching |
| cluster_id | UUID | NULLABLE, INDEX | Assigned face cluster/person |
| detection_source | VARCHAR(50) | NOT NULL, DEFAULT 'google_vision' | Detection API used |
| landmarks | JSONB | NULLABLE | Facial landmarks |
| attributes | JSONB | DEFAULT '{}' | Age, emotion, etc. |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Detection timestamp |

### Bounding Box Format

```json
{
  "x": 0.15,       // Normalized x (0-1)
  "y": 0.20,       // Normalized y (0-1)
  "width": 0.12,   // Normalized width (0-1)
  "height": 0.18,  // Normalized height (0-1)
  "rotation": 0    // Rotation in degrees
}
```

### Indexes

```sql
CREATE INDEX idx_face_asset ON faces(asset_id);
CREATE INDEX idx_face_workspace ON faces(workspace_id);
CREATE INDEX idx_face_cluster ON faces(cluster_id) WHERE cluster_id IS NOT NULL;
CREATE INDEX idx_face_embedding ON faces USING ivfflat (embedding vector_cosine_ops);
```

### Validation Rules

- `confidence` must be between 0 and 1
- `bounding_box` x, y, width, height must be between 0 and 1
- `embedding` dimension must be 512

---

## 5. ProcessingTask

Tracks asynchronous processing tasks (thumbnail generation, face detection, etc.).

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Task identifier |
| asset_id | UUID | FK → Asset, NOT NULL, INDEX | Target asset |
| workspace_id | UUID | FK → Workspace, NOT NULL, INDEX | Tenant isolation |
| task_type | VARCHAR(50) | NOT NULL, INDEX | Type of task |
| status | VARCHAR(20) | NOT NULL, INDEX | Task state |
| priority | INTEGER | NOT NULL, DEFAULT 5 | Queue priority (1-10) |
| kafka_topic | VARCHAR(100) | NULLABLE | Source Kafka topic |
| kafka_offset | BIGINT | NULLABLE | Kafka message offset |
| input_data | JSONB | DEFAULT '{}' | Task input parameters |
| output_data | JSONB | DEFAULT '{}' | Task results |
| error_message | TEXT | NULLABLE | Error details |
| retry_count | INTEGER | NOT NULL, DEFAULT 0 | Retry attempts |
| max_retries | INTEGER | NOT NULL, DEFAULT 3 | Maximum retries |
| started_at | TIMESTAMPTZ | NULLABLE | Processing start |
| completed_at | TIMESTAMPTZ | NULLABLE | Processing end |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

### Task Type Values

| Type | Description | Worker |
|------|-------------|--------|
| `thumbnail_generation` | Create WebP derivatives | General |
| `exif_extraction` | Extract metadata | General |
| `face_detection` | Detect faces via GCV | AI |
| `face_embedding` | Generate face embeddings | AI |
| `video_thumbnail` | Extract video frames | General |
| `encryption` | Encrypt file for storage | General |
| `cleanup` | Delete expired uploads | Beat |

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Queued for processing |
| `processing` | Currently executing |
| `completed` | Successfully finished |
| `failed` | Failed after all retries |
| `cancelled` | Manually cancelled |
| `retrying` | Waiting for retry |

### Indexes

```sql
CREATE INDEX idx_task_status ON processing_tasks(status, task_type);
CREATE INDEX idx_task_asset ON processing_tasks(asset_id);
CREATE INDEX idx_task_pending ON processing_tasks(priority DESC, created_at ASC)
    WHERE status = 'pending';
```

---

## 6. EncryptionKey

Tracks workspace encryption keys for rotation support.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(100) | PK | Key identifier (format: `ws-{workspace_id}-v{version}`) |
| workspace_id | UUID | FK → Workspace, NOT NULL, INDEX | Owning workspace |
| key_version | INTEGER | NOT NULL | Key version number |
| algorithm | VARCHAR(50) | NOT NULL, DEFAULT 'AES-256-GCM' | Encryption algorithm |
| key_hash | VARCHAR(64) | NOT NULL | SHA-256 of key (for verification) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Currently active for new encryptions |
| assets_count | INTEGER | NOT NULL, DEFAULT 0 | Assets encrypted with this key |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Key creation |
| rotated_at | TIMESTAMPTZ | NULLABLE | When rotation completed |
| retired_at | TIMESTAMPTZ | NULLABLE | When fully decommissioned |

### Indexes

```sql
CREATE INDEX idx_encryption_key_workspace ON encryption_keys(workspace_id, is_active);
CREATE UNIQUE INDEX idx_encryption_key_version ON encryption_keys(workspace_id, key_version);
```

### Validation Rules

- Only one `is_active = TRUE` per workspace
- `key_version` must be sequential within workspace
- `retired_at` can only be set if `rotated_at` is not null

---

## Database Migrations

### Migration Order

1. `001_create_uploads.py` - Upload table
2. `002_create_assets.py` - Asset table with encryption fields
3. `003_create_asset_metadata.py` - Metadata table
4. `004_create_faces.py` - Face detection table with pgvector
5. `005_create_processing_tasks.py` - Task tracking table
6. `006_create_encryption_keys.py` - Key rotation tracking

### pgvector Setup

```sql
-- Ensure pgvector extension (run once per database)
CREATE EXTENSION IF NOT EXISTS vector;

-- Face embedding index (IVF for approximate nearest neighbor)
CREATE INDEX idx_face_embedding ON faces
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## Relationships Summary

| Parent | Child | Relationship | On Delete |
|--------|-------|--------------|-----------|
| Workspace | Upload | 1:N | CASCADE |
| Workspace | Asset | 1:N | CASCADE |
| Workspace | EncryptionKey | 1:N | CASCADE |
| Upload | Asset | 1:1 | SET NULL |
| Asset | AssetMetadata | 1:1 | CASCADE |
| Asset | Face | 1:N | CASCADE |
| Asset | ProcessingTask | 1:N | CASCADE |
| EncryptionKey | Asset | 1:N | RESTRICT |
