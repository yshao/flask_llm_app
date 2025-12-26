#!/bin/bash

# For Docker networking, use 'postgres' as hostname
# For local development, use 'localhost'
DB_HOST=${DATABASE_INIT_HOST:-postgres}

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready at ${DB_HOST}..."
until pg_isready -h ${DB_HOST} -U ${DATABASE_USER}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - creating database '$DATABASE_NAME' if it doesn't exist..."

# Create database if it doesn't exist
PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DB_HOST} -U ${DATABASE_USER} -c "SELECT 1 FROM pg_database WHERE datname = '$DATABASE_NAME'" | grep -q 1 || PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DB_HOST} -U ${DATABASE_USER} -c "CREATE DATABASE $DATABASE_NAME"

echo "Database '$DATABASE_NAME' is ready!"

# Enable pgvector extension
echo "Enabling pgvector extension..."
PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DB_HOST} -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "pgvector extension enabled!"