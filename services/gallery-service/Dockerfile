# ===========================================
# vDrive Gallery Service Dockerfile
# ===========================================
# Gallery management service on port 8004
# Dependencies: PostgreSQL, Redis, Kafka, R2

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies (include image processing libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Run application (migrations run separately in CI/CD)
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8004"]
