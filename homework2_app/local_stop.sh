#!/bin/bash
# ============================================================================
# Stop Script for homework2_app Local Deployment
# ============================================================================

echo "=============================================="
echo "  STOPPING HOMEWORK2 APP"
echo "=============================================="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Stop PostgreSQL containers
echo "🛑 Stopping PostgreSQL containers..."
docker compose down
echo "✓ Containers stopped"
echo ""

echo "=============================================="
echo "  ALL SERVICES STOPPED"
echo "=============================================="
