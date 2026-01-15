# ===========================================
# vDrive AI Search Service Dockerfile
# ===========================================
# Semantic search, RAG chat, and caption generation on port 8009
# Dependencies: PostgreSQL (pgvector), Kafka, Gemini API
# Includes: CLIP (sentence-transformers), LangChain

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies
# - libpq-dev: PostgreSQL client
# - build-essential: Build tools for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download CLIP model during build (reduces startup time)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-L-14')" || true

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY alembic/ ./alembic/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for API and metrics
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Run FastAPI application
CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8009"]
