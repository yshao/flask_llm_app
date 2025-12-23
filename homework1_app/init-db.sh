#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h ${DATABASE_HOST} -U ${DATABASE_USER}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - creating database '$DATABASE_NAME' if it doesn't exist..."

# Create database if it doesn't exist
PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USER} -c "SELECT 1 FROM pg_database WHERE datname = '$DATABASE_NAME'" | grep -q 1 || PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USER} -c "CREATE DATABASE $DATABASE_NAME"

echo "Database '$DATABASE_NAME' is ready!"