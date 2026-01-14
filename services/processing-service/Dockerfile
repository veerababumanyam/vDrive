# ===========================================
# vDrive Processing Service Dockerfile
# ===========================================
# Kafka consumer for media processing on port 8010
# Dependencies: PostgreSQL, Kafka, R2, Google Cloud Vision
# Includes: ffmpeg, rawpy (RAW photo processing)

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies for image/video processing
# - ffmpeg: Video thumbnail extraction
# - libjpeg, libpng, zlib: Pillow image processing
# - libraw: rawpy RAW photo support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    ffmpeg \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libraw-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for metrics
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Run Kafka consumer application
CMD ["python", "-m", "src.app.main"]
