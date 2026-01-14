#!/bin/bash
# validate-env.sh - Validate required environment variables before startup
# Usage: ./validate-env.sh [--service SERVICE_NAME]

set -e

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

# Required variables for all services
COMMON_REQUIRED=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET"
)

# Service-specific required variables
BACKEND_REQUIRED=(
    "KAFKA_BOOTSTRAP_SERVERS"
)

UPLOAD_REQUIRED=(
    "R2_ACCESS_KEY_ID"
    "R2_SECRET_ACCESS_KEY"
    "R2_BUCKET_NAME"
    "R2_ENDPOINT_URL"
    "KAFKA_BOOTSTRAP_SERVERS"
)

BILLING_REQUIRED=(
    "STRIPE_API_KEY"
    "STRIPE_WEBHOOK_SECRET"
)

FACE_REQUIRED=(
    "GOOGLE_APPLICATION_CREDENTIALS"
    "KAFKA_BOOTSTRAP_SERVERS"
)

NOTIFICATIONS_REQUIRED=(
    "SENDGRID_API_KEY"
    "SENDGRID_FROM_EMAIL"
    "KAFKA_BOOTSTRAP_SERVERS"
)

WEBHOOKS_REQUIRED=(
    "KAFKA_BOOTSTRAP_SERVERS"
)

GALLERY_REQUIRED=(
    "R2_PUBLIC_URL"
)

# Optional but recommended variables
OPTIONAL_RECOMMENDED=(
    "SENTRY_DSN"
    "LOG_LEVEL"
)

validate_var() {
    local var_name="$1"
    local is_optional="${2:-false}"

    if [ -z "${!var_name}" ]; then
        if [ "$is_optional" = "true" ]; then
            log_warn "Optional variable not set: $var_name"
            return 0
        else
            log_error "Required variable not set: $var_name"
            return 1
        fi
    else
        # Mask sensitive values in output
        local value="${!var_name}"
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"KEY"* ]] || [[ "$var_name" == *"PASSWORD"* ]] || [[ "$var_name" == *"TOKEN"* ]]; then
            value="${value:0:4}****${value: -4}"
        fi
        log_info "Found $var_name = $value"
        return 0
    fi
}

validate_url() {
    local var_name="$1"
    local value="${!var_name}"

    if [ -z "$value" ]; then
        return 0  # Skip if not set (will be caught by validate_var)
    fi

    # Basic URL validation
    if [[ ! "$value" =~ ^(https?|postgresql|redis|amqp):// ]]; then
        log_error "$var_name does not appear to be a valid URL: $value"
        return 1
    fi

    return 0
}

validate_jwt_secret() {
    local secret="$JWT_SECRET"

    if [ -z "$secret" ]; then
        return 0  # Skip if not set
    fi

    # Check minimum length (should be at least 32 bytes for HS256)
    if [ ${#secret} -lt 32 ]; then
        log_warn "JWT_SECRET is shorter than recommended (32+ characters)"
    fi

    # Check if it looks like a hex string (64 chars = 32 bytes)
    if [[ ${#secret} -ge 64 ]] && [[ "$secret" =~ ^[0-9a-fA-F]+$ ]]; then
        log_info "JWT_SECRET appears to be a valid hex-encoded secret"
    fi

    return 0
}

validate_common() {
    log_info "Validating common required variables..."
    local errors=0

    for var in "${COMMON_REQUIRED[@]}"; do
        validate_var "$var" || ((errors++))
    done

    # Additional validation
    validate_url "DATABASE_URL" || ((errors++))
    validate_url "REDIS_URL" || ((errors++))
    validate_jwt_secret || true  # Warning only

    return $errors
}

validate_service() {
    local service="$1"
    local errors=0

    log_info "Validating variables for service: $service"
    echo ""

    # Always validate common vars
    validate_common || ((errors++))
    echo ""

    # Service-specific validation
    case "$service" in
        backend)
            log_info "Validating backend-specific variables..."
            for var in "${BACKEND_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        upload)
            log_info "Validating upload service variables..."
            for var in "${UPLOAD_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        billing)
            log_info "Validating billing service variables..."
            for var in "${BILLING_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        face)
            log_info "Validating face service variables..."
            for var in "${FACE_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        notifications)
            log_info "Validating notifications service variables..."
            for var in "${NOTIFICATIONS_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        webhooks)
            log_info "Validating webhooks service variables..."
            for var in "${WEBHOOKS_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        gallery)
            log_info "Validating gallery service variables..."
            for var in "${GALLERY_REQUIRED[@]}"; do
                validate_var "$var" || ((errors++))
            done
            ;;
        *)
            log_warn "Unknown service: $service. Only validating common variables."
            ;;
    esac

    echo ""

    # Check optional variables
    log_info "Checking optional but recommended variables..."
    for var in "${OPTIONAL_RECOMMENDED[@]}"; do
        validate_var "$var" "true"
    done

    echo ""

    if [ $errors -gt 0 ]; then
        log_error "Validation failed with $errors error(s)"
        return 1
    else
        log_info "All required environment variables are set!"
        return 0
    fi
}

validate_all() {
    log_info "Validating all environment variables..."
    echo ""

    local errors=0

    validate_common || ((errors++))
    echo ""

    # Validate all service-specific vars
    for var in "${BACKEND_REQUIRED[@]}" "${UPLOAD_REQUIRED[@]}" "${BILLING_REQUIRED[@]}" \
               "${FACE_REQUIRED[@]}" "${NOTIFICATIONS_REQUIRED[@]}" "${WEBHOOKS_REQUIRED[@]}" \
               "${GALLERY_REQUIRED[@]}"; do
        validate_var "$var" || ((errors++))
    done

    echo ""

    # Check optional variables
    log_info "Checking optional but recommended variables..."
    for var in "${OPTIONAL_RECOMMENDED[@]}"; do
        validate_var "$var" "true"
    done

    echo ""

    if [ $errors -gt 0 ]; then
        log_error "Validation failed with $errors error(s)"
        return 1
    else
        log_info "All required environment variables are set!"
        return 0
    fi
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Validate required environment variables before starting services."
    echo ""
    echo "Options:"
    echo "  --service NAME    Validate variables for a specific service"
    echo "                    Services: backend, upload, billing, face,"
    echo "                              notifications, webhooks, gallery"
    echo "  --all             Validate all variables for all services"
    echo "  --common          Validate only common variables"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --common                 # Check common vars only"
    echo "  $0 --service backend        # Check backend service vars"
    echo "  $0 --service upload         # Check upload service vars"
    echo "  $0 --all                    # Check all vars for all services"
}

# Main
case "${1:-}" in
    --service)
        if [ -z "${2:-}" ]; then
            log_error "Service name required"
            show_help
            exit 1
        fi
        validate_service "$2"
        ;;
    --all)
        validate_all
        ;;
    --common|"")
        validate_common
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
