# Data Model: Gallery Service

## Overview

This document defines the complete data model for the Gallery Service microservice, including entities, relationships, fields, validation rules, indexes, and state transitions. The data model enforces workspace-level multi-tenancy with Row-Level Security (RLS) and supports high-traffic gallery viewing with denormalized stats for performance.

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│   Workspace     │         │      Asset       │
│  (existing)     │         │   (existing)     │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │ 1:N                       │
         │                           │ N:1
         ▼                           ▼
┌──────────────────────────────────────────────────┐
│                   Gallery                        │
│  - gallery_id (PK)                               │
│  - workspace_id (FK, indexed)                    │
│  - title, description, client_name               │
│  - status (draft/published/archived)             │
│  - settings (password, email_reg, download)      │
│  - denormalized_stats (photo_count, etc.)        │
└────────┬─────────────────────┬───────────────────┘
         │ 1:N                 │ 1:N
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────────────┐
│  Sub-Gallery    │   │     Share Link          │
│  - sub_gallery  │   │     (Magic Link)        │
│    _id (PK)     │   │  - link_id (PK)         │
│  - gallery_id   │   │  - gallery_id (FK)      │
│  - name         │   │  - target_type, status  │
│  - sort_order   │   │  - expires_at, access   │
│  - visible      │   │  - policies, QR config  │
└────────┬────────┘   └─────────────────────────┘
         │ 1:N                 │ tracking
         │                     ▼
         ▼            ┌─────────────────────────┐
┌─────────────────┐  │   Gallery Visitor       │
│ Gallery Asset   │  │   (Access Log)          │
│  - gallery_     │  │  - gallery_visitor_id   │
│    asset_id     │  │  - visitor_id (FK)      │
│  - gallery_id   ├──┤  - gallery_id (FK)      │
│  - asset_id     │  │  - link_id (FK)         │
│  - sub_gallery  │  │  - accessed_at, ip      │
│    _id (FK)     │  └──────────┬──────────────┘
│  - visible      │             │ N:1
│  - is_private   │             ▼
│  - tags, meta   │    ┌─────────────────────┐
└─────────────────┘    │      Visitor        │
                       │   (Lead Capture)    │
                       │  - visitor_id (PK)  │
                       │  - workspace_id     │
                       │  - email (unique)   │
                       │  - name, phone, etc │
                       └─────────────────────┘

In-Memory (Not Persisted):
┌─────────────────────────┐
│  WebSocket Connection   │
│  - connection_id        │
│  - gallery_id           │
│  - client_type          │
│  - connected_at         │
│  (Prometheus metrics)   │
└─────────────────────────┘
```

## Core Entities

### 1. Gallery

**Purpose**: Core container for photos and videos with workspace-level isolation. Represents a photographer's project (e.g., "Smith Wedding - June 2026").

**Table**: `galleries`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `gallery_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `workspace_id` | UUID | NOT NULL, FOREIGN KEY → workspaces.workspace_id | Multi-tenant isolation |
| `title` | VARCHAR(255) | NOT NULL | Gallery display name (e.g., "Smith Wedding") |
| `description` | TEXT | NULLABLE | Optional markdown description for clients |
| `client_name` | VARCHAR(255) | NULLABLE | Client name for sorting/filtering |
| `shoot_date` | DATE | NULLABLE | Shoot date for chronological organization |
| `status` | ENUM | NOT NULL, DEFAULT 'draft' | draft \| published \| archived |
| `cover_asset_id` | UUID | NULLABLE, FOREIGN KEY → assets.asset_id | Cover image for gallery thumbnail |
| `password_protected` | BOOLEAN | NOT NULL, DEFAULT false | Whether password is required |
| `password_hash` | TEXT | NULLABLE | Argon2id hash (only if password_protected = true) |
| `pin_protected` | BOOLEAN | NOT NULL, DEFAULT false | Whether private photos have PIN |
| `email_registration_required` | BOOLEAN | NOT NULL, DEFAULT false | Whether email modal appears |
| `expires_at` | TIMESTAMP | NULLABLE | Expiration date (NULL = never expires) |
| `download_policy` | ENUM | NOT NULL, DEFAULT 'VIEW_ONLY' | VIEW_ONLY \| WEB_ONLY \| WATERMARKED_ONLY \| ORIGINAL_ALLOWED |
| `layout_style` | ENUM | NOT NULL, DEFAULT 'tab' | tab \| continuous_scroll |
| `theme` | VARCHAR(50) | NOT NULL, DEFAULT 'light' | light \| dark \| photographer-brand |
| `photo_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `video_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `favorites_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `total_size_bytes` | BIGINT | NOT NULL, DEFAULT 0 | Denormalized total (updated via trigger) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp (auto-updated) |
| `created_by` | UUID | NOT NULL, FOREIGN KEY → users.user_id | User who created gallery |
| `metadata` | JSONB | NULLABLE, DEFAULT '{}' | Flexible metadata (location, tags, custom fields) |

**Indexes**:
```sql
CREATE INDEX idx_galleries_workspace_id ON galleries(workspace_id);
CREATE INDEX idx_galleries_status ON galleries(status) WHERE status = 'published';
CREATE INDEX idx_galleries_shoot_date ON galleries(shoot_date DESC);
CREATE INDEX idx_galleries_client_name ON galleries(client_name);
CREATE INDEX idx_galleries_created_at ON galleries(created_at DESC);
```

**Row-Level Security (RLS)**:
```sql
ALTER TABLE galleries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access galleries in their workspaces
CREATE POLICY galleries_workspace_isolation ON galleries
  FOR ALL
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = current_user_id()
  ));
```

**Database Triggers**:
```sql
-- Trigger: Update updated_at on every row modification
CREATE TRIGGER update_galleries_updated_at
  BEFORE UPDATE ON galleries
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Update denormalized stats when gallery_assets changes
CREATE TRIGGER update_gallery_stats_on_asset_insert
  AFTER INSERT ON gallery_assets
  FOR EACH ROW
  EXECUTE FUNCTION update_gallery_stats();

CREATE TRIGGER update_gallery_stats_on_asset_delete
  AFTER DELETE ON gallery_assets
  FOR EACH ROW
  EXECUTE FUNCTION update_gallery_stats();
```

**State Transitions**:
```
draft → published → archived
  │         │
  └─────────┘ (bidirectional: can unpublish)
```

**Validation Rules**:
- `title`: Must be 1-255 characters, non-empty after trimming
- `password_hash`: Required if `password_protected = true`, must be Argon2id format
- `expires_at`: Must be in the future when set
- `cover_asset_id`: Must reference an asset that exists in this gallery
- `download_policy`: Cannot be expanded by share links (only restricted further)

---

### 2. Sub-Gallery (Section)

**Purpose**: First-class organization unit within a gallery for grouping photos by theme/timeline (e.g., "Ceremony", "Reception", "Portraits").

**Table**: `sub_galleries`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `sub_gallery_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `gallery_id` | UUID | NOT NULL, FOREIGN KEY → galleries.gallery_id ON DELETE CASCADE | Parent gallery |
| `name` | VARCHAR(255) | NOT NULL | Section name (e.g., "Pre-Wedding Photos") |
| `description` | TEXT | NULLABLE | Optional description for the section |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | Display order (ascending) |
| `visible` | BOOLEAN | NOT NULL, DEFAULT true | Whether section is visible to clients |
| `cover_asset_id` | UUID | NULLABLE, FOREIGN KEY → assets.asset_id | Cover image for tab thumbnail |
| `photo_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
```sql
CREATE INDEX idx_sub_galleries_gallery_id ON sub_galleries(gallery_id);
CREATE INDEX idx_sub_galleries_sort_order ON sub_galleries(gallery_id, sort_order);
CREATE UNIQUE INDEX idx_sub_galleries_name_per_gallery ON sub_galleries(gallery_id, name);
```

**Validation Rules**:
- `name`: Must be unique within a gallery, 1-255 characters
- `sort_order`: Must be >= 0, determines tab order or section sequence
- `cover_asset_id`: Must reference an asset assigned to this sub-gallery

**Default Sub-Gallery**:
```sql
-- Trigger: Create "All Photos" sub-gallery when gallery is created
CREATE TRIGGER create_default_sub_gallery
  AFTER INSERT ON galleries
  FOR EACH ROW
  EXECUTE FUNCTION create_default_sub_gallery_for_gallery();
```

---

### 3. Share Link (Magic Link)

**Purpose**: Capability-based access grant with fine-grained permissions and time-boxing. Enables passwordless gallery access via unique URLs.

**Table**: `share_links`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `link_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier (part of URL) |
| `gallery_id` | UUID | NOT NULL, FOREIGN KEY → galleries.gallery_id ON DELETE CASCADE | Parent gallery |
| `label` | VARCHAR(255) | NOT NULL | Human-readable name (e.g., "Bride & Groom Link") |
| `target_type` | ENUM | NOT NULL, DEFAULT 'gallery' | gallery \| sub_gallery \| photo |
| `target_id` | UUID | NULLABLE | ID of target (sub_gallery_id or asset_id) |
| `status` | ENUM | NOT NULL, DEFAULT 'active' | active \| expired \| revoked |
| `expires_at` | TIMESTAMP | NULLABLE | Expiration date (NULL = never expires) |
| `max_accesses` | INTEGER | NULLABLE | Max number of unique accesses (NULL = unlimited) |
| `access_count` | INTEGER | NOT NULL, DEFAULT 0 | Current access count (atomically incremented) |
| `password_required` | BOOLEAN | NOT NULL, DEFAULT false | Override gallery password setting |
| `email_registration_required` | BOOLEAN | NOT NULL, DEFAULT false | Override gallery email reg setting |
| `allowed_actions` | TEXT[] | NOT NULL, DEFAULT '{view}' | Array: view, favorite, select, comment, download |
| `download_variant` | ENUM | NULLABLE | web \| watermarked \| original (NULL = use gallery policy) |
| `qr_code_size` | INTEGER | NOT NULL, DEFAULT 300 | QR code pixel size (300x300) |
| `qr_code_color` | VARCHAR(7) | NOT NULL, DEFAULT '#000000' | QR code color (hex) |
| `qr_code_logo_enabled` | BOOLEAN | NOT NULL, DEFAULT true | Whether to embed logo in center |
| `qr_code_error_correction` | ENUM | NOT NULL, DEFAULT 'M' | L \| M \| Q \| H (error correction level) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `created_by` | UUID | NOT NULL, FOREIGN KEY → users.user_id | User who created link |
| `last_accessed_at` | TIMESTAMP | NULLABLE | Last access timestamp |

**Indexes**:
```sql
CREATE INDEX idx_share_links_gallery_id ON share_links(gallery_id);
CREATE INDEX idx_share_links_status ON share_links(status) WHERE status = 'active';
CREATE INDEX idx_share_links_expires_at ON share_links(expires_at) WHERE expires_at IS NOT NULL;
```

**Validation Rules**:
- `target_type = 'sub_gallery'` → `target_id` must reference valid sub_gallery_id
- `target_type = 'photo'` → `target_id` must reference valid asset_id in this gallery
- `target_type = 'gallery'` → `target_id` must be NULL
- `expires_at`: Must be in the future when set
- `max_accesses`: Must be > 0 if set
- `access_count`: Must be <= max_accesses (enforced in application logic)
- `download_variant`: Can only restrict, not expand gallery download_policy

**State Transitions**:
```
active → expired (automatic when expires_at is reached or max_accesses exceeded)
active → revoked (manual action by photographer)
```

**Access Count Atomicity**:
```sql
-- Application code must use atomic increment
UPDATE share_links
SET access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP
WHERE link_id = $1 AND status = 'active'
  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
  AND (max_accesses IS NULL OR access_count < max_accesses)
RETURNING *;
```

---

### 4. Gallery Asset

**Purpose**: Junction entity linking assets to galleries with per-gallery metadata. Supports multiple galleries sharing the same asset with different visibility/privacy settings.

**Table**: `gallery_assets`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `gallery_asset_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `gallery_id` | UUID | NOT NULL, FOREIGN KEY → galleries.gallery_id ON DELETE CASCADE | Parent gallery |
| `asset_id` | UUID | NOT NULL, FOREIGN KEY → assets.asset_id ON DELETE CASCADE | Referenced asset |
| `sub_gallery_id` | UUID | NULLABLE, FOREIGN KEY → sub_galleries.sub_gallery_id ON DELETE SET NULL | Section assignment |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | Display order within sub-gallery |
| `visible` | BOOLEAN | NOT NULL, DEFAULT true | Whether photo is visible to clients |
| `is_private` | BOOLEAN | NOT NULL, DEFAULT false | Whether PIN is required to view |
| `pin_hash` | TEXT | NULLABLE | Argon2id hash (only if is_private = true) |
| `title` | VARCHAR(255) | NULLABLE | Override asset title for this gallery |
| `description` | TEXT | NULLABLE | Override asset description for this gallery |
| `tags` | TEXT[] | NOT NULL, DEFAULT '{}' | Gallery-specific tags (e.g., ["bride", "ceremony"]) |
| `favorites_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `selections_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count (updated via trigger) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
```sql
CREATE INDEX idx_gallery_assets_gallery_id ON gallery_assets(gallery_id);
CREATE INDEX idx_gallery_assets_asset_id ON gallery_assets(asset_id);
CREATE INDEX idx_gallery_assets_sub_gallery ON gallery_assets(sub_gallery_id, sort_order);
CREATE INDEX idx_gallery_assets_visible ON gallery_assets(gallery_id, visible);
CREATE UNIQUE INDEX idx_gallery_assets_unique_pair ON gallery_assets(gallery_id, asset_id);
```

**Validation Rules**:
- `(gallery_id, asset_id)`: Must be unique (one asset can appear once per gallery)
- `pin_hash`: Required if `is_private = true`, must be Argon2id format
- `sub_gallery_id`: Must reference a sub-gallery in the same gallery
- `tags`: Each tag must be 1-50 characters, no duplicates

**Asset Metadata (from `assets` table)**:
The Gallery Service reads metadata from the existing `assets` table:
- `type`: photo | video
- `width`, `height`: Dimensions in pixels
- `mime_type`: image/jpeg, image/png, image/webp, video/mp4, etc.
- `file_size`: Size in bytes
- `date_taken`: Original capture date (from EXIF)
- `lqip`: Base64-encoded WebP data URI (16x16, ~100-200 bytes)
- `exif_data`: JSONB with camera model, ISO, aperture, etc.

---

### 5. Visitor (Lead Capture)

**Purpose**: Stores visitor information collected via email registration modal. Subject to GDPR/CCPA deletion requests.

**Table**: `visitors`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `visitor_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `workspace_id` | UUID | NOT NULL, FOREIGN KEY → workspaces.workspace_id | Multi-tenant isolation |
| `email` | VARCHAR(255) | NOT NULL | Visitor email address |
| `name` | VARCHAR(255) | NULLABLE | Full name |
| `phone` | VARCHAR(50) | NULLABLE | Phone number (E.164 format recommended) |
| `address` | TEXT | NULLABLE | Mailing address (optional) |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | Custom fields (e.g., {"referral_source": "Instagram"}) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
```sql
CREATE INDEX idx_visitors_workspace_id ON visitors(workspace_id);
CREATE UNIQUE INDEX idx_visitors_email_per_workspace ON visitors(workspace_id, LOWER(email));
CREATE INDEX idx_visitors_created_at ON visitors(created_at DESC);
```

**Validation Rules**:
- `email`: Must be valid RFC 5322 format, unique per workspace (case-insensitive)
- `phone`: Must be valid E.164 format if provided (e.g., +14155552671)
- `metadata`: JSON object, max 10KB

**Privacy Compliance**:
- **GDPR Right to Erasure**: Application must implement `DELETE FROM visitors WHERE visitor_id = $1`
- **Data Retention**: Visitors table should have configurable TTL (e.g., 2 years) for inactive records
- **Consent Tracking**: `metadata` should store consent timestamp and version (e.g., {"consent_at": "2026-01-14T12:00:00Z", "consent_version": "v1"})

---

### 6. Gallery Visitor (Access Log)

**Purpose**: Tracks which visitors accessed which galleries via Magic Links. Used for analytics, lead scoring, and security auditing.

**Table**: `gallery_visitors`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `gallery_visitor_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `visitor_id` | UUID | NOT NULL, FOREIGN KEY → visitors.visitor_id ON DELETE CASCADE | Visitor who accessed |
| `gallery_id` | UUID | NOT NULL, FOREIGN KEY → galleries.gallery_id ON DELETE CASCADE | Gallery accessed |
| `link_id` | UUID | NOT NULL, FOREIGN KEY → share_links.link_id ON DELETE CASCADE | Magic Link used |
| `accessed_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Access timestamp |
| `ip_address` | INET | NULLABLE | Client IP address (IPv4 or IPv6) |
| `user_agent` | TEXT | NULLABLE | Client User-Agent header |
| `referrer` | TEXT | NULLABLE | HTTP Referer header (e.g., Instagram, Facebook) |

**Indexes**:
```sql
CREATE INDEX idx_gallery_visitors_visitor_id ON gallery_visitors(visitor_id);
CREATE INDEX idx_gallery_visitors_gallery_id ON gallery_visitors(gallery_id);
CREATE INDEX idx_gallery_visitors_link_id ON gallery_visitors(link_id);
CREATE INDEX idx_gallery_visitors_accessed_at ON gallery_visitors(accessed_at DESC);
CREATE INDEX idx_gallery_visitors_ip_address ON gallery_visitors(ip_address);
```

**Validation Rules**:
- `ip_address`: Must be valid IPv4 or IPv6 address
- `user_agent`: Max 1024 characters (truncate if longer)

**Analytics Use Cases**:
- **Lead Scoring**: Count unique galleries viewed per visitor
- **Engagement Tracking**: Track time between first and last access
- **Referral Analysis**: Aggregate by `referrer` to see traffic sources
- **Security Auditing**: Detect suspicious access patterns (e.g., 100 accesses from same IP in 1 minute)

---

### 7. WebSocket Connection (In-Memory State)

**Purpose**: Represents active real-time connections for live proofing. Not persisted to database - tracked in-memory for WebSocket manager.

**Data Structure**:
```python
@dataclass
class WebSocketConnection:
    connection_id: str          # UUID generated on connect
    gallery_id: str             # Gallery being viewed
    client_type: str            # "staff" | "client"
    websocket: WebSocket        # FastAPI WebSocket object
    connected_at: datetime      # Connection timestamp
    last_activity: datetime     # Last message received timestamp
    sequence_number: int        # Last event sequence number received
```

**Manager State**:
```python
class ProofingConnectionManager:
    # In-memory mapping: gallery_id → set of WebSocketConnection
    active_connections: dict[str, set[WebSocketConnection]]

    # Prometheus metrics
    websocket_active_connections = Gauge(
        'websocket_active_connections',
        'Number of active WebSocket connections',
        ['gallery_id']
    )
```

**Events**:
```python
@dataclass
class WebSocketEvent:
    event_id: str               # UUID for idempotency
    event_type: str             # "favorite_added" | "selection_added" | "comment_added"
    gallery_id: str             # Gallery where event occurred
    asset_id: str               # Asset affected
    user_id: Optional[str]      # Staff user (None for clients)
    visitor_id: Optional[str]   # Visitor (None for staff)
    timestamp: datetime         # Event timestamp
    sequence_number: int        # Global sequence number for sync
    payload: dict               # Event-specific data
```

**Lifecycle**:
1. **Connect**: Client opens WebSocket at `/ws/gallery/{gallery_id}`, manager adds to `active_connections`
2. **Subscribe**: Manager subscribes to Redis channel `gallery:{gallery_id}:proofing`
3. **Broadcast**: When event occurs, publish to Redis → all pods receive → forward to local WebSocket clients
4. **Disconnect**: Client closes WebSocket, manager removes from `active_connections` and updates Prometheus gauge
5. **Reconnect**: Client reconnects with `lastSeq` parameter, server sends missed events since that sequence number

---

## Supporting Tables

### Security Audit Log

**Purpose**: Track all security-relevant events (password attempts, PIN attempts, rate limit violations).

**Table**: `security_audit_log`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `audit_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| `workspace_id` | UUID | NOT NULL | Multi-tenant isolation |
| `event_type` | VARCHAR(100) | NOT NULL | password_attempt, pin_attempt, rate_limit_exceeded, etc. |
| `gallery_id` | UUID | NULLABLE | Gallery involved (if applicable) |
| `link_id` | UUID | NULLABLE | Magic Link involved (if applicable) |
| `ip_address` | INET | NOT NULL | Client IP address |
| `user_agent` | TEXT | NULLABLE | Client User-Agent |
| `success` | BOOLEAN | NOT NULL | Whether attempt succeeded |
| `details` | JSONB | NOT NULL, DEFAULT '{}' | Event-specific details |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Event timestamp |

**Indexes**:
```sql
CREATE INDEX idx_security_audit_workspace ON security_audit_log(workspace_id);
CREATE INDEX idx_security_audit_ip ON security_audit_log(ip_address, created_at DESC);
CREATE INDEX idx_security_audit_event_type ON security_audit_log(event_type);
CREATE INDEX idx_security_audit_created_at ON security_audit_log(created_at DESC);
```

**Retention Policy**:
```sql
-- Partition by month for efficient deletion of old logs
CREATE TABLE security_audit_log_y2026m01 PARTITION OF security_audit_log
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Denormalization Strategy

### Gallery Stats (FR-024)

Gallery table maintains denormalized stats updated via database triggers:

| Field | Source | Update Trigger |
|-------|--------|----------------|
| `photo_count` | `SELECT COUNT(*) FROM gallery_assets WHERE gallery_id = X AND visible = true AND asset.type = 'photo'` | After INSERT/UPDATE/DELETE on gallery_assets |
| `video_count` | `SELECT COUNT(*) FROM gallery_assets WHERE gallery_id = X AND visible = true AND asset.type = 'video'` | After INSERT/UPDATE/DELETE on gallery_assets |
| `favorites_count` | `SELECT SUM(favorites_count) FROM gallery_assets WHERE gallery_id = X` | After UPDATE on gallery_assets.favorites_count |
| `total_size_bytes` | `SELECT SUM(assets.file_size) FROM gallery_assets JOIN assets WHERE gallery_id = X` | After INSERT/DELETE on gallery_assets |

**Trigger Implementation**:
```sql
CREATE OR REPLACE FUNCTION update_gallery_stats()
RETURNS TRIGGER AS $$
BEGIN
  -- Recalculate stats for affected gallery
  UPDATE galleries
  SET
    photo_count = (
      SELECT COUNT(*)
      FROM gallery_assets ga
      JOIN assets a ON ga.asset_id = a.asset_id
      WHERE ga.gallery_id = COALESCE(NEW.gallery_id, OLD.gallery_id)
        AND ga.visible = true
        AND a.type = 'photo'
    ),
    video_count = (
      SELECT COUNT(*)
      FROM gallery_assets ga
      JOIN assets a ON ga.asset_id = a.asset_id
      WHERE ga.gallery_id = COALESCE(NEW.gallery_id, OLD.gallery_id)
        AND ga.visible = true
        AND a.type = 'video'
    ),
    favorites_count = (
      SELECT COALESCE(SUM(ga.favorites_count), 0)
      FROM gallery_assets ga
      WHERE ga.gallery_id = COALESCE(NEW.gallery_id, OLD.gallery_id)
    ),
    total_size_bytes = (
      SELECT COALESCE(SUM(a.file_size), 0)
      FROM gallery_assets ga
      JOIN assets a ON ga.asset_id = a.asset_id
      WHERE ga.gallery_id = COALESCE(NEW.gallery_id, OLD.gallery_id)
    ),
    updated_at = CURRENT_TIMESTAMP
  WHERE gallery_id = COALESCE(NEW.gallery_id, OLD.gallery_id);

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

### Sub-Gallery Photo Count

Sub-gallery table maintains `photo_count` updated similarly:

```sql
CREATE TRIGGER update_sub_gallery_photo_count
  AFTER INSERT OR UPDATE OR DELETE ON gallery_assets
  FOR EACH ROW
  WHEN (NEW.sub_gallery_id IS NOT NULL OR OLD.sub_gallery_id IS NOT NULL)
  EXECUTE FUNCTION update_sub_gallery_photo_count();
```

---

## Caching Strategy (FR-023)

### Redis Cache Keys

| Cache Key | Value | TTL | Invalidation |
|-----------|-------|-----|--------------|
| `gallery:{gallery_id}:metadata` | Gallery object (JSON) | 5 minutes | On gallery UPDATE |
| `gallery:{gallery_id}:photos:page:{cursor}` | Paginated photos (JSON array) | 10 minutes | On gallery_assets INSERT/UPDATE/DELETE |
| `gallery:{gallery_id}:stats` | Stats object (photo_count, etc.) | 5 minutes | On gallery_assets change (trigger updates cache) |
| `share_link:{link_id}:status` | Share link status (active/expired/revoked) | 1 hour | On share_links UPDATE |
| `visitor:{email}:galleries` | Set of gallery_ids visited | 24 hours | On gallery_visitors INSERT |

**Cache Population Pattern**:
```python
async def get_gallery_metadata(gallery_id: str) -> dict:
    cache_key = f"gallery:{gallery_id}:metadata"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss: fetch from database
    async with get_db_session() as db:
        gallery = await db.get(Gallery, gallery_id)
        if not gallery:
            raise HTTPException(status_code=404, detail="Gallery not found")

        metadata = gallery.to_dict()

        # Populate cache with 5-minute TTL
        await redis.setex(cache_key, 300, json.dumps(metadata))

        return metadata
```

**Cache Invalidation**:
```python
# After updating gallery
async def update_gallery(gallery_id: str, updates: dict):
    async with get_db_session() as db:
        gallery = await db.get(Gallery, gallery_id)
        for key, value in updates.items():
            setattr(gallery, key, value)
        await db.commit()

    # Invalidate cache
    await redis.delete(f"gallery:{gallery_id}:metadata")
    await redis.delete(f"gallery:{gallery_id}:stats")
```

---

## Performance Indexes

### Query Patterns and Corresponding Indexes

| Query Pattern | Index |
|---------------|-------|
| List galleries by workspace, sorted by shoot date | `idx_galleries_workspace_id`, `idx_galleries_shoot_date` |
| Find published galleries | `idx_galleries_status` (partial index WHERE status = 'published') |
| Search galleries by client name | `idx_galleries_client_name` (consider GIN index for prefix search) |
| Get gallery assets by sub-gallery, sorted | `idx_gallery_assets_sub_gallery` (composite: sub_gallery_id, sort_order) |
| Find visible photos in gallery | `idx_gallery_assets_visible` (composite: gallery_id, visible) |
| Look up share link by link_id | Primary key lookup (no additional index needed) |
| Find active share links for gallery | `idx_share_links_gallery_id`, `idx_share_links_status` |
| Track visitor access by email | `idx_visitors_email_per_workspace` (unique index, case-insensitive) |
| Audit log by IP and time range | `idx_security_audit_ip` (composite: ip_address, created_at DESC) |

### Composite Indexes for Sorting

```sql
-- Gallery assets sorted within sub-gallery
CREATE INDEX idx_gallery_assets_sub_gallery_sort
  ON gallery_assets(sub_gallery_id, sort_order)
  WHERE visible = true;

-- Gallery visitors for analytics (recent first)
CREATE INDEX idx_gallery_visitors_gallery_time
  ON gallery_visitors(gallery_id, accessed_at DESC);
```

---

## Migration Strategy

### Initial Schema Migration

```sql
-- migrations/001_create_galleries_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Galleries table
CREATE TABLE galleries (
  gallery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  client_name VARCHAR(255),
  shoot_date DATE,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'published', 'archived')),
  cover_asset_id UUID REFERENCES assets(asset_id),
  password_protected BOOLEAN NOT NULL DEFAULT false,
  password_hash TEXT,
  pin_protected BOOLEAN NOT NULL DEFAULT false,
  email_registration_required BOOLEAN NOT NULL DEFAULT false,
  expires_at TIMESTAMP,
  download_policy VARCHAR(50) NOT NULL DEFAULT 'VIEW_ONLY'
    CHECK (download_policy IN ('VIEW_ONLY', 'WEB_ONLY', 'WATERMARKED_ONLY', 'ORIGINAL_ALLOWED')),
  layout_style VARCHAR(20) NOT NULL DEFAULT 'tab'
    CHECK (layout_style IN ('tab', 'continuous_scroll')),
  theme VARCHAR(50) NOT NULL DEFAULT 'light',
  photo_count INTEGER NOT NULL DEFAULT 0,
  video_count INTEGER NOT NULL DEFAULT 0,
  favorites_count INTEGER NOT NULL DEFAULT 0,
  total_size_bytes BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by UUID NOT NULL REFERENCES users(user_id),
  metadata JSONB NOT NULL DEFAULT '{}'
);

-- Sub-galleries table
CREATE TABLE sub_galleries (
  sub_gallery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gallery_id UUID NOT NULL REFERENCES galleries(gallery_id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  visible BOOLEAN NOT NULL DEFAULT true,
  cover_asset_id UUID REFERENCES assets(asset_id),
  photo_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (gallery_id, name)
);

-- Share links table
CREATE TABLE share_links (
  link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gallery_id UUID NOT NULL REFERENCES galleries(gallery_id) ON DELETE CASCADE,
  label VARCHAR(255) NOT NULL,
  target_type VARCHAR(20) NOT NULL DEFAULT 'gallery'
    CHECK (target_type IN ('gallery', 'sub_gallery', 'photo')),
  target_id UUID,
  status VARCHAR(20) NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'expired', 'revoked')),
  expires_at TIMESTAMP,
  max_accesses INTEGER,
  access_count INTEGER NOT NULL DEFAULT 0,
  password_required BOOLEAN NOT NULL DEFAULT false,
  email_registration_required BOOLEAN NOT NULL DEFAULT false,
  allowed_actions TEXT[] NOT NULL DEFAULT '{view}',
  download_variant VARCHAR(20)
    CHECK (download_variant IN ('web', 'watermarked', 'original')),
  qr_code_size INTEGER NOT NULL DEFAULT 300,
  qr_code_color VARCHAR(7) NOT NULL DEFAULT '#000000',
  qr_code_logo_enabled BOOLEAN NOT NULL DEFAULT true,
  qr_code_error_correction VARCHAR(1) NOT NULL DEFAULT 'M'
    CHECK (qr_code_error_correction IN ('L', 'M', 'Q', 'H')),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by UUID NOT NULL REFERENCES users(user_id),
  last_accessed_at TIMESTAMP
);

-- Gallery assets junction table
CREATE TABLE gallery_assets (
  gallery_asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gallery_id UUID NOT NULL REFERENCES galleries(gallery_id) ON DELETE CASCADE,
  asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
  sub_gallery_id UUID REFERENCES sub_galleries(sub_gallery_id) ON DELETE SET NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  visible BOOLEAN NOT NULL DEFAULT true,
  is_private BOOLEAN NOT NULL DEFAULT false,
  pin_hash TEXT,
  title VARCHAR(255),
  description TEXT,
  tags TEXT[] NOT NULL DEFAULT '{}',
  favorites_count INTEGER NOT NULL DEFAULT 0,
  selections_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (gallery_id, asset_id)
);

-- Visitors table
CREATE TABLE visitors (
  visitor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  phone VARCHAR(50),
  address TEXT,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (workspace_id, LOWER(email))
);

-- Gallery visitors access log
CREATE TABLE gallery_visitors (
  gallery_visitor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visitor_id UUID NOT NULL REFERENCES visitors(visitor_id) ON DELETE CASCADE,
  gallery_id UUID NOT NULL REFERENCES galleries(gallery_id) ON DELETE CASCADE,
  link_id UUID NOT NULL REFERENCES share_links(link_id) ON DELETE CASCADE,
  accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address INET,
  user_agent TEXT,
  referrer TEXT
);

-- Security audit log
CREATE TABLE security_audit_log (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  gallery_id UUID,
  link_id UUID,
  ip_address INET NOT NULL,
  user_agent TEXT,
  success BOOLEAN NOT NULL,
  details JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create all indexes (see above sections)
-- Create all triggers (see above sections)
-- Enable RLS policies (see above sections)
```

---

## Summary

The Gallery Service data model provides:

1. **Multi-Tenancy**: All tables enforce workspace-level isolation via RLS
2. **Performance**: Denormalized stats, strategic indexes, Redis caching
3. **Security**: Argon2id password hashing, rate limiting, audit logging
4. **Scalability**: Cursor-based pagination, WebSocket connection tracking for KEDA
5. **Flexibility**: JSONB metadata fields, extensible tag arrays
6. **Data Integrity**: Foreign key constraints, check constraints, unique indexes

Next steps: Generate API contracts in `/contracts/` directory based on functional requirements.
