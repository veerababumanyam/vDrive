# ===========================================
# RawDrive Onboarding Service Dockerfile
# ===========================================
# User registration and email verification on port 8006

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy Alembic migrations
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy scripts (including entrypoint and seed scripts)
COPY scripts/ ./scripts/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Run entrypoint (migrations + seeding + app)
ENTRYPOINT ["/bin/bash", "scripts/docker-entrypoint.sh"]
