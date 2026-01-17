# Implementation Plan: Phase 4 - AI & Gallery Services

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RawDrive Platform                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Face Service   │  │ AI Search Svc   │  │ Gallery Service │            │
│  │   (8002)        │  │   (8009)        │  │   (8004)        │            │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤            │
│  │ Face Detection  │  │ CLIP Embedding  │  │ WebSocket Mgr   │            │
│  │ DeepFace Embed  │  │ Semantic Search │  │ Preview Mode    │            │
│  │ DBSCAN Cluster  │  │ RAG Chat        │  │ Batch Ops       │            │
│  │ People Groups   │  │ Captions        │  │                 │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                      │
│           └────────────┬───────┴────────────────────┘                      │
│                        │                                                    │
│                ┌───────▼───────┐                                           │
│                │    Kafka      │                                           │
│                │ face.detected │                                           │
│                │ asset.embed.* │                                           │
│                └───────┬───────┘                                           │
│                        │                                                    │
│  ┌─────────────────────▼─────────────────────┐                            │
│  │           PostgreSQL + pgvector            │                            │
│  │  faces (512d)  │  photo_embeddings (1536d) │                            │
│  └────────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Service Directory Structures

### Face Service Structure
```
services/face-service/
├── Dockerfile
├── requirements.txt
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 001_initial_face_tables.py
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   └── v1/
│       │       ├── faces.py
│       │       ├── people.py
│       │       └── find_me.py
│       ├── consumers/
│       │   └── asset_face_processor.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── redis.py
│       │   └── circuit_breaker.py
│       ├── models/
│       │   ├── face.py
│       │   ├── face_group.py
│       │   └── face_embedding.py
│       ├── schemas/
│       │   ├── face.py
│       │   └── people.py
│       └── services/
│           ├── face_detection_service.py
│           ├── embedding_service.py
│           ├── clustering_service.py
│           └── event_service.py
└── tests/
    ├── unit/
    │   ├── test_embedding_service.py
    │   └── test_clustering_service.py
    └── integration/
        └── test_face_pipeline.py
```

### AI Search Service Structure
```
services/ai-search-service/
├── Dockerfile
├── requirements.txt
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       ├── 001_initial_embedding_tables.py
│       ├── 002_conversation_table.py
│       └── 003_caption_table.py
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   └── v1/
│       │       ├── search.py
│       │       ├── chat.py
│       │       └── captions.py
│       ├── consumers/
│       │   └── asset_embedding_processor.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   └── llm.py
│       ├── models/
│       │   ├── photo_embedding.py
│       │   ├── conversation.py
│       │   └── caption.py
│       ├── schemas/
│       │   ├── search.py
│       │   ├── chat.py
│       │   └── caption.py
│       └── services/
│           ├── embedding_service.py
│           ├── search_service.py
│           ├── rag_service.py
│           ├── caption_service.py
│           └── event_service.py
└── tests/
    ├── unit/
    │   └── test_search_service.py
    └── integration/
        └── test_search.py
```

## Dependencies

### Face Service
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
pgvector>=0.2.4
redis>=5.0.1
aiokafka>=0.10.0
google-cloud-vision>=3.5.0
deepface>=0.0.79
numpy>=1.26.0
scikit-learn>=1.4.0
Pillow>=10.2.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
structlog>=24.1.0
prometheus-client>=0.19.0
sentry-sdk[fastapi]>=1.39.0
```

### AI Search Service
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
pgvector>=0.2.4
aiokafka>=0.10.0
transformers>=4.36.0
torch>=2.1.0
sentence-transformers>=2.3.0
langchain>=0.1.0
langchain-google-genai>=0.0.6
google-generativeai>=0.3.0
numpy>=1.26.0
Pillow>=10.2.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
structlog>=24.1.0
prometheus-client>=0.19.0
sentry-sdk[fastapi]>=1.39.0
```

## Kafka Events

### Published Events
- `face.detected`: When faces are detected in an asset
- `asset.embedding.generated`: When CLIP embedding is created

### Consumed Events
- `asset.processed`: Trigger face detection and embedding generation

## Database Schema

### Face Service Tables

```sql
-- faces table
CREATE TABLE faces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    workspace_id UUID NOT NULL,
    bounding_box JSONB NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    embedding_id UUID REFERENCES face_embeddings(id),
    group_id UUID REFERENCES face_groups(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- face_embeddings table
CREATE TABLE face_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    face_id UUID NOT NULL REFERENCES faces(id),
    embedding vector(512) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX face_embeddings_ivfflat_idx ON face_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- face_groups table
CREATE TABLE face_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    name VARCHAR(255),
    representative_face_id UUID REFERENCES faces(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### AI Search Service Tables

```sql
-- photo_embeddings table
CREATE TABLE photo_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL UNIQUE,
    workspace_id UUID NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX photo_embeddings_hnsw_idx ON photo_embeddings
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    user_id UUID NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- captions table
CREATE TABLE captions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL,
    workspace_id UUID NOT NULL,
    style VARCHAR(50) NOT NULL,
    suggestions JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Docker Configuration

### Face Service (Port 8002)
```yaml
face-service:
  build:
    context: ../../services/face-service
    dockerfile: Dockerfile
  container_name: RawDrive-face-service
  ports:
    - "8002:8002"
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
    - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-vision.json
  depends_on:
    - postgres
    - redis
    - kafka
```

### AI Search Service (Port 8009)
```yaml
ai-search-service:
  build:
    context: ../../services/ai-search-service
    dockerfile: Dockerfile
  container_name: RawDrive-ai-search-service
  ports:
    - "8009:8009"
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
    - GEMINI_API_KEY=${GEMINI_API_KEY}
  depends_on:
    - postgres
    - kafka
```

## Implementation Phases

### Phase 1: Setup (T001-T009)
- Create service directories
- Setup requirements.txt
- Create Dockerfiles
- Add to docker-compose.yml
- Create Kafka topics

### Phase 2: Foundation (T010-T024)
- Core config, database, redis modules
- FastAPI main.py with lifespan
- Event service for Kafka
- Alembic migrations setup
- Gallery service WebSocket manager

### Phase 3-10: User Stories
Each user story implemented independently with:
- Models
- Services
- API endpoints
- Tests

### Phase 11: Polish
- Prometheus metrics
- Sentry integration
- Kubernetes deployments
- KEDA autoscaling
- Comprehensive testing

## Testing Strategy

- Unit tests for services (mocked dependencies)
- Integration tests for pipelines
- Contract tests for Kafka events
- E2E tests for user flows
