#!/bin/bash
# ============================================================================
# PostgreSQL + pgvector Initialization Script
# ============================================================================
# This script runs automatically on first container start via
# /docker-entrypoint-initdb.d/ mechanism provided by the postgres base image.
#
# It ensures:
# 1. The database is created
# 2. The pgvector extension is enabled
# ============================================================================

set -e

echo "=========================================="
echo "Initializing PostgreSQL with pgvector"
echo "=========================================="

# The database is automatically created by POSTGRES_DB environment variable
# This script just needs to enable the extension

echo "Enabling pgvector extension in database '${POSTGRES_DB}'..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable pgvector extension for vector embeddings
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Display confirmation
    SELECT 'pgvector extension enabled successfully!' AS status;
EOSQL

echo ""
echo "=========================================="
echo "Initialization complete!"
echo "=========================================="
echo "Database: ${POSTGRES_DB}"
echo "User: ${POSTGRES_USER}"
echo "Extension: vector (pgvector)"
echo "=========================================="
