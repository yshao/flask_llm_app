#!/bin/bash
# ============================================================================
# Development Deployment Script
# PostgreSQL in Docker + Flask running locally
# ============================================================================

set -e  # Exit on error

echo "=============================================="
echo "  DEVELOPMENT DEPLOYMENT"
echo "  PostgreSQL (Docker) + Flask (Local)"
echo "=============================================="
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# ============================================================================
# Step 1: Environment Check
# ============================================================================
echo "📋 Step 1: Checking environment..."
if [ ! -f .env ]; then
    echo "  ✗ ERROR: .env file not found!"
    echo "    Please create .env file with required configuration"
    echo "    You can copy from .env.example: cp .env.example .env"
    exit 1
fi
echo "  ✓ .env file found"
echo ""

# ============================================================================
# Step 2: Start PostgreSQL in Docker
# ============================================================================
echo "🐘 Step 2: Starting PostgreSQL in Docker..."
docker compose up -d postgres db-init
echo "  ✓ PostgreSQL containers started"
echo ""

# ============================================================================
# Step 3: Wait for Database Initialization
# ============================================================================
echo "⏳ Step 3: Waiting for database initialization..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker compose logs db-init 2>/dev/null | grep -q "pgvector extension enabled"; then
        echo "  ✓ Database initialization complete!"
        break
    fi
    if [ $elapsed -eq 0 ]; then
        echo "  → Waiting for db-init to complete..."
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "  ⚠️  Warning: Database initialization timeout"
    echo "  → Checking logs:"
    docker compose logs db-init
fi
echo ""

# ============================================================================
# Step 4: Install Python Dependencies
# ============================================================================
echo "📦 Step 4: Installing Python dependencies..."
if [ ! -d "venv" ]; then
    echo "  → Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✓ Dependencies installed"
echo ""

# ============================================================================
# Step 5: Start Flask Application
# ============================================================================
echo "🚀 Step 5: Starting Flask application..."
echo ""
echo "=============================================="
echo "  APPLICATION READY"
echo "=============================================="
echo ""
echo "📝 Access at: http://localhost:8080"
echo "🛑 Stop: Press Ctrl+C"
echo ""
echo "=============================================="
echo ""

# Start Flask with development server
# Use the venv's python explicitly to ensure correct environment
venv/bin/python app.py
