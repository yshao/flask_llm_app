#!/bin/bash
# Set postgres password explicitly during initialization
# This runs after postgres is ready but before other services connect

echo "Waiting for postgres..."
until PGPASSWORD=iamsoecure psql -h postgres -U postgres -d postgres -c "SELECT 1" > /dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Setting postgres password..."
PGPASSWORD=iamsoecure psql -h postgres -U postgres -d postgres -c "ALTER USER postgres PASSWORD 'iamsoecure';"

echo "Password set successfully!"
