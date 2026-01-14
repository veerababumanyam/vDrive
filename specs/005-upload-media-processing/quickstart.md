# Quickstart: Storage & Media Processing

**Feature**: 005-upload-media-processing
**Services**: upload-service (port 8008), processing-service (port 8010)

---

## Prerequisites

Ensure these services are running:
```bash
cd infrastructure/docker
docker compose up -d postgres redis kafka zookeeper kafka-init
```

## 1. Start Upload Service

### Option A: Docker (Recommended)
```bash
# Build and start
docker compose up -d upload-service

# View logs
docker compose logs -f upload-service
```

### Option B: Local Development
```bash
cd services/upload-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vdrive
export REDIS_URL=redis://localhost:6379/0
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
export R2_ACCESS_KEY_ID=your_access_key
export R2_SECRET_ACCESS_KEY=your_secret_key
export R2_BUCKET_NAME=vdrive
export ENCRYPTION_MASTER_KEY=your_64_hex_char_key

# Run service
uvicorn src.app.main:app --host 0.0.0.0 --port 8008 --reload
```

## 2. Start Processing Service

```bash
# Docker
docker compose up -d processing-service

# Or local
cd services/processing-service
pip install -r requirements.txt
python -m src.app.consumers.main
```

## 3. Test Upload Flow

### Create Upload Session
```bash
# Encode metadata as base64
FILENAME=$(echo -n "test.jpg" | base64)
FILETYPE=$(echo -n "image/jpeg" | base64)
WORKSPACE=$(echo -n "550e8400-e29b-41d4-a716-446655440000" | base64)

# Create upload
curl -X POST http://localhost:8008/files \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Tus-Resumable: 1.0.0" \
  -H "Upload-Length: 1048576" \
  -H "Upload-Metadata: filename $FILENAME,filetype $FILETYPE,workspace_id $WORKSPACE" \
  -v
```

Response includes:
```
Location: http://localhost:8008/files/abc123-upload-id
Upload-Expires: 2026-01-15T10:30:00Z
```

### Upload Chunk
```bash
UPLOAD_URL="http://localhost:8008/files/abc123-upload-id"

curl -X PATCH $UPLOAD_URL \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Tus-Resumable: 1.0.0" \
  -H "Upload-Offset: 0" \
  -H "Content-Type: application/offset+octet-stream" \
  --data-binary @test.jpg \
  -v
```

### Check Status
```bash
curl http://localhost:8008/uploads/abc123-upload-id/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 4. Verify Processing

### Check Asset Processing
```bash
# After upload completes, check asset status
curl http://localhost:8008/assets/ASSET_ID/processing \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### View Kafka Events
```bash
# In Kafka UI at http://localhost:8081
# Check topics: upload.initiated, upload.completed, asset.processed
```

### View Processing Metrics
```bash
curl http://localhost:8010/metrics
```

## 5. Run Tests

```bash
cd services/upload-service

# Unit tests
pytest tests/unit -v

# Integration tests (requires Docker services)
pytest tests/integration -v

# Full test suite
pytest --cov=src tests/
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | `localhost:9092` | Kafka broker addresses |
| `R2_ENDPOINT` | Yes | - | Cloudflare R2 endpoint |
| `R2_ACCESS_KEY_ID` | Yes | - | R2 access key |
| `R2_SECRET_ACCESS_KEY` | Yes | - | R2 secret key |
| `R2_BUCKET_NAME` | Yes | `vdrive` | R2 bucket name |
| `ENCRYPTION_MASTER_KEY` | Yes | - | 64-char hex key for AES-256 |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | - | GCV API credentials path |
| `UPLOAD_MAX_SIZE` | No | `10737418240` | Max upload size (10GB) |
| `UPLOAD_CHUNK_SIZE` | No | `5242880` | Chunk size (5MB) |
| `UPLOAD_TTL_HOURS` | No | `24` | Upload URL expiration |

## Common Issues

### Upload Stuck at "uploading"
```bash
# Check Kafka connectivity
docker compose logs kafka

# Check processing service is consuming
docker compose logs processing-service
```

### Encryption Errors
```bash
# Verify master key is 64 hex characters
echo $ENCRYPTION_MASTER_KEY | wc -c  # Should be 65 (64 + newline)

# Test key derivation
python -c "from cryptography.hazmat.primitives.kdf.hkdf import HKDF; print('OK')"
```

### R2 Upload Failures
```bash
# Test R2 connectivity
aws s3 ls s3://vdrive/ \
  --endpoint-url $R2_ENDPOINT \
  --profile r2
```

## Health Checks

```bash
# Upload service health
curl http://localhost:8008/health

# Processing service metrics
curl http://localhost:8010/metrics | grep kafka_consumer_lag

# Kafka topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```
