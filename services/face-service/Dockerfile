# ===========================================
# vDrive Face Service Dockerfile
# ===========================================
# Face detection, embedding, and clustering service on port 8002
# Dependencies: PostgreSQL (pgvector), Kafka, Redis, Google Cloud Vision
# Includes: DeepFace, TensorFlow for face embeddings

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies for ML and image processing
# - libgl1, libglib2.0: OpenCV dependencies for DeepFace
# - libpq-dev: PostgreSQL client
# - cmake, build-essential: Build tools for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY alembic/ ./alembic/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for API and metrics
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run FastAPI application
CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
