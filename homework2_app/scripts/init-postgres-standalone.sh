#!/bin/bash
# =============================================================================
# PostgreSQL Initialization Script for Flask LLM App
# =============================================================================
# This script runs automatically when the PostgreSQL container starts
# for the first time (via docker-entrypoint-initdb.d)
# =============================================================================

set -e

echo "=========================================="
echo "PostgreSQL Initialization"
echo "=========================================="

# Wait for PostgreSQL to be ready
until pg_isready -U postgres > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL to start..."
    sleep 2
done

echo "PostgreSQL is ready!"

# Enable pgvector extension
echo ""
echo "Enabling pgvector extension..."
psql -v ON_ERROR_STOP=1 -U postgres -d "$POSTGRES_DB" <<-EOSQL
-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
EOSQL

if [ $? -eq 0 ]; then
    echo "✓ pgvector extension enabled successfully!"
else
    echo "✗ Failed to enable pgvector extension"
    exit 1
fi

echo ""
echo "=========================================="
echo "Initialization Complete!"
echo "=========================================="
echo ""
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo "Port: 5432"
echo ""
echo "To connect:"
echo "  docker exec -it flask_llm_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB"
