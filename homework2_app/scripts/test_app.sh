#!/bin/bash
# =============================================================================
# test_app.sh - App Communication Test Helper
# =============================================================================
# Tests HTTP communication with Flask app using curl
# Exit 0 if responding, exit 1 if not
# =============================================================================

set -e

# Configuration
APP_HOST="${FLASK_HOST:-127.0.0.1}"
APP_PORT="${FLASK_PORT:-8080}"
APP_URL="http://${APP_HOST}:${APP_PORT}"
TIMEOUT="${CURL_TIMEOUT:-10}"

# Colors
RESET='\033[0m'
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
CYAN='\033[36m'

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${RESET}"
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${RESET}"
}

print_info() {
    echo -e "${CYAN}→ $1${RESET}"
}

# Main test logic
main() {
    print_info "Testing app communication at ${APP_URL}..."

    # Check if curl is available
    if ! command -v curl > /dev/null 2>&1; then
        print_error "curl is not installed"
        exit 1
    fi

    # Test HTTP endpoint
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "${TIMEOUT}" "${APP_URL}" 2>/dev/null || echo "000")

    # Check if response is valid (200, 302, or 404 are all acceptable - means app is running)
    if echo "${response_code}" | grep -qE "^(200|302|404)$"; then
        print_success "App communication OK (HTTP ${response_code})"
        exit 0
    else
        print_error "Unexpected response: ${response_code}"
        if [ "${response_code}" = "000" ]; then
            print_warning "Connection refused - app may not be running"
            echo "Start with: make app-start-bg"
        fi
        exit 1
    fi
}

main "$@"
