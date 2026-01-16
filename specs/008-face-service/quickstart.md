# Quickstart: Face Service

**Feature**: 008-face-service
**Date**: 2026-01-16

## Prerequisites

Before starting development, ensure:

1. **Docker environment** is running with all dependencies:
   ```bash
   cd infrastructure/docker
   docker compose up -d postgres redis kafka zookeeper
   ```

2. **pgvector extension** is installed in PostgreSQL:
   ```bash
   docker compose exec postgres psql -U rawdrive_user -d rawdrive_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

3. **Google Cloud Vision credentials** (optional for development):
   ```bash
   # Set in .env or export
   export GOOGLE_CLOUD_VISION_ENABLED=false  # Use mock for local dev
   export GOOGLE_CLOUD_VISION_CREDENTIALS=/path/to/credentials.json
   ```

## Running the Service

### Option 1: Docker (Recommended)

```bash
cd infrastructure/docker
docker compose up face-service
```

Service runs on: http://localhost:8002

### Option 2: Local Development

```bash
cd services/face-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start service
uvicorn src.app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Health Checks

```bash
# Liveness
curl http://localhost:8002/health

# Readiness (checks dependencies)
curl http://localhost:8002/ready

# Metrics (Prometheus format)
curl http://localhost:8002/metrics
```

## Quick API Test

### 1. List Faces in an Asset

```bash
curl -X GET "http://localhost:8002/api/v1/faces/550e8400-e29b-41d4-a716-446655440001?workspace_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 2. List People (Person Groups)

```bash
curl -X GET "http://localhost:8002/api/v1/people?workspace_id=550e8400-e29b-41d4-a716-446655440000&limit=10" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 3. Update Person Name

```bash
curl -X PATCH "http://localhost:8002/api/v1/people/770e8400-e29b-41d4-a716-446655440020?workspace_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith"}'
```

### 4. Find Me (Selfie Search)

```bash
curl -X POST "http://localhost:8002/api/v1/find-me?workspace_id=550e8400-e29b-41d4-a716-446655440000&threshold=0.6" \
  -F "selfie=@/path/to/selfie.jpg"
```

### 5. Merge Person Groups

```bash
curl -X POST "http://localhost:8002/api/v1/people/merge?workspace_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_group_ids": ["group-id-1", "group-id-2"],
    "target_group_id": "target-group-id"
  }'
```

## Triggering Face Detection

Face detection is triggered automatically when an `asset.processed` Kafka event is received.

### Manual Kafka Event (for testing)

```bash
# Using kafka-console-producer
docker compose exec kafka kafka-console-producer.sh \
  --broker-list localhost:9092 \
  --topic asset.processed

# Paste event JSON:
{"type":"asset.processed","timestamp":"2026-01-16T10:00:00Z","source":"upload-service","version":"1.0","data":{"asset_id":"550e8400-e29b-41d4-a716-446655440001","workspace_id":"550e8400-e29b-41d4-a716-446655440000","storage_path":"workspaces/ws1/assets/test.jpg","mime_type":"image/jpeg"}}
```

## Running Tests

```bash
cd services/face-service

# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test file
pytest tests/unit/test_clustering_service.py -v
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8002 | Service port |
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL connection |
| `REDIS_URL` | redis://redis:6379/0 | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | kafka:9092 | Kafka brokers |
| `GOOGLE_CLOUD_VISION_ENABLED` | false | Enable Google Vision API |
| `FACE_DETECTION_MIN_CONFIDENCE` | 0.7 | Min confidence threshold |
| `DBSCAN_EPS` | 0.5 | Clustering distance threshold |
| `DBSCAN_MIN_SAMPLES` | 2 | Min cluster size |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | 5 | Circuit breaker failures |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | 60 | Recovery wait (seconds) |

## Common Issues

### 1. pgvector Extension Not Found

```
ERROR: extension "vector" does not exist
```

**Solution**: Install pgvector in PostgreSQL container:
```bash
docker compose exec postgres psql -U rawdrive_user -d rawdrive_db -c "CREATE EXTENSION vector;"
```

### 2. Kafka Connection Timeout

```
ERROR: KafkaConnectionError: Unable to connect to any broker
```

**Solution**: Ensure Kafka is running and healthy:
```bash
docker compose up -d kafka zookeeper
docker compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### 3. Google Vision API Error

```
ERROR: google.api_core.exceptions.PermissionDenied
```

**Solution**: Check credentials and enable Vision API in GCP Console, or disable for local dev:
```bash
export GOOGLE_CLOUD_VISION_ENABLED=false
```

### 4. Redis Connection Error (Non-Critical)

```
WARNING: Redis connection failed, continuing without idempotency
```

**Note**: Service continues without Redis but may reprocess assets. For production, ensure Redis is available.

## API Documentation

Interactive API docs available when service is running:

- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc
- OpenAPI JSON: http://localhost:8002/openapi.json

## Next Steps

1. **Explore the API**: Use Swagger UI to test endpoints interactively
2. **Upload test images**: Use upload-service to trigger face detection
3. **View people**: Check the /people endpoint to see detected groups
4. **Test Find Me**: Upload a selfie to find matching photos
5. **Review clustering**: Merge/split groups to refine accuracy
