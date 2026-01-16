#!/bin/bash
# wait-for-deps.sh - Wait for infrastructure dependencies to be ready
# Usage: ./wait-for-deps.sh [--postgres] [--redis] [--kafka] [--all]

set -e

# Configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-RawDrive}"

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

KAFKA_HOST="${KAFKA_HOST:-kafka}"
KAFKA_PORT="${KAFKA_PORT:-9092}"

ZOOKEEPER_HOST="${ZOOKEEPER_HOST:-zookeeper}"
ZOOKEEPER_PORT="${ZOOKEEPER_PORT:-2181}"

# Timeouts (seconds)
POSTGRES_TIMEOUT="${POSTGRES_TIMEOUT:-60}"
REDIS_TIMEOUT="${REDIS_TIMEOUT:-30}"
KAFKA_TIMEOUT="${KAFKA_TIMEOUT:-90}"
ZOOKEEPER_TIMEOUT="${ZOOKEEPER_TIMEOUT:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

wait_for_postgres() {
    log_info "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
    local start_time=$(date +%s)

    until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; do
        local elapsed=$(($(date +%s) - start_time))
        if [ "$elapsed" -ge "$POSTGRES_TIMEOUT" ]; then
            log_error "PostgreSQL did not become ready within ${POSTGRES_TIMEOUT}s"
            return 1
        fi
        echo -n "."
        sleep 2
    done

    echo ""
    log_info "PostgreSQL is ready!"
}

wait_for_redis() {
    log_info "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
    local start_time=$(date +%s)

    until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; do
        local elapsed=$(($(date +%s) - start_time))
        if [ "$elapsed" -ge "$REDIS_TIMEOUT" ]; then
            log_error "Redis did not become ready within ${REDIS_TIMEOUT}s"
            return 1
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    log_info "Redis is ready!"
}

wait_for_zookeeper() {
    log_info "Waiting for Zookeeper at ${ZOOKEEPER_HOST}:${ZOOKEEPER_PORT}..."
    local start_time=$(date +%s)

    until echo "ruok" | nc -w 2 "$ZOOKEEPER_HOST" "$ZOOKEEPER_PORT" 2>/dev/null | grep -q "imok"; do
        local elapsed=$(($(date +%s) - start_time))
        if [ "$elapsed" -ge "$ZOOKEEPER_TIMEOUT" ]; then
            log_error "Zookeeper did not become ready within ${ZOOKEEPER_TIMEOUT}s"
            return 1
        fi
        echo -n "."
        sleep 2
    done

    echo ""
    log_info "Zookeeper is ready!"
}

wait_for_kafka() {
    log_info "Waiting for Kafka at ${KAFKA_HOST}:${KAFKA_PORT}..."
    local start_time=$(date +%s)

    # First wait for Zookeeper since Kafka depends on it
    wait_for_zookeeper || return 1

    # Then wait for Kafka broker to be available
    until kafka-topics --bootstrap-server "${KAFKA_HOST}:${KAFKA_PORT}" --list > /dev/null 2>&1; do
        local elapsed=$(($(date +%s) - start_time))
        if [ "$elapsed" -ge "$KAFKA_TIMEOUT" ]; then
            log_error "Kafka did not become ready within ${KAFKA_TIMEOUT}s"
            return 1
        fi
        echo -n "."
        sleep 3
    done

    echo ""
    log_info "Kafka is ready!"
}

wait_for_all() {
    log_info "Waiting for all infrastructure dependencies..."
    echo ""

    wait_for_postgres || exit 1
    wait_for_redis || exit 1
    wait_for_kafka || exit 1

    echo ""
    log_info "All infrastructure dependencies are ready!"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Wait for infrastructure dependencies to be ready before starting services."
    echo ""
    echo "Options:"
    echo "  --postgres    Wait for PostgreSQL only"
    echo "  --redis       Wait for Redis only"
    echo "  --kafka       Wait for Kafka (includes Zookeeper)"
    echo "  --zookeeper   Wait for Zookeeper only"
    echo "  --all         Wait for all dependencies (default)"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  POSTGRES_HOST      PostgreSQL host (default: postgres)"
    echo "  POSTGRES_PORT      PostgreSQL port (default: 5432)"
    echo "  POSTGRES_USER      PostgreSQL user (default: RawDrive)"
    echo "  POSTGRES_TIMEOUT   PostgreSQL wait timeout in seconds (default: 60)"
    echo ""
    echo "  REDIS_HOST         Redis host (default: redis)"
    echo "  REDIS_PORT         Redis port (default: 6379)"
    echo "  REDIS_TIMEOUT      Redis wait timeout in seconds (default: 30)"
    echo ""
    echo "  KAFKA_HOST         Kafka host (default: kafka)"
    echo "  KAFKA_PORT         Kafka port (default: 9092)"
    echo "  KAFKA_TIMEOUT      Kafka wait timeout in seconds (default: 90)"
    echo ""
    echo "  ZOOKEEPER_HOST     Zookeeper host (default: zookeeper)"
    echo "  ZOOKEEPER_PORT     Zookeeper port (default: 2181)"
    echo "  ZOOKEEPER_TIMEOUT  Zookeeper wait timeout in seconds (default: 30)"
}

# Main
case "${1:-}" in
    --postgres)
        wait_for_postgres
        ;;
    --redis)
        wait_for_redis
        ;;
    --kafka)
        wait_for_kafka
        ;;
    --zookeeper)
        wait_for_zookeeper
        ;;
    --all|"")
        wait_for_all
        ;;
    -h|--help)
        show_help
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
