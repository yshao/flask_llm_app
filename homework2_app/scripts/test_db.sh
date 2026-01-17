#!/bin/bash
# =============================================================================
# test_db.sh - Database Connection Test Helper
# =============================================================================
# Tests connection to PostgreSQL database using docker exec + pg_isready
# Exit 0 if connected, exit 1 if not
# =============================================================================

set -e

# Configuration (can be overridden via environment)
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-flask_llm_postgres}"
DB_USER="${DATABASE_USER:-postgres}"
DB_NAME="${DATABASE_NAME:-homework_db}"

# Colors
RESET='\033[0m'
GREEN='\033[32m'
RED='\033[31m'
CYAN='\033[36m'

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${RESET}"
}

print_info() {
    echo -e "${CYAN}→ $1${RESET}"
}

# Main test logic
main() {
    print_info "Testing database connection..."

    # Check if container is running
    if ! docker ps --filter "name=${POSTGRES_CONTAINER}" --format "{{.Names}}" | grep -q "${POSTGRES_CONTAINER}"; then
        print_error "Container '${POSTGRES_CONTAINER}' is not running"
        echo "Start with: make db-up"
        exit 1
    fi

    # Test if database is accepting connections
    if docker exec "${POSTGRES_CONTAINER}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; then
        print_success "Database connection OK (container: ${POSTGRES_CONTAINER}, db: ${DB_NAME})"
        exit 0
    else
        print_error "Database not ready"
        exit 1
    fi
}

main "$@"
