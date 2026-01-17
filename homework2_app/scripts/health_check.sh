#!/bin/bash
# =============================================================================
# health_check.sh - Comprehensive Health Check
# =============================================================================
# Tests both database and application health
# Exit 0 if all healthy, exit 1 if any failed
# =============================================================================

set -e

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# Colors
RESET='\033[0m'
GREEN='\033[32m'
RED='\033[31m'
CYAN='\033[36m'
YELLOW='\033[33m'

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${RESET}"
}

print_header() {
    echo ""
    echo "=============================================="
    echo "  SYSTEM HEALTH CHECK"
    echo "=============================================="
    echo ""
}

# Main health check logic
main() {
    print_header

    # Track overall status
    all_healthy=true

    # Test database
    echo -e "${CYAN}1. Database:${RESET}"
    if "${SCRIPT_DIR}/test_db.sh" > /dev/null 2>&1; then
        echo "   ✓ Healthy"
    else
        echo "   ✗ Not healthy"
        all_healthy=false
    fi

    echo ""

    # Test application
    echo -e "${CYAN}2. Application:${RESET}"
    if "${SCRIPT_DIR}/test_app.sh" > /dev/null 2>&1; then
        echo "   ✓ Healthy"
    else
        echo "   ✗ Not healthy"
        all_healthy=false
    fi

    echo ""

    # Final result
    if [ "$all_healthy" = true ]; then
        print_success "All systems healthy"
        exit 0
    else
        print_error "Some systems are not healthy"
        exit 1
    fi
}

main "$@"
