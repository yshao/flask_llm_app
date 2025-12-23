#!/bin/bash
# ============================================================================
# LOCAL FLASK DEPLOYMENT SCRIPT
# ============================================================================
# This script sets up and runs the Flask application natively (without Docker)
# Author: AI Assistant
# ============================================================================

set -e  # Exit on error

echo "=================================================="
echo "  Homework 1 - Local Flask Deployment"
echo "=================================================="
echo ""

# ============================================================================
# STEP 1: Environment Setup
# ============================================================================
echo "[1/6] Checking environment setup..."

# Check if .env exists, if not copy from .env.local
if [ ! -f .env ]; then
    if [ -f .env.local ]; then
        echo "  → Copying .env.local to .env"
        cp .env.local .env
    else
        echo "  ✗ ERROR: No .env or .env.local file found!"
        echo "    Create .env.local with your configuration first."
        exit 1
    fi
else
    echo "  ✓ .env file found"
fi

# ============================================================================
# STEP 2: Python Environment
# ============================================================================
echo ""
echo "[2/6] Checking Python environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "  → Creating virtual environment..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
else
    echo "  ✓ Virtual environment exists"
fi

# Activate virtual environment
echo "  → Activating virtual environment..."
source venv/bin/activate

# ============================================================================
# STEP 3: Install Dependencies
# ============================================================================
echo ""
echo "[3/6] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✓ Dependencies installed"

# ============================================================================
# STEP 4: PostgreSQL Check
# ============================================================================
echo ""
echo "[4/6] Checking PostgreSQL..."

# Check if PostgreSQL is running
if ! command -v psql &> /dev/null; then
    echo "  ✗ ERROR: PostgreSQL is not installed!"
    echo ""
    echo "  Install PostgreSQL:"
    echo "    - Ubuntu/Debian: sudo apt install postgresql"
    echo "    - macOS: brew install postgresql"
    echo "    - Windows: Download from https://www.postgresql.org/download/"
    exit 1
fi

# Try to connect to PostgreSQL
if ! pg_isready -q; then
    echo "  ✗ WARNING: PostgreSQL service may not be running"
    echo ""
    echo "  Start PostgreSQL:"
    echo "    - Ubuntu/Debian: sudo systemctl start postgresql"
    echo "    - macOS: brew services start postgresql"
    echo "    - Windows: Start from Services or pg_ctl start"
    echo ""
    read -p "  Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "  ✓ PostgreSQL is running"
fi

# ============================================================================
# STEP 5: Database Setup
# ============================================================================
echo ""
echo "[5/6] Setting up database..."

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check if database exists, create if not
if ! psql -U ${DATABASE_USER:-postgres} -lqt | cut -d \| -f 1 | grep -qw ${DATABASE_NAME:-homework1_local}; then
    echo "  → Creating database: ${DATABASE_NAME:-homework1_local}"
    createdb -U ${DATABASE_USER:-postgres} ${DATABASE_NAME:-homework1_local} 2>/dev/null || {
        echo "  [INFO] Database creation may require sudo access or different credentials"
        echo "    Run manually: createdb -U postgres ${DATABASE_NAME:-homework1_local}"
    }
    echo "  ✓ Database created"
else
    echo "  ✓ Database exists: ${DATABASE_NAME:-homework1_local}"
fi

# ============================================================================
# STEP 6: Start Flask Application
# ============================================================================
echo ""
echo "[6/6] Starting Flask application..."
echo ""
echo "=================================================="
echo "  Application starting on http://${FLASK_HOST:-127.0.0.1}:${FLASK_PORT:-8080}"
echo "=================================================="
echo ""
echo "  Press Ctrl+C to stop the server"
echo ""

# Run Flask with hot reload enabled
python app.py
