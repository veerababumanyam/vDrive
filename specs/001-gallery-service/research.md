# Phase 0 Research: Gallery Service Technical Decisions

## Overview

This document consolidates the technical research conducted for the Gallery Service microservice implementation. Each section presents the decision made, the rationale behind it, and alternatives that were considered and rejected.

## 1. WebSocket Implementation for Real-Time Proofing

### Decision
**Native FastAPI WebSocket + Redis Pub/Sub with Broadcaster library**

### Rationale
- **ASGI-Native**: FastAPI's native WebSocket support integrates seamlessly with the existing async architecture
- **Multi-Pod Broadcasting**: Redis pub/sub via Broadcaster library enables message delivery across multiple Gallery Service pods during KEDA scaling
- **Performance at Scale**: Supports 500 concurrent WebSocket connections per pod (meets FR-017 requirement)
- **Graceful Shutdown**: Compatible with KEDA's pod termination workflow - can drain connections during scale-down events
- **Simple Protocol**: Direct WebSocket messaging without protocol overhead (Socket.IO uses multiple HTTP requests for handshake)
- **Production-Proven**: Used extensively in high-traffic FastAPI applications

### Implementation Pattern
```python
from broadcaster import Broadcast
from fastapi import WebSocket, WebSocketDisconnect

broadcast = Broadcast("redis://redis:6379/0")

class ProofingConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, gallery_id: str):
        await websocket.accept()
        if gallery_id not in self.active_connections:
            self.active_connections[gallery_id] = set()
        self.active_connections[gallery_id].add(websocket)

    async def broadcast_to_room(self, gallery_id: str, message: dict):
        """Publish to Redis channel for cross-pod delivery"""
        await broadcast.publish(
            channel=f"gallery:{gallery_id}:proofing",
            message=json.dumps(message)
        )

    async def listen_to_room(self, gallery_id: str):
        """Subscribe to Redis channel and forward to local WebSocket clients"""
        async with broadcast.subscribe(channel=f"gallery:{gallery_id}:proofing") as subscriber:
            async for event in subscriber:
                message = json.loads(event.message)
                for connection in self.active_connections.get(gallery_id, set()):
                    try:
                        await connection.send_json(message)
                    except WebSocketDisconnect:
                        self.active_connections[gallery_id].discard(connection)

@app.websocket("/ws/gallery/{gallery_id}")
async def websocket_endpoint(websocket: WebSocket, gallery_id: str):
    await manager.connect(websocket, gallery_id)

    # Start listening to Redis pub/sub in background
    asyncio.create_task(manager.listen_to_room(gallery_id))

    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast favorite/selection events
            await manager.broadcast_to_room(gallery_id, {
                "type": data["type"],
                "asset_id": data["asset_id"],
                "user_id": data.get("user_id"),
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, gallery_id)
```

### Graceful Shutdown for KEDA Scaling
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await broadcast.connect()
    yield
    # Graceful shutdown: drain WebSocket connections
    for gallery_id, connections in manager.active_connections.items():
        for ws in connections:
            await ws.close(code=1001, reason="Server shutting down")
    await broadcast.disconnect()

# In Dockerfile
STOPSIGNAL SIGTERM

# In Kubernetes deployment
spec:
  terminationGracePeriodSeconds: 80
  containers:
    - name: gallery-service
      lifecycle:
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 30"]
```

### Client Reconnection Logic
```javascript
// Frontend: Exponential backoff reconnection
class WebSocketManager {
  connect(galleryId) {
    const ws = new WebSocket(`wss://app.vdrive.io/api/gallery/ws/gallery/${galleryId}`);

    ws.onclose = () => {
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => this.connect(galleryId), delay);
      this.reconnectAttempts++;
    };

    ws.onopen = () => {
      this.reconnectAttempts = 0;
      // Request missed messages via sequence number sync
      ws.send(JSON.stringify({ type: 'sync', lastSeq: this.lastSequenceNumber }));
    };
  }
}
```

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **python-socketio** | Protocol overhead (multiple HTTP requests for handshake), heavier library footprint, Socket.IO client required on frontend |
| **websockets library** | Lower-level than FastAPI native, requires manual ASGI integration, slower development velocity |
| **picows** | Overly complex for use case, designed for ultra-high-frequency trading (100k+ connections/pod), adds unnecessary optimization complexity |
| **Pusher/Ably (3rd-party)** | Vendor lock-in, additional cost, latency from external service, doesn't meet self-hosted requirement |

---

## 2. LQIP Generation and Caching Strategy

### Decision
**Pillow for 16x16 WebP LQIP + Cloudflare R2 Signed URLs (4hr TTL) + Immutable Cache Headers**

### Rationale
- **Native Python**: Pillow (PIL) is the de-facto standard for image processing in Python, no external dependencies
- **WebP Block Encoding**: 16x16 dimensions align with WebP's 16x16 block encoding for optimal compression (~100-200 bytes)
- **Security vs. Performance Balance**: 4-hour TTL for signed URLs provides reasonable security window while maximizing cache hit rates
- **Immutable Headers**: `Cache-Control: private, max-age=14400, immutable` prevents unnecessary revalidation requests
- **Cursor-Based Pagination**: O(1) performance for paginating 10,000+ photos (doesn't degrade with offset)
- **Prefetching Strategy**: Load next page at 75% scroll, prefetch lightbox neighbors (N-1, N+1) for instant navigation

### LQIP Generation Implementation
```python
from PIL import Image
import base64
from io import BytesIO

def generate_lqip(image_path: str, size: int = 16, quality: int = 70) -> str:
    """
    Generate Low Quality Image Placeholder (LQIP) as base64-encoded WebP.

    Args:
        image_path: Path to original image
        size: Target dimension (16x16 for WebP block alignment)
        quality: WebP quality (70 balances size vs. blur effect)

    Returns:
        Data URI: data:image/webp;base64,<base64-encoded-webp>
    """
    with Image.open(image_path) as img:
        # Preserve aspect ratio while fitting within size x size
        img.thumbnail((size, size), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='WebP', quality=quality, method=6)

        b64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/webp;base64,{b64_string}"

# Async variant for FastAPI endpoint
async def generate_lqip_async(image_bytes: bytes) -> str:
    """Generate LQIP from bytes (e.g., from R2 download)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: generate_lqip_from_bytes(image_bytes)
    )
```

### Signed URL Generation (Cloudflare R2)
```python
import boto3
from botocore.config import Config

# R2 client configuration
s3_client = boto3.client(
    's3',
    endpoint_url='https://<account-id>.r2.cloudflarestorage.com',
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)

def generate_signed_url(
    bucket: str,
    key: str,
    expiration: int = 14400  # 4 hours in seconds
) -> str:
    """
    Generate presigned URL for thumbnail access.

    Args:
        bucket: R2 bucket name (e.g., 'vdrive-thumbnails')
        key: Object key (e.g., 'workspace_id/gallery_id/asset_id_800x600.jpg')
        expiration: URL validity period (4 hours = 14400 seconds)

    Returns:
        Presigned URL valid for 4 hours
    """
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration,
        HttpMethod='GET'
    )
```

### Response Headers for Caching
```python
from fastapi import Response

@app.get("/api/gallery/{gallery_id}/photos")
async def get_gallery_photos(gallery_id: str, response: Response):
    photos = await fetch_gallery_photos(gallery_id)

    # Immutable cache headers (4-hour TTL matches signed URL expiration)
    response.headers["Cache-Control"] = "private, max-age=14400, immutable"
    response.headers["CDN-Cache-Control"] = "public, max-age=14400, immutable"

    return {
        "photos": [
            {
                "id": photo.id,
                "lqip": photo.lqip,  # Base64 data URI (already in DB)
                "thumbnail_url": generate_signed_url(
                    bucket='vdrive-thumbnails',
                    key=f'{photo.workspace_id}/{photo.gallery_id}/{photo.id}_800x600.jpg'
                ),
                "full_url": generate_signed_url(
                    bucket='vdrive-originals',
                    key=f'{photo.workspace_id}/{photo.gallery_id}/{photo.id}_original.jpg',
                    expiration=3600  # 1 hour for full-size downloads
                )
            }
            for photo in photos
        ]
    }
```

### Cursor-Based Pagination (O(1) Performance)
```python
from typing import Optional

@app.get("/api/gallery/{gallery_id}/photos")
async def get_gallery_photos(
    gallery_id: str,
    cursor: Optional[str] = None,
    limit: int = 50
):
    """
    Cursor-based pagination using (created_at, id) composite key.
    Performance: O(1) regardless of offset (unlike OFFSET/LIMIT which degrades).
    """
    query = select(GalleryAsset).where(
        GalleryAsset.gallery_id == gallery_id,
        GalleryAsset.status == 'visible'
    ).order_by(
        GalleryAsset.created_at.desc(),
        GalleryAsset.id.desc()
    ).limit(limit + 1)  # Fetch limit + 1 to determine if more pages exist

    if cursor:
        # Decode cursor: base64(created_at|id)
        decoded = base64.b64decode(cursor).decode('utf-8')
        cursor_created_at, cursor_id = decoded.split('|')

        query = query.where(
            or_(
                GalleryAsset.created_at < cursor_created_at,
                and_(
                    GalleryAsset.created_at == cursor_created_at,
                    GalleryAsset.id < cursor_id
                )
            )
        )

    results = await db.execute(query)
    photos = results.scalars().all()

    has_more = len(photos) > limit
    if has_more:
        photos = photos[:limit]

    next_cursor = None
    if has_more and photos:
        last_photo = photos[-1]
        next_cursor = base64.b64encode(
            f"{last_photo.created_at.isoformat()}|{last_photo.id}".encode()
        ).decode()

    return {
        "photos": [serialize_photo(p) for p in photos],
        "next_cursor": next_cursor,
        "has_more": has_more
    }
```

### Frontend Prefetching with React Query
```javascript
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

function GalleryView({ galleryId }) {
  const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
    queryKey: ['gallery', galleryId],
    queryFn: ({ pageParam = null }) =>
      fetchGalleryPhotos(galleryId, pageParam),
    getNextPageParam: (lastPage) => lastPage.next_cursor,
  });

  // Prefetch next page at 75% scroll
  const { ref, inView } = useInView({ threshold: 0.75 });

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage]);

  return (
    <div>
      {data.pages.map((page) => (
        page.photos.map((photo) => (
          <PhotoCard
            key={photo.id}
            lqip={photo.lqip}
            thumbnailUrl={photo.thumbnail_url}
            onLightboxOpen={() => prefetchNeighbors(photo)}
          />
        ))
      ))}
      <div ref={ref} /> {/* Intersection observer trigger */}
    </div>
  );
}
```

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Thumbor** | Overly complex service (requires separate deployment), slower than Pillow for batch processing, Python 2 legacy issues |
| **Sharp (Node.js)** | Requires Node.js runtime in Python service, interop complexity, doesn't meet Python-native requirement |
| **20x20 LQIP** | WebP uses 16x16 block encoding - 20x20 wastes bytes with padding to 32x32 block boundary |
| **JPEG LQIP** | WebP achieves 25-40% better compression than JPEG at same quality, faster decode in modern browsers |
| **2-hour signed URL TTL** | Too short - causes cache invalidation during typical gallery viewing session (photographers spend 30-60 min reviewing) |
| **8-hour signed URL TTL** | Too long - increases risk window for URL sharing, violates security best practice of minimal privilege duration |
| **Offset-based pagination** | O(N) performance degrades with offset (OFFSET 9000 LIMIT 50 scans 9000 rows), cursor-based is O(1) |
| **CDN-only caching (no signed URLs)** | Can't enforce access control - anyone with URL can bypass Magic Link authorization |

---

## 3. KEDA Autoscaling Configuration

### Decision
**KEDA ScaledObject with Dual Prometheus Triggers (HTTP RPS + WebSocket Connections)**

### Rationale
- **Event-Driven Scaling**: KEDA monitors real-time metrics (Prometheus) and scales instantly when thresholds are breached
- **Custom Metrics Support**: Can scale based on application-specific metrics (WebSocket connections, not just CPU/memory)
- **Multi-Trigger Logic**: OR condition between HTTP RPS and WebSocket connection triggers ensures scaling for both traffic patterns
- **Production-Proven**: KEDA is CNCF graduated project, used by major platforms (Microsoft, Red Hat, Bloomberg)
- **Cost Efficiency**: Scales to zero during idle periods (not applicable for Gallery Service with minReplicaCount: 5)
- **Graceful Pod Termination**: Integrates with Kubernetes pod lifecycle for draining connections during scale-down

### KEDA ScaledObject Configuration
```yaml
# infrastructure/kubernetes/gallery-service/keda-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: gallery-service-scaledobject
  namespace: vdrive
spec:
  scaleTargetRef:
    name: gallery-service
  pollingInterval: 15  # Check metrics every 15 seconds
  cooldownPeriod: 60   # Wait 60 seconds before scaling down after last trigger
  minReplicaCount: 5   # Minimum replicas (high-traffic service)
  maxReplicaCount: 50  # Maximum replicas

  triggers:
    # Trigger 1: HTTP Request Rate (RPS)
    - type: prometheus
      metadata:
        serverAddress: http://prometheus.vdrive.svc.cluster.local:9090
        metricName: http_request_rate
        query: |
          sum(rate(http_requests_total{
            job="gallery-service",
            method!="OPTIONS"
          }[1m]))
        threshold: "100"  # Scale up when total RPS > 100

    # Trigger 2: WebSocket Active Connections
    - type: prometheus
      metadata:
        serverAddress: http://prometheus.vdrive.svc.cluster.local:9090
        metricName: websocket_connections
        query: |
          sum(websocket_active_connections{
            job="gallery-service"
          })
        threshold: "500"  # Scale up when total connections > 500 per pod

  # Advanced HPA behavior: conservative scale-down, aggressive scale-up
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
          policies:
            - type: Percent
              value: 10          # Max 10% pods removed per period
              periodSeconds: 60  # Every 60 seconds
        scaleUp:
          stabilizationWindowSeconds: 0  # Scale up immediately
          policies:
            - type: Percent
              value: 100         # Double pod count if needed
              periodSeconds: 15  # Every 15 seconds
            - type: Pods
              value: 4           # Or add 4 pods, whichever is larger
              periodSeconds: 15
          selectPolicy: Max      # Use the larger of Percent or Pods
```

### Prometheus Metrics Instrumentation
```python
# src/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# WebSocket connection metrics
websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections',
    ['gallery_id']
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages sent/received',
    ['direction', 'message_type']
)

# Application-specific metrics
gallery_views_total = Counter(
    'gallery_views_total',
    'Total gallery views via Magic Link',
    ['workspace_id']
)

lqip_generation_duration_seconds = Histogram(
    'lqip_generation_duration_seconds',
    'LQIP generation latency'
)
```

### Middleware Integration
```python
# src/app/middleware/metrics.py
from starlette.middleware.base import BaseHTTPMiddleware
import time

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

# Register middleware
app.add_middleware(PrometheusMiddleware)
```

### WebSocket Connection Tracking
```python
class ProofingConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, gallery_id: str):
        await websocket.accept()

        if gallery_id not in self.active_connections:
            self.active_connections[gallery_id] = set()

        self.active_connections[gallery_id].add(websocket)

        # Update Prometheus gauge
        websocket_active_connections.labels(gallery_id=gallery_id).inc()

    def disconnect(self, websocket: WebSocket, gallery_id: str):
        if gallery_id in self.active_connections:
            self.active_connections[gallery_id].discard(websocket)

            # Update Prometheus gauge
            websocket_active_connections.labels(gallery_id=gallery_id).dec()

            # Cleanup empty rooms
            if not self.active_connections[gallery_id]:
                del self.active_connections[gallery_id]
```

### Graceful Shutdown for Scaling
```python
# src/app/main.py
import signal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Gallery Service starting")
    await broadcast.connect()

    # Register shutdown handlers
    shutdown_event = asyncio.Event()

    def handle_sigterm(signum, frame):
        logger.info("SIGTERM received, initiating graceful shutdown")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, handle_sigterm)

    yield

    # Shutdown: drain WebSocket connections
    logger.info(f"Draining {sum(len(conns) for conns in manager.active_connections.values())} WebSocket connections")

    for gallery_id, connections in list(manager.active_connections.items()):
        for ws in connections:
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

    await broadcast.disconnect()
    logger.info("Graceful shutdown complete")
```

### Kubernetes Deployment Configuration
```yaml
# infrastructure/kubernetes/gallery-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gallery-service
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 80  # 30s preStop + 50s for draining
      containers:
        - name: gallery-service
          image: vdrive/gallery-service:latest
          ports:
            - containerPort: 8004
              name: http

          # Health checks
          livenessProbe:
            httpGet:
              path: /health
              port: 8004
            initialDelaySeconds: 10
            periodSeconds: 10

          readinessProbe:
            httpGet:
              path: /ready
              port: 8004
            initialDelaySeconds: 5
            periodSeconds: 5

          # Graceful shutdown: remove from load balancer before SIGTERM
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 30"]

          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"
```

### Monitoring KEDA Scaling
```bash
# Check ScaledObject status
kubectl get scaledobject gallery-service-scaledobject -n vdrive

# View HPA created by KEDA
kubectl get hpa -n vdrive

# Watch scaling events
kubectl get events -n vdrive --field-selector reason=SuccessfulRescale --watch

# Check current pod count
kubectl get pods -n vdrive -l app=gallery-service

# View KEDA operator logs
kubectl logs -f deployment/keda-operator -n keda
```

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Standard Kubernetes HPA (CPU/Memory)** | Cannot scale based on WebSocket connections or HTTP RPS, only CPU/memory (not representative of actual load) |
| **HPA with custom metrics adapter** | More complex setup than KEDA, requires separate metrics server deployment, less community support |
| **KEDA Redis Scaler** | Wrong metrics - Redis queue depth doesn't represent gallery viewing load (WebSocket connections + HTTP requests are correct signals) |
| **Manual scaling via kubectl** | Not automated, requires human intervention, defeats purpose of event-driven autoscaling |
| **Cluster Autoscaler only** | Scales nodes, not pods - KEDA handles pod-level scaling which is faster and more cost-efficient |
| **Vertical Pod Autoscaler (VPA)** | Adjusts resource requests/limits but doesn't add replicas - Gallery Service needs horizontal scaling for 50,000 concurrent viewers |

---

## Summary of Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | Python 3.11 + FastAPI | Async web framework with ASGI support |
| **WebSocket** | FastAPI native WebSocket + Broadcaster | Real-time proofing with multi-pod support |
| **Pub/Sub** | Redis (via Broadcaster) | Cross-pod WebSocket message broadcasting |
| **Image Processing** | Pillow (PIL) | LQIP generation (16x16 WebP) |
| **Object Storage** | Cloudflare R2 (S3-compatible) | Thumbnail and original photo storage |
| **Signed URLs** | boto3 (AWS SDK) | 4-hour TTL presigned URLs for thumbnails |
| **Autoscaling** | KEDA 2.12+ | Event-driven pod scaling based on Prometheus metrics |
| **Metrics** | prometheus_client | HTTP request rate, WebSocket connection count |
| **Monitoring** | Prometheus + Grafana + Loki | Metrics collection, dashboards, log aggregation |

---

## Next Steps

With Phase 0 research complete, proceed to **Phase 1: Data Model and API Contracts**:

1. **Generate `data-model.md`**: Define entities (Gallery, Sub-Gallery, Share Link, Gallery Asset, Visitor, Gallery Visitor, WebSocket Connection) with fields, relationships, validation rules, and state transitions
2. **Generate API contracts**: Create OpenAPI schemas in `/contracts/` directory mapping functional requirements to endpoints
3. **Generate `quickstart.md`**: Document setup instructions for Gallery Service (environment variables, dependencies, running instructions)
4. **Update agent context**: Run `.specify/scripts/bash/update-agent-context.sh claude` to add new technologies from current plan

All technical decisions are now documented with clear rationale and alternatives considered. Implementation can proceed with confidence.
