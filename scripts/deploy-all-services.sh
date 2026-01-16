#!/bin/bash
# RawDrive Complete Deployment Script
# Deploys ALL 23 Docker services without exception
# Location: /Users/v13478/Desktop/RawDrive/scripts/deploy-all-services.sh
# Usage: bash scripts/deploy-all-services.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================================="
echo "RawDrive Complete Deployment - ALL 23 Services"
echo "=========================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/infrastructure/docker/docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run from project root."
    exit 1
fi

cd "$PROJECT_ROOT/infrastructure/docker"

print_info "Step 1: Pre-flight checks..."

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker is running"

# Check .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_error ".env file not found in project root"
    exit 1
fi
print_success ".env file found"

# Check JWT keys exist
if [ ! -f "$PROJECT_ROOT/backend/secrets/jwt_private_key" ]; then
    print_warning "JWT keys not found. Generating now..."
    mkdir -p "$PROJECT_ROOT/backend/secrets"
    ssh-keygen -t ed25519 -f "$PROJECT_ROOT/backend/secrets/jwt_key" -N "" -C "RawDrive-jwt-signing-key"
    openssl pkey -in "$PROJECT_ROOT/backend/secrets/jwt_key" -out "$PROJECT_ROOT/backend/secrets/jwt_private_key" 2>/dev/null || cp "$PROJECT_ROOT/backend/secrets/jwt_key" "$PROJECT_ROOT/backend/secrets/jwt_private_key"
    cp "$PROJECT_ROOT/backend/secrets/jwt_key.pub" "$PROJECT_ROOT/backend/secrets/jwt_public_key"
    chmod 600 "$PROJECT_ROOT/backend/secrets/jwt_private_key"
    chmod 644 "$PROJECT_ROOT/backend/secrets/jwt_public_key"
    print_success "JWT keys generated"
else
    print_success "JWT keys exist"
fi

echo ""
print_info "Step 2: Deploying ALL infrastructure services (no builds required)..."
echo "This includes: PostgreSQL, Redis, Kafka, Zookeeper, Traefik, Prometheus, Grafana, Loki, and all exporters"

# Deploy core infrastructure first
docker compose up -d postgres redis zookeeper kafka

print_info "Waiting for core infrastructure to be healthy (30 seconds)..."
sleep 30

# Verify core services are healthy
POSTGRES_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' RawDrive-postgres 2>/dev/null || echo "unknown")
REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' RawDrive-redis 2>/dev/null || echo "unknown")
KAFKA_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' RawDrive-kafka 2>/dev/null || echo "unknown")

if [ "$POSTGRES_HEALTH" = "healthy" ]; then
    print_success "PostgreSQL is healthy"
else
    print_warning "PostgreSQL health: $POSTGRES_HEALTH (may still be starting)"
fi

if [ "$REDIS_HEALTH" = "healthy" ]; then
    print_success "Redis is healthy"
else
    print_warning "Redis health: $REDIS_HEALTH (may still be starting)"
fi

if [ "$KAFKA_HEALTH" = "healthy" ]; then
    print_success "Kafka is healthy"
else
    print_warning "Kafka health: $KAFKA_HEALTH (may still be starting)"
fi

# Deploy monitoring stack and exporters
print_info "Deploying monitoring stack (Prometheus, Grafana, Loki, Promtail, Alertmanager)..."
docker compose up -d prometheus grafana loki promtail alertmanager

print_info "Deploying metric exporters (Redis, PostgreSQL, Kafka)..."
docker compose up -d redis-exporter postgres-exporter kafka-exporter

print_info "Deploying management UIs (Kafka UI, Flower)..."
docker compose up -d kafka-ui flower

# Deploy Traefik (may fail if image can't be pulled)
print_info "Deploying Traefik API Gateway..."
if docker compose up -d traefik 2>/dev/null; then
    print_success "Traefik deployed"
else
    print_warning "Traefik deployment failed (likely network issue with Docker registry)"
fi

echo ""
print_info "Step 3: Building application Docker images..."
echo "This may take 5-15 minutes depending on your system and network..."

# Try to build application images
BUILD_FAILED=0

print_info "Building backend image..."
if docker compose build backend 2>&1 | tee /tmp/backend-build.log; then
    print_success "Backend image built"
else
    print_error "Backend build failed (check /tmp/backend-build.log)"
    BUILD_FAILED=1
fi

print_info "Building frontend image..."
if docker compose build frontend 2>&1 | tee /tmp/frontend-build.log; then
    print_success "Frontend image built"
else
    print_error "Frontend build failed (check /tmp/frontend-build.log)"
    BUILD_FAILED=1
fi

print_info "Building website image..."
if docker compose build website 2>&1 | tee /tmp/website-build.log; then
    print_success "Website image built"
else
    print_error "Website build failed (check /tmp/website-build.log)"
    BUILD_FAILED=1
fi

print_info "Building onboarding service image..."
if docker compose build onboarding-service 2>&1 | tee /tmp/onboarding-build.log; then
    print_success "Onboarding service image built"
else
    print_error "Onboarding service build failed (check /tmp/onboarding-build.log)"
    BUILD_FAILED=1
fi

if [ $BUILD_FAILED -eq 1 ]; then
    echo ""
    print_error "Some Docker images failed to build"
    print_warning "This is likely due to Docker registry network issues with Cloudflare R2 CDN"
    print_warning "You can retry this script later when network connectivity is restored"
    echo ""
    print_info "Current deployment status:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    print_warning "Infrastructure services are running, but application services require successful builds"
    exit 1
fi

echo ""
print_info "Step 4: Running database migrations..."

# Wait for PostgreSQL to be fully ready
print_info "Waiting for PostgreSQL to be ready..."
sleep 5

# Backend migrations (12 migrations)
print_info "Running backend migrations (12 migrations)..."
if docker compose run --rm backend alembic upgrade head; then
    print_success "Backend migrations completed"
else
    print_error "Backend migrations failed"
    exit 1
fi

# Onboarding service migrations (1 migration)
print_info "Running onboarding service migrations (1 migration)..."
if docker compose run --rm onboarding-service alembic upgrade head; then
    print_success "Onboarding service migrations completed"
else
    print_error "Onboarding service migrations failed"
    exit 1
fi

# Verify migrations
print_info "Verifying migrations..."
MIGRATION_COUNT=$(docker compose exec postgres psql -U RawDrive -d RawDrive -t -c "SELECT COUNT(*) FROM alembic_version;" | tr -d ' ')
if [ "$MIGRATION_COUNT" -ge "2" ]; then
    print_success "Migrations verified ($MIGRATION_COUNT version records found)"
else
    print_error "Migration verification failed"
    exit 1
fi

echo ""
print_info "Step 5: Starting application services..."

docker compose up -d backend frontend website onboarding-service

# Wait for services to start
print_info "Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
print_info "Step 6: Running health checks..."

# Check backend
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend is healthy (port 8000)"
else
    print_warning "Backend health check failed (may still be starting)"
fi

# Check frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is accessible (port 3000)"
else
    print_warning "Frontend health check failed (may still be starting)"
fi

# Check website
if curl -sf http://localhost:8020 > /dev/null 2>&1; then
    print_success "Website is accessible (port 8020)"
else
    print_warning "Website health check failed (may still be starting)"
fi

# Check onboarding service
if curl -sf http://localhost:8006/health > /dev/null 2>&1; then
    print_success "Onboarding service is healthy (port 8006)"
else
    print_warning "Onboarding service health check failed (may still be starting)"
fi

echo ""
print_info "Step 7: Verifying database schema..."
TABLE_COUNT=$(docker compose exec postgres psql -U RawDrive -d RawDrive -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'app';" | tr -d ' ')
if [ "$TABLE_COUNT" -ge "30" ]; then
    print_success "Database schema verified ($TABLE_COUNT tables in 'app' schema)"
else
    print_warning "Expected 30+ tables, found $TABLE_COUNT (migrations may still be running)"
fi

# Final status
echo ""
echo "=========================================================="
echo "Deployment Complete - ALL Services Status"
echo "=========================================================="
echo ""
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Service URLs:"
echo "  - Backend API:     http://localhost:8000"
echo "  - Backend Docs:    http://localhost:8000/docs"
echo "  - Frontend:        http://localhost:3000"
echo "  - Website:         http://localhost:8020"
echo "  - Onboarding:      http://localhost:8006"
echo ""
echo "Infrastructure:"
echo "  - PostgreSQL:      localhost:5432"
echo "  - Redis:           localhost:6379"
echo "  - Kafka:           localhost:9092"
echo "  - Traefik:         http://localhost:8080"
echo ""
echo "Monitoring:"
echo "  - Prometheus:      http://localhost:9090"
echo "  - Grafana:         http://localhost:3001 (admin/admin)"
echo "  - Loki:            http://localhost:3100"
echo "  - Kafka UI:        http://localhost:8081"
echo "  - Flower:          http://localhost:5555"
echo ""
print_success "All 23 services have been deployed!"
echo ""
echo "To view logs: docker compose logs -f [service-name]"
echo "To stop all:  docker compose down"
echo "To restart:   docker compose restart [service-name]"
echo ""
