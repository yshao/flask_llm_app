#!/usr/bin/env python3
"""
Database initialization script for local development.
Initializes PostgreSQL database running in Docker with tables and initial data.

Usage:
    python init_local_db.py [--purge]

Options:
    --purge    Drop existing tables before creating new ones (default: False)
"""

import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

def wait_for_postgres(host, port, user, password, database, max_retries=30, retry_delay=2):
    """Wait for PostgreSQL to be ready."""
    print(f"Waiting for PostgreSQL at {host}:{port}...")

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: PostgreSQL not ready yet - {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("Failed to connect to PostgreSQL after all retries")
                return False

    return False

def initialize_database(purge=False):
    """Initialize database tables and data."""
    from flask import Flask
    from flask_app.utils.database import database

    # Create minimal Flask app for context
    app = Flask(__name__)

    # Load configuration from environment variables
    app.config['DATABASE_NAME'] = os.getenv('DATABASE_NAME')
    app.config['DATABASE_HOST'] = os.getenv('DATABASE_HOST')
    app.config['DATABASE_USER'] = os.getenv('DATABASE_USER')
    app.config['DATABASE_PORT'] = os.getenv('DATABASE_PORT')
    app.config['DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
    app.config['ENCRYPTION_ONEWAY_SALT'] = os.getenv('ENCRYPTION_ONEWAY_SALT')
    app.config['ENCRYPTION_ONEWAY_N'] = int(os.getenv('ENCRYPTION_ONEWAY_N', 32))
    app.config['ENCRYPTION_ONEWAY_R'] = int(os.getenv('ENCRYPTION_ONEWAY_R', 9))
    app.config['ENCRYPTION_ONEWAY_P'] = int(os.getenv('ENCRYPTION_ONEWAY_P', 1))
    app.config['ENCRYPTION_REVERSIBLE_KEY'] = os.getenv('ENCRYPTION_REVERSIBLE_KEY')

    # Initialize database within app context
    with app.app_context():
        db = database()
        print("\nInitializing database tables...")
        db.createTables(purge=purge)
        print("\n✅ Database initialization complete!")
        print("\nDatabase is ready for local Flask development.")
        print("Run the Flask app with: python app.py")

def main():
    """Main entry point."""
    # Parse command line arguments
    purge = '--purge' in sys.argv

    # Load environment variables from .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_file):
        print(f"❌ Error: .env file not found at {env_file}")
        print("Please create a .env file with your database configuration.")
        sys.exit(1)

    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}\n")

    # Get database configuration
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = int(os.getenv('DATABASE_PORT', 5432))
    db_user = os.getenv('DATABASE_USER', 'postgres')
    db_password = os.getenv('DATABASE_PASSWORD', 'postgres')
    db_name = os.getenv('DATABASE_NAME', 'db')

    print("Database Configuration:")
    print(f"  Host: {db_host}")
    print(f"  Port: {db_port}")
    print(f"  User: {db_user}")
    print(f"  Database: {db_name}")
    print(f"  Purge existing tables: {purge}\n")

    # Wait for PostgreSQL to be ready
    if not wait_for_postgres(db_host, db_port, db_user, db_password, db_name):
        print("\n❌ Failed to connect to PostgreSQL.")
        print("Make sure Docker containers are running:")
        print("  docker-compose -f docker-compose-local.yml up -d")
        sys.exit(1)

    # Initialize database
    try:
        initialize_database(purge=purge)
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
