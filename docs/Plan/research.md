# Technology Research & Decisions

**Version:** 1.0.0 | **Last Updated:** January 2026

This document captures technology research findings and architectural decisions for each implementation phase of the RawDrive platform.

---

## Table of Contents

1. [Phase 2: Core Backend](#phase-2-core-backend)
2. [Phase 3: Storage & Media Processing](#phase-3-storage--media-processing)
3. [Phase 4: AI & Gallery Services](#phase-4-ai--gallery-services)
4. [Phase 5: Business Logic Services](#phase-5-business-logic-services)
5. [Phase 6: Mobile Experience](#phase-6-mobile-experience)
6. [Phase 7: Observability & Autoscaling](#phase-7-observability--autoscaling)

---

## Phase 2: Core Backend

### 2.1 FastAPI Project Structure

**Decision:** Modular layered architecture with dependency injection

**Rationale:**
- FastAPI's native dependency injection enables clean separation of concerns
- Modular structure allows microservices to share code via packages
- Async-first design aligns with high-concurrency requirements

**Project Structure:**
```
backend/
├── src/
│   └── app/
│       ├── main.py                 # FastAPI application entry
│       ├── config/
│       │   ├── settings.py         # Pydantic Settings
│       │   └── database.py         # Database connection
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py       # API router aggregation
│       │       ├── auth.py         # Authentication endpoints
│       │       ├── users.py        # User management
│       │       ├── galleries.py    # Gallery CRUD
│       │       └── ...
│       ├── models/
│       │   ├── base.py             # SQLAlchemy base model
│       │   ├── user.py             # User model
│       │   ├── gallery.py          # Gallery model
│       │   └── ...
│       ├── schemas/
│       │   ├── user.py             # Pydantic schemas
│       │   └── ...
│       ├── services/
│       │   ├── auth.py             # Authentication service
│       │   └── ...
│       ├── core/
│       │   ├── security.py         # JWT, password hashing
│       │   ├── dependencies.py     # Common dependencies
│       │   └── exceptions.py       # Custom exceptions
│       └── middleware/
│           ├── workspace.py        # Workspace extraction
│           └── logging.py          # Request logging
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
├── requirements.txt
└── Dockerfile
```

**Alternatives Considered:**
- Django REST Framework: More batteries-included but slower async support
- Starlette: Lower-level, would require more boilerplate
- Flask: Not async-native, would need ASGI adapters

---

### 2.2 JWT Authentication (EdDSA)

**Decision:** EdDSA (Ed25519) for JWT signatures

**Rationale:**
- EdDSA provides faster signature generation and verification than RSA
- 64-byte signatures (vs 256+ for RSA-2048)
- Ed25519 is recommended by NIST for new implementations
- Smaller key sizes with equivalent security (256-bit vs 2048-bit RSA)

**Implementation:**
```python
# backend/src/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class JWTService:
    def __init__(self, private_key: Ed25519PrivateKey, public_key, algorithm: str = "EdDSA"):
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: str,
        workspace_id: str,
        expires_delta: timedelta = timedelta(minutes=15)
    ) -> str:
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user_id,
            "wid": workspace_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: timedelta = timedelta(days=7)
    ) -> str:
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, self.public_key, algorithms=[self.algorithm])
```

**Token Storage:**
| Token Type | Storage | HttpOnly | Secure | SameSite |
|------------|---------|----------|--------|----------|
| Access Token | Memory/Header | N/A | N/A | N/A |
| Refresh Token | Cookie | Yes | Yes | Strict |

**Alternatives Considered:**
- RS256 (RSA): Slower, larger signatures, but widely supported
- HS256 (HMAC): Simpler but requires shared secret
- ES256 (ECDSA): Good alternative but EdDSA is newer and faster

---

### 2.3 Password Hashing (Argon2id)

**Decision:** Argon2id with tuned parameters

**Rationale:**
- Winner of the Password Hashing Competition (PHC)
- Argon2id provides resistance to both side-channel and GPU attacks
- Memory-hard function makes brute-force attacks expensive
- Recommended by OWASP for password storage

**Configuration:**
```python
# backend/src/app/core/security.py
from argon2 import PasswordHasher
from argon2.profiles import RFC_9106_LOW_MEMORY

# Production settings (adjust based on server capacity)
ph = PasswordHasher(
    time_cost=3,           # Number of iterations
    memory_cost=65536,     # 64 MB memory usage
    parallelism=4,         # Parallel threads
    hash_len=32,           # Output hash length
    salt_len=16,           # Salt length
    type=argon2.Type.ID    # Argon2id variant
)

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)

def verify_password(password: str, hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        ph.verify(hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False

def needs_rehash(hash: str) -> bool:
    """Check if hash needs to be upgraded to new parameters."""
    return ph.check_needs_rehash(hash)
```

**Parameter Tuning:**
| Environment | time_cost | memory_cost | parallelism |
|-------------|-----------|-------------|-------------|
| Development | 1 | 16384 | 1 |
| Staging | 2 | 32768 | 2 |
| Production | 3 | 65536 | 4 |

**Alternatives Considered:**
- bcrypt: Well-established but no memory-hardness
- scrypt: Memory-hard but Argon2 is newer standard
- PBKDF2: Legacy, not recommended for new applications

---

### 2.4 SQLAlchemy Async Patterns

**Decision:** SQLAlchemy 2.0 with async session management

**Rationale:**
- Native async/await support in SQLAlchemy 2.0
- Connection pooling with asyncpg for PostgreSQL
- Integrates well with FastAPI's async request handling
- Type hints and IDE support with SQLModel compatibility

**Database Configuration:**
```python
# backend/src/app/config/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DB_POOL_MIN_SIZE,
    max_overflow=settings.DB_POOL_MAX_SIZE - settings.DB_POOL_MIN_SIZE,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Dependency for database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# FastAPI dependency
async def get_db():
    async with get_db_session() as session:
        yield session
```

**Repository Pattern:**
```python
# backend/src/app/repositories/base.py
from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: str, workspace_id: str) -> Optional[ModelType]:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.workspace_id == workspace_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        workspace_id: str,
        offset: int = 0,
        limit: int = 20
    ) -> List[ModelType]:
        stmt = (
            select(self.model)
            .where(self.model.workspace_id == workspace_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

### 2.5 Multi-Tenancy via workspace_id

**Decision:** Row-Level Security (RLS) with workspace_id column

**Rationale:**
- Single database with logical tenant isolation
- Simplifies infrastructure vs separate databases per tenant
- PostgreSQL RLS provides database-level enforcement
- workspace_id in JWT enables automatic filtering

**Implementation Layers:**

**Layer 1: Database RLS Policies**
```sql
-- Enable RLS on tenant tables
ALTER TABLE galleries ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

-- Create isolation policy
CREATE POLICY workspace_isolation ON galleries
    USING (workspace_id = current_setting('app.workspace_id')::uuid);

-- Set workspace context at connection start
SET app.workspace_id = 'workspace-uuid-here';
```

**Layer 2: Application Middleware**
```python
# backend/src/app/middleware/workspace.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class WorkspaceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract workspace_id from JWT
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            try:
                payload = jwt_service.verify_token(token)
                request.state.workspace_id = payload.get("wid")
            except Exception:
                pass

        response = await call_next(request)
        return response
```

**Layer 3: Repository Enforcement**
```python
# Every query MUST include workspace_id
async def get_gallery(self, gallery_id: str, workspace_id: str) -> Gallery:
    stmt = select(Gallery).where(
        Gallery.id == gallery_id,
        Gallery.workspace_id == workspace_id  # CRITICAL: Always filter
    )
    result = await self.session.execute(stmt)
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return gallery
```

**Security Rules:**
1. Never trust client-provided workspace_id in request body
2. Always extract workspace_id from verified JWT
3. Include workspace_id in all SELECT, UPDATE, DELETE queries
4. Log cross-tenant access attempts as security incidents

---

## Phase 3: Storage & Media Processing

### 3.1 TUS Protocol for Resumable Uploads

**Decision:** TUS v1.0.0 protocol implementation

**Rationale:**
- Resumable uploads essential for large RAW files (50MB+)
- Client libraries available for all platforms
- Handles network interruptions gracefully
- Industry standard for large file uploads

**Protocol Flow:**
```
1. POST /upload/init
   → Create upload session
   → Returns Upload-Location header

2. HEAD /upload/{id}
   → Check upload status
   → Returns Upload-Offset header

3. PATCH /upload/{id}
   Content-Type: application/offset+octet-stream
   Upload-Offset: {current_offset}
   → Send file chunk
   → Server returns new offset

4. DELETE /upload/{id}
   → Cancel upload (cleanup)
```

**Implementation:**
```python
# services/upload-service/src/routes/upload.py
from fastapi import APIRouter, Request, Response, HTTPException
from typing import Optional

router = APIRouter()

@router.post("/upload/init")
async def create_upload(
    request: Request,
    upload_length: int = Header(..., alias="Upload-Length"),
    upload_metadata: Optional[str] = Header(None, alias="Upload-Metadata"),
):
    """Initialize a new upload session."""
    workspace_id = request.state.workspace_id

    # Parse metadata (base64 encoded key-value pairs)
    metadata = parse_tus_metadata(upload_metadata)

    # Create upload session in Redis
    upload_id = str(uuid.uuid4())
    session = UploadSession(
        id=upload_id,
        workspace_id=workspace_id,
        file_name=metadata.get("filename"),
        file_type=metadata.get("filetype"),
        total_size=upload_length,
        uploaded_size=0,
        status="uploading",
        created_at=datetime.utcnow(),
    )
    await redis.set(f"upload:{upload_id}", session.json(), ex=86400)  # 24h TTL

    return Response(
        status_code=201,
        headers={
            "Location": f"/upload/{upload_id}",
            "Tus-Resumable": "1.0.0",
        }
    )

@router.patch("/upload/{upload_id}")
async def upload_chunk(
    upload_id: str,
    request: Request,
    upload_offset: int = Header(..., alias="Upload-Offset"),
):
    """Receive a file chunk."""
    # Get session
    session = await get_upload_session(upload_id)

    # Verify offset matches
    if session.uploaded_size != upload_offset:
        raise HTTPException(status_code=409, detail="Offset mismatch")

    # Read chunk
    chunk = await request.body()
    chunk_size = len(chunk)

    # Write to temporary storage
    await write_chunk(upload_id, upload_offset, chunk)

    # Update session
    session.uploaded_size += chunk_size
    await redis.set(f"upload:{upload_id}", session.json(), ex=86400)

    # Check if complete
    if session.uploaded_size >= session.total_size:
        # Publish completion event to Kafka
        await kafka_producer.send("upload.completed", {
            "upload_id": upload_id,
            "workspace_id": session.workspace_id,
            "file_name": session.file_name,
        })

    return Response(
        status_code=204,
        headers={
            "Upload-Offset": str(session.uploaded_size),
            "Tus-Resumable": "1.0.0",
        }
    )
```

**Chunk Size Configuration:**
| Network Type | Chunk Size |
|--------------|------------|
| High-bandwidth | 10 MB |
| Standard | 5 MB |
| Mobile/Low | 1 MB |

---

### 3.2 AES-256-GCM Encryption

**Decision:** AES-256-GCM for at-rest encryption

**Rationale:**
- AEAD (Authenticated Encryption with Associated Data)
- Provides both confidentiality and integrity
- NIST-approved, widely supported
- GCM mode enables parallel encryption

**Key Management:**
```python
# services/upload-service/src/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64

class EncryptionService:
    def __init__(self, master_key: bytes):
        # Master key from environment/KMS
        self.master_key = master_key

    def generate_data_key(self) -> tuple[bytes, bytes]:
        """Generate a unique data key for each file."""
        # Generate random 256-bit key
        data_key = os.urandom(32)

        # Encrypt data key with master key
        aesgcm = AESGCM(self.master_key)
        nonce = os.urandom(12)
        encrypted_key = aesgcm.encrypt(nonce, data_key, None)

        # Return encrypted key (to store) and plaintext key (to use)
        return nonce + encrypted_key, data_key

    def decrypt_data_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt a data key using master key."""
        nonce = encrypted_key[:12]
        ciphertext = encrypted_key[12:]
        aesgcm = AESGCM(self.master_key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_file(self, data: bytes, data_key: bytes) -> bytes:
        """Encrypt file data with data key."""
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    def decrypt_file(self, encrypted_data: bytes, data_key: bytes) -> bytes:
        """Decrypt file data with data key."""
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(data_key)
        return aesgcm.decrypt(nonce, ciphertext, None)
```

**Storage Strategy:**
| Component | Storage Location | Encrypted |
|-----------|------------------|-----------|
| Original File | R2 Bucket | Yes (AES-256-GCM) |
| Encrypted Data Key | PostgreSQL (assets.encrypted_key) | Yes (Master Key) |
| Master Key | Environment Variable / KMS | N/A |

---

### 3.3 Celery Task Patterns

**Decision:** Celery with Redis broker and PostgreSQL result backend

**Rationale:**
- Proven distributed task queue
- Redis broker provides fast message delivery
- Supports task priorities and routing
- Native retry mechanisms with exponential backoff

**Worker Configuration:**
```python
# backend/src/app/celery/config.py
from celery import Celery

celery_app = Celery(
    "RawDrive",
    broker=settings.REDIS_URL,
    backend=f"db+{settings.DATABASE_URL}",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 min soft limit
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routing
celery_app.conf.task_routes = {
    "tasks.ai.*": {"queue": "ai"},
    "tasks.email.*": {"queue": "email"},
    "tasks.thumbnail.*": {"queue": "media"},
}
```

**Task Patterns:**
```python
# backend/src/app/celery/tasks/media.py
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def generate_thumbnails(self, asset_id: str, workspace_id: str):
    """Generate thumbnails for uploaded asset."""
    try:
        # Download original from R2
        original = download_from_r2(asset_id)

        # Generate thumbnails at different sizes
        sizes = [(150, 150), (300, 300), (800, 800), (1600, 1600)]
        for width, height in sizes:
            thumbnail = resize_image(original, width, height)
            upload_to_r2(f"{asset_id}/thumb_{width}x{height}", thumbnail)

        # Update asset status
        update_asset_status(asset_id, "ready")

        # Publish completion event
        kafka_producer.send("asset.processed", {
            "asset_id": asset_id,
            "workspace_id": workspace_id,
        })

    except Exception as exc:
        # Log and re-raise for retry
        logger.error(f"Thumbnail generation failed: {exc}")
        raise self.retry(exc=exc)
```

**Worker Types:**
| Worker | Queue | Tasks | Concurrency |
|--------|-------|-------|-------------|
| General | celery | Thumbnails, cleanup | 8 |
| AI | ai | Face detection, embedding | 4 |
| Email | email | Notifications, invites | 2 |

---

### 3.4 Thumbnail Generation

**Decision:** Pillow with ImageMagick fallback for RAW formats

**Rationale:**
- Pillow handles common formats (JPEG, PNG, WebP)
- ImageMagick/rawpy for RAW formats (CR2, NEF, ARW)
- Thumbnail sizes optimized for different viewports
- LQIP (Low-Quality Image Placeholder) for progressive loading

**Implementation:**
```python
# backend/src/app/services/thumbnail.py
from PIL import Image
import rawpy
from io import BytesIO

class ThumbnailService:
    SIZES = {
        "xs": (150, 150),    # Gallery grid
        "sm": (300, 300),    # Preview
        "md": (800, 800),    # Detail view
        "lg": (1600, 1600),  # Lightbox
        "lqip": (20, 20),    # Placeholder
    }

    def generate_thumbnails(self, file_data: bytes, mime_type: str) -> dict[str, bytes]:
        """Generate all thumbnail sizes for an image."""
        # Load image based on type
        if mime_type in ["image/x-canon-cr2", "image/x-nikon-nef", "image/x-sony-arw"]:
            image = self._load_raw(file_data)
        else:
            image = Image.open(BytesIO(file_data))

        # Convert to RGB if necessary
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        thumbnails = {}
        for name, (width, height) in self.SIZES.items():
            thumb = self._resize(image, width, height)
            thumbnails[name] = self._encode(thumb, name)

        return thumbnails

    def _load_raw(self, data: bytes) -> Image:
        """Load RAW file using rawpy."""
        with rawpy.imread(BytesIO(data)) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,
                half_size=False,
                no_auto_bright=False,
            )
            return Image.fromarray(rgb)

    def _resize(self, image: Image, width: int, height: int) -> Image:
        """Resize image maintaining aspect ratio."""
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        return image

    def _encode(self, image: Image, size_name: str) -> bytes:
        """Encode thumbnail to bytes."""
        buffer = BytesIO()
        quality = 10 if size_name == "lqip" else 85
        format = "WEBP" if size_name != "lqip" else "JPEG"
        image.save(buffer, format=format, quality=quality, optimize=True)
        return buffer.getvalue()
```

**EXIF Extraction:**
```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def extract_exif(image: Image) -> dict:
    """Extract EXIF metadata from image."""
    exif_data = {}

    if hasattr(image, "_getexif") and image._getexif():
        raw_exif = image._getexif()
        for tag_id, value in raw_exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ["Make", "Model", "DateTime", "ExposureTime",
                       "FNumber", "ISOSpeedRatings", "FocalLength"]:
                exif_data[tag] = str(value)

    return exif_data
```

---

## Phase 4: AI & Gallery Services

### 4.1 Google Cloud Vision API

**Decision:** Google Cloud Vision for face detection

**Rationale:**
- High accuracy face detection with bounding boxes
- Handles multiple faces per image
- Returns facial landmarks for alignment
- Pay-per-use pricing scales with usage

**Implementation:**
```python
# services/face-service/src/vision.py
from google.cloud import vision
from google.oauth2 import service_account

class VisionService:
    def __init__(self, credentials_path: str):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        self.client = vision.ImageAnnotatorClient(credentials=credentials)

    async def detect_faces(self, image_data: bytes) -> list[dict]:
        """Detect faces in an image."""
        image = vision.Image(content=image_data)

        response = self.client.face_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        faces = []
        for face in response.face_annotations:
            # Get bounding box
            vertices = face.bounding_poly.vertices
            bbox = {
                "x": vertices[0].x,
                "y": vertices[0].y,
                "width": vertices[2].x - vertices[0].x,
                "height": vertices[2].y - vertices[0].y,
            }

            # Get facial landmarks for alignment
            landmarks = {}
            for landmark in face.landmarks:
                landmarks[landmark.type_.name] = {
                    "x": landmark.position.x,
                    "y": landmark.position.y,
                    "z": landmark.position.z,
                }

            faces.append({
                "bounding_box": bbox,
                "landmarks": landmarks,
                "detection_confidence": face.detection_confidence,
                "joy_likelihood": face.joy_likelihood.name,
                "roll_angle": face.roll_angle,
                "pan_angle": face.pan_angle,
                "tilt_angle": face.tilt_angle,
            })

        return faces
```

**Rate Limiting & Costs:**
| Feature | Free Tier | Price (after) |
|---------|-----------|---------------|
| Face Detection | 1,000/month | $1.50/1000 |
| Label Detection | 1,000/month | $1.50/1000 |

---

### 4.2 ArcFace Embeddings (512-dim)

**Decision:** ArcFace model for face recognition embeddings

**Rationale:**
- State-of-the-art face recognition accuracy
- 512-dimensional embeddings balance accuracy and storage
- Open-source model available (InsightFace)
- Supports pgvector for similarity search

**Implementation:**
```python
# services/face-service/src/arcface.py
import numpy as np
from insightface.app import FaceAnalysis

class ArcFaceService:
    def __init__(self):
        self.app = FaceAnalysis(
            name="buffalo_l",  # Model name
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def get_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """Generate 512-dim embedding for aligned face image."""
        faces = self.app.get(face_image)
        if not faces:
            return None

        # Return normalized 512-dim embedding
        embedding = faces[0].embedding
        return embedding / np.linalg.norm(embedding)

    def compare_faces(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2))

    def find_matches(
        self,
        query_embedding: np.ndarray,
        embeddings: list[np.ndarray],
        threshold: float = 0.5
    ) -> list[tuple[int, float]]:
        """Find matching faces above similarity threshold."""
        matches = []
        for idx, emb in enumerate(embeddings):
            similarity = self.compare_faces(query_embedding, emb)
            if similarity >= threshold:
                matches.append((idx, similarity))
        return sorted(matches, key=lambda x: x[1], reverse=True)
```

**Similarity Thresholds:**
| Threshold | Use Case | False Positive Rate |
|-----------|----------|---------------------|
| 0.7+ | Same person (high confidence) | <0.1% |
| 0.5-0.7 | Likely same person | ~1% |
| 0.3-0.5 | Possible match (needs review) | ~5% |

---

### 4.3 pgvector IVFFlat Indexes

**Decision:** pgvector with IVFFlat index for vector similarity search

**Rationale:**
- Native PostgreSQL extension (no separate service)
- IVFFlat provides good balance of speed and accuracy
- Supports cosine, euclidean, and inner product distances
- Integrates with existing SQLAlchemy models

**Setup:**
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create face embeddings table
CREATE TABLE face_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    person_id UUID REFERENCES people(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    embedding vector(512) NOT NULL,
    confidence FLOAT NOT NULL,
    bounding_box JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create IVFFlat index for cosine similarity
CREATE INDEX ON face_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on data size

-- Index for filtering by workspace
CREATE INDEX idx_face_embeddings_workspace
ON face_embeddings(workspace_id);
```

**Querying:**
```python
# services/face-service/src/repository.py
from pgvector.sqlalchemy import Vector
from sqlalchemy import select, func

class FaceRepository:
    async def find_similar_faces(
        self,
        embedding: list[float],
        workspace_id: str,
        limit: int = 10,
        threshold: float = 0.5
    ) -> list[FaceEmbedding]:
        """Find similar faces using cosine similarity."""
        # Convert to pgvector format
        query_vector = embedding

        stmt = (
            select(FaceEmbedding)
            .where(FaceEmbedding.workspace_id == workspace_id)
            .order_by(FaceEmbedding.embedding.cosine_distance(query_vector))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        faces = result.scalars().all()

        # Filter by threshold (1 - cosine_distance = similarity)
        return [f for f in faces if (1 - f.cosine_distance) >= threshold]
```

**Index Tuning:**
| Data Size | lists Parameter | Probes at Query |
|-----------|-----------------|-----------------|
| <10K vectors | 50 | 10 |
| 10K-100K | 100 | 20 |
| 100K-1M | 500 | 50 |
| >1M | 1000+ | 100 |

---

### 4.4 WebSocket Scaling

**Decision:** WebSocket with Redis Pub/Sub for horizontal scaling

**Rationale:**
- Real-time gallery updates without polling
- Redis Pub/Sub enables multi-instance communication
- Traefik handles WebSocket upgrades
- Connection limits per user prevent abuse

**Implementation:**
```python
# services/gallery-service/src/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import redis.asyncio as redis

class ConnectionManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, gallery_id: str, user_id: str):
        """Accept WebSocket connection and subscribe to gallery channel."""
        await websocket.accept()

        if gallery_id not in self.active_connections:
            self.active_connections[gallery_id] = set()
        self.active_connections[gallery_id].add(websocket)

        # Subscribe to Redis channel for this gallery
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"gallery:{gallery_id}")

        # Listen for messages in background
        asyncio.create_task(self._listen(pubsub, websocket))

    async def disconnect(self, websocket: WebSocket, gallery_id: str):
        """Remove WebSocket from active connections."""
        if gallery_id in self.active_connections:
            self.active_connections[gallery_id].discard(websocket)

    async def broadcast(self, gallery_id: str, message: dict):
        """Broadcast message to all instances via Redis."""
        await self.redis.publish(
            f"gallery:{gallery_id}",
            json.dumps(message)
        )

    async def _listen(self, pubsub, websocket: WebSocket):
        """Listen for Redis messages and forward to WebSocket."""
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))

# FastAPI endpoint
@router.websocket("/ws/galleries/{gallery_id}")
async def gallery_websocket(
    websocket: WebSocket,
    gallery_id: str,
    token: str = Query(...),
):
    # Verify token
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001)
        return

    manager = ConnectionManager(settings.REDIS_URL)
    await manager.connect(websocket, gallery_id, user.id)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_json()
            # Process client message if needed
    except WebSocketDisconnect:
        await manager.disconnect(websocket, gallery_id)
```

**Connection Limits:**
| Tier | Max Connections | Message Rate |
|------|-----------------|--------------|
| Free | 5 | 10/sec |
| Starter | 20 | 50/sec |
| Professional | 100 | 200/sec |
| Business | 500 | 1000/sec |

---

### 4.5 Magic Link Security

**Decision:** HMAC-signed magic links with time-bound tokens

**Rationale:**
- Secure gallery sharing without account creation
- Links expire after configurable duration
- Optional password protection
- Access tracking for analytics

**Implementation:**
```python
# services/gallery-service/src/magic_link.py
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode

class MagicLinkService:
    def __init__(self, secret: str):
        self.secret = secret.encode()

    def generate(
        self,
        gallery_id: str,
        access_level: str = "view",  # view, select, download
        expires_hours: int = 168,  # 7 days default
        password: str = None,
    ) -> dict:
        """Generate a magic link for gallery access."""
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        # Create token payload
        payload = {
            "gid": gallery_id,
            "lvl": access_level,
            "exp": int(expires_at.timestamp()),
        }

        # Generate signature
        message = f"{gallery_id}:{access_level}:{payload['exp']}"
        signature = hmac.new(
            self.secret,
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]  # Shortened for URL friendliness

        # Build magic link
        token = base64.urlsafe_b64encode(
            f"{payload['gid']}:{payload['lvl']}:{payload['exp']}:{signature}".encode()
        ).decode().rstrip("=")

        return {
            "token": token,
            "url": f"https://app.RawDrive.io/g/{token}",
            "expires_at": expires_at.isoformat(),
            "password_protected": password is not None,
        }

    def verify(self, token: str) -> dict:
        """Verify and decode a magic link token."""
        try:
            # Decode token
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode()
            parts = decoded.split(":")

            if len(parts) != 4:
                raise ValueError("Invalid token format")

            gallery_id, access_level, exp_timestamp, signature = parts

            # Verify signature
            message = f"{gallery_id}:{access_level}:{exp_timestamp}"
            expected_sig = hmac.new(
                self.secret,
                message.encode(),
                hashlib.sha256
            ).hexdigest()[:16]

            if not hmac.compare_digest(signature, expected_sig):
                raise ValueError("Invalid signature")

            # Check expiration
            if int(exp_timestamp) < datetime.utcnow().timestamp():
                raise ValueError("Token expired")

            return {
                "gallery_id": gallery_id,
                "access_level": access_level,
                "expires_at": datetime.fromtimestamp(int(exp_timestamp)),
            }

        except Exception as e:
            raise ValueError(f"Invalid magic link: {str(e)}")
```

**Access Levels:**
| Level | Permissions |
|-------|-------------|
| `view` | Browse gallery, view photos |
| `select` | View + mark favorites |
| `download` | View + select + download |

---

## Phase 5: Business Logic Services

### 5.1 Stripe Webhook Handling

**Decision:** Stripe webhooks with signature verification and idempotency

**Rationale:**
- Stripe's official recommendation for payment events
- Signature verification prevents replay attacks
- Idempotency keys prevent duplicate processing
- Supports all subscription lifecycle events

**Implementation:**
```python
# services/billing-service/src/webhooks/stripe.py
import stripe
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Idempotency check
    event_id = event["id"]
    if await is_event_processed(event_id):
        return {"status": "already_processed"}

    # Process event by type
    event_type = event["type"]
    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_payment_failed,
        "customer.created": handle_customer_created,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            await handler(event["data"]["object"])
            await mark_event_processed(event_id)
        except Exception as e:
            logger.error(f"Webhook handler failed: {e}")
            raise HTTPException(status_code=500)

    return {"status": "processed"}

async def handle_subscription_created(subscription: dict):
    """Handle new subscription creation."""
    customer_id = subscription["customer"]
    workspace = await get_workspace_by_stripe_customer(customer_id)

    await update_workspace_subscription(
        workspace_id=workspace.id,
        tier=map_price_to_tier(subscription["items"]["data"][0]["price"]["id"]),
        status="active",
        stripe_subscription_id=subscription["id"],
        current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
    )

    # Publish event for other services
    await kafka_producer.send("user.subscription.changed", {
        "workspace_id": workspace.id,
        "old_tier": workspace.subscription_tier,
        "new_tier": map_price_to_tier(subscription["items"]["data"][0]["price"]["id"]),
    })
```

**Event Types to Handle:**
| Event | Action |
|-------|--------|
| `customer.subscription.created` | Activate subscription |
| `customer.subscription.updated` | Update tier/status |
| `customer.subscription.deleted` | Cancel subscription |
| `invoice.paid` | Record payment |
| `invoice.payment_failed` | Send retry notification |

---

### 5.2 Razorpay Integration

**Decision:** Razorpay for Indian market with webhook support

**Rationale:**
- Required for INR transactions in India
- Similar webhook pattern to Stripe
- Supports subscription plans
- UPI and local payment methods

**Implementation:**
```python
# services/billing-service/src/payment/razorpay.py
import razorpay
import hmac
import hashlib

class RazorpayService:
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.key_secret = key_secret

    async def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        total_count: int = 12,  # Billing cycles
    ) -> dict:
        """Create a new subscription."""
        subscription = self.client.subscription.create({
            "plan_id": plan_id,
            "customer_id": customer_id,
            "total_count": total_count,
            "customer_notify": 1,
        })
        return subscription

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Razorpay webhook signature."""
        expected = hmac.new(
            self.key_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, event: dict):
        """Process Razorpay webhook event."""
        event_type = event["event"]

        handlers = {
            "subscription.activated": self._handle_subscription_activated,
            "subscription.charged": self._handle_subscription_charged,
            "subscription.cancelled": self._handle_subscription_cancelled,
            "payment.failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(event["payload"])
```

**Payment Methods:**
| Method | Support | Processing Time |
|--------|---------|-----------------|
| Credit/Debit Card | Yes | Instant |
| UPI | Yes | Instant |
| Net Banking | Yes | Instant |
| Wallets | Yes | Instant |
| EMI | Yes | Instant |

---

### 5.3 Exponential Backoff Retry Pattern

**Decision:** Exponential backoff with jitter for webhook delivery

**Rationale:**
- Prevents thundering herd on service recovery
- Jitter prevents synchronized retries
- Configurable max retries and backoff limits
- Dead letter queue for permanent failures

**Implementation:**
```python
# services/webhooks-service/src/delivery.py
import random
from datetime import datetime, timedelta
from typing import Optional

class WebhookDelivery:
    MAX_RETRIES = 5
    BASE_DELAY_SECONDS = 1
    MAX_DELAY_SECONDS = 3600  # 1 hour max

    def calculate_next_retry(
        self,
        attempt: int,
        last_attempt: datetime
    ) -> Optional[datetime]:
        """Calculate next retry time with exponential backoff + jitter."""
        if attempt >= self.MAX_RETRIES:
            return None  # Send to DLQ

        # Exponential backoff: 2^attempt * base_delay
        delay = min(
            (2 ** attempt) * self.BASE_DELAY_SECONDS,
            self.MAX_DELAY_SECONDS
        )

        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay_with_jitter = delay + jitter

        return last_attempt + timedelta(seconds=delay_with_jitter)

    async def deliver(
        self,
        webhook_id: str,
        payload: dict,
        target_url: str,
    ) -> bool:
        """Attempt webhook delivery with retries."""
        attempt = 0

        while attempt < self.MAX_RETRIES:
            try:
                response = await httpx.post(
                    target_url,
                    json=payload,
                    headers=self._sign_payload(payload),
                    timeout=30.0,
                )

                if response.status_code < 400:
                    await self._log_success(webhook_id, attempt, response)
                    return True

                # 4xx errors (except 429) are permanent failures
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    await self._send_to_dlq(webhook_id, payload, "client_error")
                    return False

            except Exception as e:
                logger.warning(f"Webhook delivery attempt {attempt} failed: {e}")

            attempt += 1
            if attempt < self.MAX_RETRIES:
                next_retry = self.calculate_next_retry(attempt, datetime.utcnow())
                await asyncio.sleep((next_retry - datetime.utcnow()).total_seconds())

        # Max retries exceeded
        await self._send_to_dlq(webhook_id, payload, "max_retries_exceeded")
        return False
```

**Retry Schedule:**
| Attempt | Delay (base) | With Jitter |
|---------|--------------|-------------|
| 1 | 2s | 1.5-2.5s |
| 2 | 4s | 3-5s |
| 3 | 8s | 6-10s |
| 4 | 16s | 12-20s |
| 5 | 32s | 24-40s |

---

### 5.4 Dead Letter Queue (DLQ) Pattern

**Decision:** Kafka DLQ for failed webhook deliveries

**Rationale:**
- Preserves failed messages for analysis
- Enables manual retry after issue resolution
- Separates failure handling from main processing
- 30-day retention for debugging

**Implementation:**
```python
# services/webhooks-service/src/dlq.py
from aiokafka import AIOKafkaProducer

class DeadLetterQueue:
    def __init__(self, producer: AIOKafkaProducer):
        self.producer = producer
        self.topic = "webhook.dlq"

    async def send(
        self,
        original_message: dict,
        error_reason: str,
        attempts: int,
        last_error: str,
    ):
        """Send failed message to DLQ."""
        dlq_message = {
            "original": original_message,
            "metadata": {
                "failed_at": datetime.utcnow().isoformat(),
                "error_reason": error_reason,
                "total_attempts": attempts,
                "last_error": last_error,
            }
        }

        await self.producer.send_and_wait(
            self.topic,
            key=original_message["id"].encode(),
            value=json.dumps(dlq_message).encode(),
        )

        # Also log to database for easy querying
        await self._log_to_database(dlq_message)

    async def reprocess(self, message_id: str):
        """Manually retry a DLQ message."""
        message = await self._get_from_database(message_id)

        if not message:
            raise ValueError(f"Message {message_id} not found in DLQ")

        # Republish to original topic
        await self.producer.send_and_wait(
            "webhook.pending",
            key=message_id.encode(),
            value=json.dumps(message["original"]).encode(),
        )

        # Mark as reprocessed
        await self._mark_reprocessed(message_id)
```

**DLQ Management:**
| Action | Endpoint | Description |
|--------|----------|-------------|
| List | `GET /admin/dlq` | View failed messages |
| Inspect | `GET /admin/dlq/{id}` | View message details |
| Retry | `POST /admin/dlq/{id}/retry` | Reprocess message |
| Purge | `DELETE /admin/dlq/{id}` | Remove message |

---

### 5.5 SendGrid Email Templates

**Decision:** SendGrid with dynamic templates

**Rationale:**
- Reliable email delivery with analytics
- Dynamic templates for personalization
- Supports attachments for invoices
- Webhook for delivery status

**Template Setup:**
```python
# services/notifications-service/src/email.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment

class EmailService:
    TEMPLATES = {
        "welcome": "d-xxxx1111",
        "gallery_invite": "d-xxxx2222",
        "selection_complete": "d-xxxx3333",
        "invoice": "d-xxxx4444",
        "password_reset": "d-xxxx5555",
    }

    def __init__(self, api_key: str):
        self.client = SendGridAPIClient(api_key)

    async def send_templated_email(
        self,
        to_email: str,
        template_name: str,
        dynamic_data: dict,
        attachments: list[Attachment] = None,
    ):
        """Send email using dynamic template."""
        template_id = self.TEMPLATES.get(template_name)
        if not template_id:
            raise ValueError(f"Unknown template: {template_name}")

        message = Mail(
            from_email=("no-reply@RawDrive.io", "RawDrive"),
            to_emails=to_email,
        )
        message.template_id = template_id
        message.dynamic_template_data = dynamic_data

        if attachments:
            for attachment in attachments:
                message.add_attachment(attachment)

        response = self.client.send(message)

        return {
            "status_code": response.status_code,
            "message_id": response.headers.get("X-Message-Id"),
        }

    async def send_gallery_invite(
        self,
        to_email: str,
        gallery_name: str,
        photographer_name: str,
        magic_link: str,
        thumbnail_url: str,
    ):
        """Send gallery invitation email."""
        return await self.send_templated_email(
            to_email=to_email,
            template_name="gallery_invite",
            dynamic_data={
                "gallery_name": gallery_name,
                "photographer_name": photographer_name,
                "magic_link": magic_link,
                "thumbnail_url": thumbnail_url,
                "current_year": datetime.now().year,
            }
        )
```

**Template Variables:**
| Template | Required Variables |
|----------|-------------------|
| `welcome` | `user_name`, `login_url` |
| `gallery_invite` | `gallery_name`, `photographer_name`, `magic_link`, `thumbnail_url` |
| `selection_complete` | `client_name`, `gallery_name`, `selected_count`, `dashboard_url` |
| `invoice` | `invoice_number`, `amount`, `currency`, `due_date`, `payment_url` |
| `password_reset` | `user_name`, `reset_url`, `expires_at` |

---

## Phase 6: Mobile Experience

### 6.1 React Native Shared Logic

**Decision:** React Native with shared business logic

**Rationale:**
- Code sharing between iOS and Android
- Reuse React web components where possible
- Shared TypeScript types with web frontend
- Native performance for camera and gallery access

**Architecture:**
```
mobile/
├── packages/
│   └── shared/               # Shared with web
│       ├── api/              # API client
│       ├── hooks/            # Business logic hooks
│       ├── types/            # TypeScript types
│       └── utils/            # Utilities
├── apps/
│   ├── mobile/               # React Native app
│   │   ├── src/
│   │   │   ├── screens/      # Screen components
│   │   │   ├── navigation/   # React Navigation
│   │   │   ├── components/   # Native components
│   │   │   └── native/       # Platform-specific
│   │   ├── ios/
│   │   └── android/
│   └── web/                  # Web app (reuses shared)
```

**Shared Hook Example:**
```typescript
// packages/shared/hooks/useGallery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import type { Gallery, GalleryCreate } from '../types';

export function useGallery(galleryId: string) {
  return useQuery({
    queryKey: ['gallery', galleryId],
    queryFn: () => api.galleries.get(galleryId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useGalleries(options?: { limit?: number }) {
  return useQuery({
    queryKey: ['galleries', options],
    queryFn: () => api.galleries.list(options),
  });
}

export function useCreateGallery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GalleryCreate) => api.galleries.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['galleries'] });
    },
  });
}
```

---

### 6.2 WatermelonDB Offline-First

**Decision:** WatermelonDB for offline data sync

**Rationale:**
- SQLite-based for large datasets
- Lazy loading for performance
- Sync engine for conflict resolution
- Works with React Native and web

**Schema Definition:**
```typescript
// mobile/apps/mobile/src/database/schema.ts
import { appSchema, tableSchema } from '@nozbe/watermelondb';

export const schema = appSchema({
  version: 1,
  tables: [
    tableSchema({
      name: 'galleries',
      columns: [
        { name: 'server_id', type: 'string', isIndexed: true },
        { name: 'name', type: 'string' },
        { name: 'slug', type: 'string' },
        { name: 'thumbnail_url', type: 'string', isOptional: true },
        { name: 'asset_count', type: 'number' },
        { name: 'is_synced', type: 'boolean' },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number' },
      ],
    }),
    tableSchema({
      name: 'assets',
      columns: [
        { name: 'server_id', type: 'string', isIndexed: true },
        { name: 'gallery_id', type: 'string', isIndexed: true },
        { name: 'local_uri', type: 'string', isOptional: true },
        { name: 'remote_url', type: 'string', isOptional: true },
        { name: 'thumbnail_url', type: 'string', isOptional: true },
        { name: 'status', type: 'string' }, // pending, uploading, synced
        { name: 'file_size', type: 'number' },
        { name: 'is_synced', type: 'boolean' },
        { name: 'created_at', type: 'number' },
      ],
    }),
  ],
});
```

**Sync Implementation:**
```typescript
// mobile/apps/mobile/src/database/sync.ts
import { synchronize } from '@nozbe/watermelondb/sync';

export async function syncDatabase(database: Database) {
  await synchronize({
    database,
    pullChanges: async ({ lastPulledAt }) => {
      const response = await api.sync.pull({
        lastPulledAt,
        schemaVersion: schema.version,
      });

      return {
        changes: response.changes,
        timestamp: response.timestamp,
      };
    },
    pushChanges: async ({ changes }) => {
      await api.sync.push({ changes });
    },
    migrationsEnabledAtVersion: 1,
  });
}
```

---

### 6.3 Biometric Authentication

**Decision:** expo-local-authentication for biometric auth

**Rationale:**
- Cross-platform biometric support (Face ID, Touch ID, fingerprint)
- Secure keychain storage for credentials
- Graceful fallback to PIN/password
- Privacy-respecting (no biometric data leaves device)

**Implementation:**
```typescript
// mobile/apps/mobile/src/auth/biometric.ts
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

export class BiometricService {
  async isAvailable(): Promise<boolean> {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  }

  async getSupportedTypes(): Promise<string[]> {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    return types.map(type => {
      switch (type) {
        case LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION:
          return 'Face ID';
        case LocalAuthentication.AuthenticationType.FINGERPRINT:
          return 'Fingerprint';
        case LocalAuthentication.AuthenticationType.IRIS:
          return 'Iris';
        default:
          return 'Unknown';
      }
    });
  }

  async authenticate(reason: string): Promise<boolean> {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      cancelLabel: 'Cancel',
      fallbackLabel: 'Use Passcode',
      disableDeviceFallback: false,
    });

    return result.success;
  }

  async storeCredentials(key: string, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }

  async getCredentials(key: string): Promise<string | null> {
    return await SecureStore.getItemAsync(key);
  }

  async authenticateAndGetToken(): Promise<string | null> {
    const authenticated = await this.authenticate('Unlock RawDrive');
    if (!authenticated) return null;

    return await this.getCredentials('refresh_token');
  }
}
```

---

## Phase 7: Observability & Autoscaling

### 7.1 KEDA Threshold Tuning

**Decision:** Multi-metric scaling with conservative scale-down

**Rationale:**
- HTTP RPS for request-driven services
- Kafka lag for event-driven services
- Conservative cooldown prevents thrashing
- Prometheus metrics for custom triggers

**ScaledObject Configuration:**
```yaml
# infrastructure/kubernetes/base/keda/backend-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: backend-scaledobject
  namespace: RawDrive
spec:
  scaleTargetRef:
    name: backend
    apiVersion: apps/v1
    kind: Deployment
  pollingInterval: 15
  cooldownPeriod: 60
  minReplicaCount: 2
  maxReplicaCount: 100
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
          policies:
            - type: Percent
              value: 10
              periodSeconds: 60
        scaleUp:
          stabilizationWindowSeconds: 0
          policies:
            - type: Percent
              value: 100
              periodSeconds: 15
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: http_requests_per_second
        threshold: "100"
        query: |
          sum(rate(traefik_service_requests_total{service="backend@docker"}[1m]))
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: http_p95_latency
        threshold: "500"  # 500ms
        query: |
          histogram_quantile(0.95,
            sum(rate(traefik_service_request_duration_seconds_bucket{service="backend@docker"}[5m]))
            by (le)
          ) * 1000
```

**Service-Specific Tuning:**
| Service | Primary Trigger | Threshold | Cooldown |
|---------|-----------------|-----------|----------|
| Backend | HTTP RPS | 100/replica | 60s |
| Gallery | HTTP RPS + WebSocket | 100 RPS, 500 conn | 60s |
| Upload | Kafka lag | 100 messages | 60s |
| Face | Kafka lag | 50 messages | 120s |
| Celery | Redis queue | 100 tasks | 60s |

---

### 7.2 Alert Rule Optimization

**Decision:** Tiered alerting with actionable thresholds

**Rationale:**
- Critical alerts for immediate action (pager)
- Warning alerts for investigation (Slack)
- Info alerts for dashboards only
- Alert fatigue prevention via proper thresholds

**Alert Rules:**
```yaml
# infrastructure/prometheus/alert-rules.yaml
groups:
  - name: RawDrive-critical
    rules:
      - alert: ServiceDown
        expr: up{job=~"backend|gallery|billing"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          runbook: "https://wiki.RawDrive.io/runbooks/service-down"

      - alert: HighErrorRate
        expr: |
          sum(rate(traefik_service_requests_total{code=~"5.."}[5m])) by (service)
          / sum(rate(traefik_service_requests_total[5m])) by (service)
          > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate ({{ $value | humanizePercentage }}) for {{ $labels.service }}"

      - alert: DatabaseConnectionExhausted
        expr: |
          pg_stat_activity_count{datname="RawDrive"}
          / pg_settings_max_connections
          > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL connections at {{ $value | humanizePercentage }}"

  - name: RawDrive-warning
    rules:
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(traefik_service_request_duration_seconds_bucket[5m]))
            by (le, service)
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 500ms for {{ $labels.service }}"

      - alert: KafkaConsumerLag
        expr: kafka_consumergroup_lag > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Kafka consumer lag high for {{ $labels.consumergroup }}"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"}
          / node_filesystem_size_bytes{mountpoint="/"})
          < 0.15
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 15% on {{ $labels.instance }}"
```

**Notification Routing:**
| Severity | Channel | Response Time |
|----------|---------|---------------|
| Critical | PagerDuty | 5 min |
| Warning | Slack #alerts | 30 min |
| Info | Dashboard only | N/A |

---

### 7.3 Prometheus Query Best Practices

**Decision:** Optimized PromQL queries for dashboards and alerts

**Rationale:**
- Pre-aggregated recording rules reduce query load
- Label filtering minimizes cardinality
- Rate functions for counter metrics
- Histogram quantiles for latency percentiles

**Recording Rules:**
```yaml
# infrastructure/prometheus/recording-rules.yaml
groups:
  - name: RawDrive-recording-rules
    rules:
      # Pre-aggregate request rates by service
      - record: RawDrive:http_requests:rate5m
        expr: sum(rate(traefik_service_requests_total[5m])) by (service, code)

      # Pre-aggregate error rates
      - record: RawDrive:http_error_rate:ratio5m
        expr: |
          sum(rate(traefik_service_requests_total{code=~"5.."}[5m])) by (service)
          / sum(rate(traefik_service_requests_total[5m])) by (service)

      # Pre-aggregate latency percentiles
      - record: RawDrive:http_latency_p95:seconds
        expr: |
          histogram_quantile(0.95,
            sum(rate(traefik_service_request_duration_seconds_bucket[5m]))
            by (le, service)
          )

      # Pre-aggregate database metrics
      - record: RawDrive:db_connections:ratio
        expr: |
          pg_stat_activity_count{datname="RawDrive"}
          / pg_settings_max_connections

      # Pre-aggregate Kafka lag
      - record: RawDrive:kafka_lag:total
        expr: sum(kafka_consumergroup_lag) by (consumergroup, topic)
```

**Dashboard Queries:**
```promql
# Request rate by service (use recording rule)
RawDrive:http_requests:rate5m

# Error rate percentage
RawDrive:http_error_rate:ratio5m * 100

# P95 latency in milliseconds
RawDrive:http_latency_p95:seconds * 1000

# Active users (unique IPs in last hour)
count(sum by (client_ip) (
  increase(traefik_service_requests_total[1h])
))

# Top 10 slowest endpoints
topk(10,
  histogram_quantile(0.95,
    sum(rate(traefik_service_request_duration_seconds_bucket[5m]))
    by (le, service, method, path)
  )
)
```

---

## Appendix: Technology Versions

| Technology | Version | Notes |
|------------|---------|-------|
| Python | 3.11+ | FastAPI backend |
| Node.js | 20+ | Frontend, website |
| PostgreSQL | 16 | With pgvector extension |
| Redis | 7 | Cache, broker |
| Kafka | 7.5 | Event streaming |
| Traefik | v3 | API gateway |
| React | 19 | Frontend |
| React Native | 0.73+ | Mobile |
| KEDA | 2.12+ | Autoscaling |
| Prometheus | 2.x | Metrics |
| Grafana | 10.x | Dashboards |

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [TUS Protocol](https://tus.io/protocols/resumable-upload.html)
- [KEDA Documentation](https://keda.sh/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [ArcFace Paper](https://arxiv.org/abs/1801.07698)
