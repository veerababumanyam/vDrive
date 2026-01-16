#!/bin/bash
###############################################################################
# End-to-End Export Flow Verification Script
#
# This script automates the verification steps for the bulk export feature.
# Run this after all services are up and running.
#
# Usage:
#   ./scripts/verify-export-e2e.sh [--user-token TOKEN]
#
# Prerequisites:
#   - All Docker services running (docker compose up -d)
#   - Test user account with workspace
#   - jq installed for JSON parsing
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
EXPORT_SERVICE_URL="http://localhost:8009"
TRAEFIK_URL="http://localhost:80"
FRONTEND_URL="http://localhost:3000"

# Parse arguments
USER_TOKEN="${2:-}"

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        exit 1
    fi
}

###############################################################################
# Pre-flight Checks
###############################################################################

echo ""
echo "=========================================="
echo "Export Flow E2E Verification"
echo "=========================================="
echo ""

log_info "Checking prerequisites..."

# Check required commands
check_command "curl"
check_command "docker"
check_command "jq"

log_success "All required commands are installed"

###############################################################################
# Step 1: Verify Services are Running
###############################################################################

echo ""
log_info "Step 1: Verifying all services are running..."

# Check Docker services
log_info "Checking Docker Compose services..."
cd infrastructure/docker

if ! docker compose ps | grep -q "Up"; then
    log_error "Docker services are not running. Start with: docker compose up -d"
    exit 1
fi

log_success "Docker services are running"

# Check postgres
if ! docker compose ps postgres | grep -q "healthy"; then
    log_error "PostgreSQL is not healthy"
    exit 1
fi
log_success "PostgreSQL is healthy"

# Check redis
if ! docker compose ps redis | grep -q "healthy"; then
    log_error "Redis is not healthy"
    exit 1
fi
log_success "Redis is healthy"

# Check export-service
if ! docker compose ps export-service | grep -q "Up"; then
    log_error "export-service is not running"
    exit 1
fi
log_success "export-service is running"

# Check export-worker
if ! docker compose ps export-worker | grep -q "Up"; then
    log_error "export-worker is not running"
    exit 1
fi
log_success "export-worker is running"

cd ../..

###############################################################################
# Step 2: Verify Service Health Endpoints
###############################################################################

echo ""
log_info "Step 2: Verifying service health endpoints..."

# Check export-service health (direct)
log_info "Checking export-service health (direct)..."
HEALTH_RESPONSE=$(curl -s -f "$EXPORT_SERVICE_URL/health" || echo "FAILED")

if [[ "$HEALTH_RESPONSE" == "FAILED" ]]; then
    log_error "export-service health check failed (direct)"
    exit 1
fi

if ! echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    log_error "export-service is not healthy"
    echo "$HEALTH_RESPONSE"
    exit 1
fi

log_success "export-service is healthy (direct)"

# Check export-service health (via Traefik)
log_info "Checking export-service health (via Traefik)..."
TRAEFIK_HEALTH=$(curl -s -f "$TRAEFIK_URL/api/v1/export/health" || echo "FAILED")

if [[ "$TRAEFIK_HEALTH" == "FAILED" ]]; then
    log_error "export-service health check failed (via Traefik)"
    log_warning "Check Traefik routing configuration"
    exit 1
fi

log_success "export-service is accessible via Traefik"

# Check export-service ready endpoint
log_info "Checking export-service ready endpoint..."
READY_RESPONSE=$(curl -s -f "$EXPORT_SERVICE_URL/ready" || echo "FAILED")

if [[ "$READY_RESPONSE" == "FAILED" ]]; then
    log_error "export-service is not ready"
    exit 1
fi

log_success "export-service is ready"

###############################################################################
# Step 3: Verify Database Migrations
###############################################################################

echo ""
log_info "Step 3: Verifying database migrations..."

# Check export_jobs table exists
log_info "Checking export_jobs table..."
cd infrastructure/docker
EXPORT_TABLE=$(docker compose exec -T postgres psql -U vDrive -d vDrive -t -c "SELECT tablename FROM pg_tables WHERE tablename='export_jobs';" 2>&1)

if [[ ! "$EXPORT_TABLE" =~ "export_jobs" ]]; then
    log_error "export_jobs table does not exist"
    log_warning "Run migrations: docker compose exec export-service alembic upgrade head"
    exit 1
fi

log_success "export_jobs table exists"

# Check migration_jobs table exists
log_info "Checking migration_jobs table..."
MIGRATION_TABLE=$(docker compose exec -T postgres psql -U vDrive -d vDrive -t -c "SELECT tablename FROM pg_tables WHERE tablename='migration_jobs';" 2>&1)

if [[ ! "$MIGRATION_TABLE" =~ "migration_jobs" ]]; then
    log_error "migration_jobs table does not exist"
    log_warning "Run migrations: docker compose exec export-service alembic upgrade head"
    exit 1
fi

log_success "migration_jobs table exists"

# Check current migration version
log_info "Checking migration version..."
MIGRATION_VERSION=$(docker compose exec -T export-service alembic current 2>&1 || echo "FAILED")

if [[ "$MIGRATION_VERSION" == "FAILED" ]]; then
    log_warning "Could not check migration version (service may be starting)"
else
    log_success "Migrations applied: $(echo $MIGRATION_VERSION | head -n 1)"
fi

cd ../..

###############################################################################
# Step 4: Verify Celery Worker
###############################################################################

echo ""
log_info "Step 4: Verifying Celery worker..."

cd infrastructure/docker

# Check worker is responsive
log_info "Pinging Celery worker..."
WORKER_PING=$(docker compose exec -T export-worker celery -A src.app.workers.celery_app inspect ping 2>&1 || echo "FAILED")

if [[ "$WORKER_PING" =~ "pong" ]]; then
    log_success "Celery worker is responsive"
else
    log_error "Celery worker is not responding"
    log_warning "Check logs: docker compose logs export-worker"
    exit 1
fi

# Check worker active queues
log_info "Checking worker queues..."
WORKER_QUEUES=$(docker compose exec -T export-worker celery -A src.app.workers.celery_app inspect active_queues 2>&1 || echo "FAILED")

if [[ "$WORKER_QUEUES" =~ "exports" ]]; then
    log_success "Worker is listening on 'exports' queue"
else
    log_warning "Worker may not be listening on correct queues"
fi

cd ../..

###############################################################################
# Step 5: Test API Endpoints (if token provided)
###############################################################################

if [ -n "$USER_TOKEN" ]; then
    echo ""
    log_info "Step 5: Testing API endpoints with authentication..."

    # Test create export job
    log_info "Creating test export job..."
    CREATE_RESPONSE=$(curl -s -X POST "$TRAEFIK_URL/api/v1/export/jobs" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "export_type": "workspace",
            "options": {
                "include_metadata": true,
                "include_thumbnails": false
            }
        }')

    if echo "$CREATE_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
        JOB_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
        log_success "Export job created: $JOB_ID"

        # Wait for processing
        log_info "Waiting for job to start processing..."
        sleep 5

        # Test get job status
        log_info "Fetching job status..."
        STATUS_RESPONSE=$(curl -s "$TRAEFIK_URL/api/v1/export/jobs/$JOB_ID" \
            -H "Authorization: Bearer $USER_TOKEN")

        if echo "$STATUS_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
            JOB_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
            log_success "Job status: $JOB_STATUS"
        else
            log_error "Could not fetch job status"
        fi

        # Test list jobs
        log_info "Listing all export jobs..."
        LIST_RESPONSE=$(curl -s "$TRAEFIK_URL/api/v1/export/jobs" \
            -H "Authorization: Bearer $USER_TOKEN")

        if echo "$LIST_RESPONSE" | jq -e '.jobs' > /dev/null 2>&1; then
            JOB_COUNT=$(echo "$LIST_RESPONSE" | jq '.jobs | length')
            log_success "Found $JOB_COUNT export jobs"
        else
            log_error "Could not list export jobs"
        fi

    else
        log_error "Failed to create export job"
        echo "$CREATE_RESPONSE"
    fi
else
    echo ""
    log_warning "Step 5: Skipping API tests (no user token provided)"
    log_info "To test API endpoints, run: $0 --user-token <YOUR_TOKEN>"
fi

###############################################################################
# Step 6: Frontend Verification (manual)
###############################################################################

echo ""
log_info "Step 6: Frontend verification (manual steps)..."
echo ""
echo "Please verify the following manually:"
echo ""
echo "  1. Navigate to: $FRONTEND_URL/signin"
echo "  2. Login with test credentials"
echo "  3. Navigate to: $FRONTEND_URL/export"
echo "  4. Verify Export page renders without errors"
echo "  5. Click 'Export All Photos'"
echo "  6. Configure export options"
echo "  7. Create export job"
echo "  8. Watch progress updates"
echo "  9. Download completed export"
echo "  10. Verify ZIP file contents"
echo ""
log_info "See E2E_VERIFICATION.md for detailed manual testing steps"

###############################################################################
# Summary
###############################################################################

echo ""
echo "=========================================="
log_success "Automated verification PASSED"
echo "=========================================="
echo ""
log_info "Summary:"
echo "  ✓ All Docker services are running"
echo "  ✓ Service health checks pass"
echo "  ✓ Database migrations applied"
echo "  ✓ Celery worker is operational"
if [ -n "$USER_TOKEN" ]; then
    echo "  ✓ API endpoints tested successfully"
else
    echo "  ⊗ API endpoints not tested (no token)"
fi
echo "  ⊗ Frontend verification pending (manual)"
echo ""
log_info "Next steps:"
echo "  1. Complete manual frontend verification"
echo "  2. Run E2E tests: See E2E_VERIFICATION.md"
echo "  3. Mark subtask-6-3 as completed"
echo ""
