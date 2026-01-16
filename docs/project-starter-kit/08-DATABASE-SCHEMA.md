# RawDrive Database Schema

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Database Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Primary Database** | PostgreSQL 16 | Relational data storage |
| **Vector Extension** | pgvector + pgvectorscale | AI embeddings, similarity search |
| **Connection Pooler** | PgBouncer 1.21+ | Connection management |
| **Cache** | Redis 7 | Sessions, caching, queues |
| **Vector DB** | Milvus | High-performance face embeddings |

**Docker Image:** `timescale/timescaledb-ha:pg16` (includes pgvector + pgvectorscale)

---

## Core Concepts

### Multi-Tenancy

**CRITICAL:** Every table with customer data MUST include `workspace_id`:

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    -- other columns
    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Every query MUST filter by workspace_id
CREATE INDEX idx_assets_workspace ON assets(workspace_id);
```

### UUID Primary Keys

All tables use UUID primary keys for security and distributed systems:

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

### Timestamps

All tables include audit timestamps:

```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

---

## Core Tables

### Workspaces (Tenants)

```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id),

    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'free',
    storage_limit_bytes BIGINT DEFAULT 1073741824, -- 1GB
    gallery_limit INTEGER DEFAULT 3,

    -- Settings
    settings JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

### Users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),

    -- Authentication
    email_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Workspace Members

```sql
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member',

    -- Permissions
    permissions JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(workspace_id, user_id)
);
```

### Galleries

```sql
CREATE TABLE galleries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(100),

    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    visibility VARCHAR(50) DEFAULT 'private',

    -- Settings
    settings JSONB DEFAULT '{}',

    -- Branding
    gradient_start VARCHAR(7),
    gradient_end VARCHAR(7),
    logo_url VARCHAR(500),

    -- Security
    pin_code VARCHAR(10),
    password_hash VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Denormalized Stats (v0.3.2)
    photo_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(workspace_id, slug)
);

CREATE INDEX idx_galleries_workspace ON galleries(workspace_id);
CREATE INDEX idx_galleries_status ON galleries(workspace_id, status);
```

### Assets

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    gallery_id UUID REFERENCES galleries(id),

    -- File Info
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,

    -- Storage
    storage_key VARCHAR(1000) NOT NULL,
    thumbnail_key VARCHAR(1000),
    lqip VARCHAR(2000), -- Low Quality Image Placeholder (v0.3.2)

    -- Metadata
    width INTEGER,
    height INTEGER,
    duration_seconds FLOAT, -- For video
    exif_data JSONB DEFAULT '{}',

    -- AI Analysis
    quality_score FLOAT,
    tags JSONB DEFAULT '[]',
    description TEXT,
    ai_metadata JSONB DEFAULT '{}',

    -- Vector Embedding
    embedding vector(512), -- pgvector

    -- Status
    status VARCHAR(50) DEFAULT 'processing',
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_assets_workspace ON assets(workspace_id);
CREATE INDEX idx_assets_gallery ON assets(gallery_id);
CREATE INDEX idx_assets_status ON assets(workspace_id, status);
CREATE INDEX idx_assets_embedding ON assets USING hnsw (embedding vector_cosine_ops);
```

### Clients

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Contact Info
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Status
    status VARCHAR(50) DEFAULT 'active',

    -- Metadata
    notes TEXT,
    custom_fields JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_clients_workspace ON clients(workspace_id);
CREATE INDEX idx_clients_email ON clients(workspace_id, email);
```

### Selections (Client Favorites)

```sql
CREATE TABLE selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    gallery_id UUID NOT NULL REFERENCES galleries(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    client_id UUID REFERENCES clients(id),

    -- Selection Type
    selection_type VARCHAR(50) DEFAULT 'favorite',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(gallery_id, asset_id, client_id)
);
```

### Comments

```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    asset_id UUID NOT NULL REFERENCES assets(id),

    -- Author
    user_id UUID REFERENCES users(id),
    client_id UUID REFERENCES clients(id),
    author_name VARCHAR(255),

    -- Content
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,

    -- Status
    status VARCHAR(50) DEFAULT 'open',
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Face Recognition Tables

### People

```sql
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Identity
    name VARCHAR(255),
    is_named BOOLEAN DEFAULT FALSE,

    -- Stats
    face_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_people_workspace ON people(workspace_id);
```

### Faces

```sql
CREATE TABLE faces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    person_id UUID REFERENCES people(id),

    -- Bounding Box
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,

    -- Embedding (512-dimensional for ArcFace)
    embedding vector(512),

    -- Quality
    confidence FLOAT,
    quality_score FLOAT,

    -- Attributes
    attributes JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_faces_workspace ON faces(workspace_id);
CREATE INDEX idx_faces_person ON faces(person_id);
CREATE INDEX idx_faces_embedding ON faces USING hnsw (embedding vector_cosine_ops);
```

---

## Webhook Tables (v0.3.2)

### Webhook Subscriptions

```sql
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Endpoint
    url VARCHAR(2048) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    previous_secret VARCHAR(255), -- For rotation grace period
    secret_rotated_at TIMESTAMP WITH TIME ZONE,

    -- Configuration
    events JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    max_retries INTEGER DEFAULT 5,

    -- Circuit Breaker
    failure_count INTEGER DEFAULT 0,
    circuit_open_until TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Webhook Deliveries

```sql
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES webhook_subscriptions(id),

    -- Event
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,

    -- Delivery Status
    status VARCHAR(50) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,

    -- Response
    response_status INTEGER,
    response_body TEXT,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deliveries_status ON webhook_deliveries(status, next_retry_at);
```

---

## Personal Profile Tables (v0.3.2)

### Personal Profiles

```sql
CREATE TABLE personal_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Identity
    slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    tagline VARCHAR(500),
    bio TEXT,

    -- Contact
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(500),

    -- Location
    address JSONB DEFAULT '{}',
    service_areas JSONB DEFAULT '[]',

    -- Social Links
    social_links JSONB DEFAULT '{}',

    -- Branding
    brand_theme VARCHAR(50) DEFAULT 'minimal',
    brand_color VARCHAR(7),

    -- Visibility
    is_public BOOLEAN DEFAULT FALSE,
    field_visibility JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Migrations

### Alembic Configuration

Migrations are managed with Alembic in `backend/migrations/versions/`.

**Run migrations:**
```bash
docker exec RawDrive-backend alembic upgrade head
```

**Create new migration:**
```bash
docker exec RawDrive-backend alembic revision --autogenerate -m "description"
```

**Downgrade:**
```bash
docker exec RawDrive-backend alembic downgrade -1
```

### Migration Naming

```
{revision_number}_{description}.py

Example: 0156_add_notification_categories.py
```

### Current Migrations (v0.3.3)

| Range | Description |
|-------|-------------|
| 0001-0050 | Core schema (users, workspaces, galleries, assets) |
| 0051-0092 | Features (clients, selections, comments) |
| 0093-0100 | Subscriptions and payments |
| 0101-0140 | AI features, face recognition |
| 0141-0145 | Workspace settings |
| 0146-0149 | Gallery performance (LQIP, stats) |
| 0150-0153 | Webhooks |
| 0154-0156 | SEO, personal profiles |

---

## Vector Search Indexes

### Index Selection

| Dataset Size | Index Type | Use Case |
|--------------|------------|----------|
| < 100K vectors | HNSW (pgvector) | Face detection, small galleries |
| 100K - 10M | IVFFlat or HNSW | Medium galleries, AI search |
| > 10M vectors | StreamingDiskANN (pgvectorscale) | Large-scale similarity |

### Creating Indexes

```sql
-- HNSW index (default)
CREATE INDEX idx_assets_embedding
ON assets USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- StreamingDiskANN for large datasets
CREATE INDEX idx_assets_embedding_diskann
ON assets USING diskann (embedding)
WITH (max_neighbors = 64);
```

### Query Example

```sql
SELECT id, filename,
       1 - (embedding <=> $1) AS similarity
FROM assets
WHERE workspace_id = $2
ORDER BY embedding <=> $1
LIMIT 20;
```

---

## Performance Indexes

### Essential Indexes

```sql
-- Workspace isolation (on all tables)
CREATE INDEX idx_{table}_workspace ON {table}(workspace_id);

-- Common queries
CREATE INDEX idx_assets_gallery_status ON assets(gallery_id, status);
CREATE INDEX idx_galleries_workspace_status ON galleries(workspace_id, status);
CREATE INDEX idx_clients_workspace_email ON clients(workspace_id, email);

-- Full-text search
CREATE INDEX idx_assets_tags_gin ON assets USING gin (tags);
CREATE INDEX idx_assets_description_trgm ON assets
    USING gin (description gin_trgm_ops);
```

### Query Optimization

```sql
-- Check query plan
EXPLAIN ANALYZE
SELECT * FROM assets
WHERE workspace_id = 'xxx' AND status = 'published';

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Triggers

### Gallery Stats Trigger (v0.3.2)

```sql
CREATE OR REPLACE FUNCTION update_gallery_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE galleries
    SET
        photo_count = (SELECT COUNT(*) FROM assets WHERE gallery_id = NEW.gallery_id AND mime_type LIKE 'image/%'),
        video_count = (SELECT COUNT(*) FROM assets WHERE gallery_id = NEW.gallery_id AND mime_type LIKE 'video/%'),
        total_size_bytes = (SELECT COALESCE(SUM(file_size_bytes), 0) FROM assets WHERE gallery_id = NEW.gallery_id)
    WHERE id = NEW.gallery_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_gallery_stats
AFTER INSERT OR UPDATE OR DELETE ON assets
FOR EACH ROW EXECUTE FUNCTION update_gallery_stats();
```

---

## Backup & Recovery

### Automated Backups

```bash
# Daily backup to R2
pg_dump -Fc RawDrive > RawDrive_$(date +%Y%m%d).dump
rclone copy RawDrive_*.dump r2:RawDrive-backups/
```

### Point-in-Time Recovery

```bash
# Restore to specific time
pg_restore -d RawDrive RawDrive_backup.dump
```

### Backup Retention

| Type | Retention |
|------|-----------|
| Daily | 7 days |
| Weekly | 4 weeks |
| Monthly | 12 months |

---

## Related Documentation

- **Full Data Model:** `docs/project/04-DATA_MODEL.md`
- **Database Schemas:** `docs/DatabaseSchemas/`
- **Technical Specs:** `docs/TechnicalSpecs/`
