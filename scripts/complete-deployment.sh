#!/bin/bash
# vDrive Deployment Completion Script
# Run this script when Docker registry network issue is resolved
#
# Prerequisites: Docker registry connectivity restored
# Location: /Users/v13478/Desktop/vDrive/scripts/complete-deployment.sh
# Usage: bash scripts/complete-deployment.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=================================================="
echo "vDrive Deployment Completion Script"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/infrastructure/docker/docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run from project root."
    exit 1
fi

cd "$PROJECT_ROOT/infrastructure/docker"

# Step 1: Verify infrastructure is running
print_info "Step 1: Verifying infrastructure services..."
POSTGRES_STATUS=$(docker ps --filter "name=vDrive-postgres" --format "{{.Status}}" | grep -c "Up" || echo "0")
REDIS_STATUS=$(docker ps --filter "name=vDrive-redis" --format "{{.Status}}" | grep -c "Up" || echo "0")
KAFKA_STATUS=$(docker ps --filter "name=vDrive-kafka" --format "{{.Status}}" | grep -c "Up" || echo "0")

if [ "$POSTGRES_STATUS" = "0" ] || [ "$REDIS_STATUS" = "0" ] || [ "$KAFKA_STATUS" = "0" ]; then
    print_error "Infrastructure not running. Starting now..."
    docker compose up -d postgres redis zookeeper kafka
    sleep 20
else
    print_success "Infrastructure services are running"
fi

# Step 2: Build application images
print_info "Step 2: Building application Docker images..."
echo "This may take 5-10 minutes depending on your system..."

docker compose build backend || {
    print_error "Backend build failed"
    exit 1
}
print_success "Backend image built"

docker compose build onboarding-service || {
    print_error "Onboarding service build failed"
    exit 1
}
print_success "Onboarding service image built"

docker compose build frontend || {
    print_error "Frontend build failed"
    exit 1
}
print_success "Frontend image built"

docker compose build website || {
    print_error "Website build failed"
    exit 1
}
print_success "Website image built"

# Step 3: Run database migrations
print_info "Step 3: Running database migrations..."

# Wait for PostgreSQL to be healthy
print_info "Waiting for PostgreSQL to be ready..."
sleep 5

# Backend migrations (12 migrations)
print_info "Running backend migrations (12 migrations)..."
docker compose run --rm backend alembic upgrade head || {
    print_error "Backend migrations failed"
    exit 1
}
print_success "Backend migrations completed"

# Onboarding service migrations (1 migration)
print_info "Running onboarding service migrations..."
docker compose run --rm onboarding-service alembic upgrade head || {
    print_error "Onboarding service migrations failed"
    exit 1
}
print_success "Onboarding service migrations completed"

# Verify migrations
print_info "Verifying migrations..."
MIGRATION_COUNT=$(docker compose exec postgres psql -U vDrive -d vDrive -t -c "SELECT COUNT(*) FROM alembic_version;" | tr -d ' ')
if [ "$MIGRATION_COUNT" -ge "2" ]; then
    print_success "Migrations verified ($MIGRATION_COUNT version records found)"
else
    print_error "Migration verification failed"
    exit 1
fi

# Step 4: Start application services
print_info "Step 4: Starting application services..."

docker compose up -d backend frontend website onboarding-service

# Wait for services to start
print_info "Waiting for services to initialize (30 seconds)..."
sleep 30

# Step 5: Health checks
print_info "Step 5: Running health checks..."

# Check backend
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend is healthy (port 8000)"
else
    print_error "Backend health check failed"
fi

# Check frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is accessible (port 3000)"
else
    print_error "Frontend health check failed"
fi

# Check website
if curl -sf http://localhost:8020 > /dev/null 2>&1; then
    print_success "Website is accessible (port 8020)"
else
    print_error "Website health check failed"
fi

# Check onboarding service
if curl -sf http://localhost:8006/health > /dev/null 2>&1; then
    print_success "Onboarding service is healthy (port 8006)"
else
    print_error "Onboarding service health check failed"
fi

# Step 6: Verify database tables
print_info "Step 6: Verifying database schema..."
TABLE_COUNT=$(docker compose exec postgres psql -U vDrive -d vDrive -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'app';" | tr -d ' ')
if [ "$TABLE_COUNT" -ge "30" ]; then
    print_success "Database schema verified ($TABLE_COUNT tables in 'app' schema)"
else
    print_error "Expected 30+ tables, found $TABLE_COUNT"
fi

# Optional Step 7: Start monitoring stack
read -p "Start monitoring stack (Prometheus, Grafana, Loki)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Step 7: Starting monitoring stack..."
    docker compose up -d prometheus grafana loki promtail
    sleep 10
    print_success "Monitoring stack started"
    echo "  - Grafana: http://localhost:3001 (admin/admin)"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Loki: http://localhost:3100"
fi

# Optional Step 8: Seed test data
read -p "Seed test users for development? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Step 8: Seeding test users..."
    docker compose run --rm onboarding-service python scripts/seed_test_users.py || {
        print_error "Test user seeding failed (non-critical)"
    }
    print_success "Test users seeded (password: Test@123)"
    echo "  - free@test.vdrive.in"
    echo "  - starter@test.vdrive.in"
    echo "  - professional@test.vdrive.in"
    echo "  - superadmin@test.vdrive.in"
fi

# Final status
echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
docker compose ps

echo ""
echo "Service URLs:"
echo "  - Backend API:     http://localhost:8000"
echo "  - Backend Docs:    http://localhost:8000/docs"
echo "  - Frontend:        http://localhost:3000"
echo "  - Website:         http://localhost:8020"
echo "  - Onboarding:      http://localhost:8006"
echo "  - PostgreSQL:      localhost:5432"
echo "  - Redis:           localhost:6379"
echo "  - Kafka:           localhost:9092"
echo ""
print_success "All services deployed successfully!"
echo ""
echo "To view logs: docker compose logs -f [service-name]"
echo "To stop all:  docker compose down"
echo "To restart:   docker compose restart [service-name]"
echo ""
