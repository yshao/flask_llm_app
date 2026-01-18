# ============================================================================
# RAILWAY POSTGRESQL DATABASE INITIALIZATION
# ============================================================================
# This script initializes the database after Railway PostgreSQL is ready
# Run this manually or add to app startup for first-time setup
# ============================================================================

import os
import time
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Railway PostgreSQL connection (uses Railway references)
DB_HOST = os.environ.get("DATABASE_HOST", "localhost")
DB_PORT = os.environ.get("DATABASE_PORT", "5432")
DB_NAME = os.environ.get("DATABASE_NAME", "homework_db")
DB_USER = os.environ.get("DATABASE_USER", "postgres")
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD", "changeme")

print("=" * 50)
print("Railway PostgreSQL Initialization")
print("=" * 50)
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"Database: {DB_NAME}")
print(f"User: {DB_USER}")
print("")

# Wait for database to be ready
max_retries = 30
retry_delay = 2

for attempt in range(max_retries):
    try:
        print(f"Connecting to database... (attempt {attempt + 1}/{max_retries})")

        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("✓ Connected successfully!")

        # Check if pgvector is already installed
        cursor.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        )

        if cursor.fetchone():
            print("✓ pgvector extension already installed")
        else:
            # Enable pgvector extension
            print("Enabling pgvector extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("✓ pgvector extension enabled!")

        cursor.close()
        conn.close()

        print("")
        print("=" * 50)
        print("Initialization Complete!")
        print("=" * 50)
        break

    except psycopg2.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"Connection failed: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("")
            print("=" * 50)
            print("ERROR: Failed to connect to database")
            print("=" * 50)
            print(f"\nError: {e}")
            print("\nMake sure Railway PostgreSQL service is running")
            print("and environment variables are set correctly:")
            print("")
            print("DATABASE_HOST=${{Postgres.HOSTNAME}}")
            print("DATABASE_PORT=${{Postgres.PORT}}")
            print("DATABASE_NAME=${{Postgres.DATABASE}}")
            print("DATABASE_USER=${{Postgres.USERNAME}}")
            print("DATABASE_PASSWORD=${{Postgres.PASSWORD}}")
            raise
