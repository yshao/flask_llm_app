#!/bin/bash
# ============================================================================
# Docker Deployment Script
# PostgreSQL + Flask App - All in Docker
# ============================================================================

set -e  # Exit on error

echo "=============================================="
echo "  DOCKER DEPLOYMENT"
echo "  Full Stack in Docker Containers"
echo "=============================================="
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# ============================================================================
# Step 1: Environment Check
# ============================================================================
echo "📋 Step 1: Checking environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "  ✗ ERROR: Docker is not installed!"
    echo "    Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "  ✓ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "  ✗ ERROR: Docker Compose is not installed!"
    echo "    Install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "  ✓ Docker Compose is installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "  ✗ ERROR: Docker daemon is not running!"
    echo "    Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi
echo "  ✓ Docker daemon is running"

# Check for .env file
if [ ! -f .env ]; then
    echo "  ✗ ERROR: .env file not found!"
    echo "    Create .env from template: cp .env.example .env"
    echo "    Then edit .env with your configuration."
    exit 1
fi
echo "  ✓ .env file found"
echo ""

# ============================================================================
# Step 2: Clean Up Previous Deployment
# ============================================================================
echo "🧹 Step 2: Cleaning up previous deployment..."
echo "  → Stopping existing containers..."
docker compose down 2>/dev/null || true
echo "  ✓ Cleanup complete"
echo ""

# ============================================================================
# Step 3: Build Docker Images
# ============================================================================
echo "🏗️  Step 3: Building Docker images..."
echo "  → Building Flask application image..."
docker compose --profile docker build --no-cache flask-app
echo "  ✓ Images built successfully"
echo ""

# ============================================================================
# Step 4: Start Services
# ============================================================================
echo "🚀 Step 4: Starting services..."
echo "  → Starting PostgreSQL..."
docker compose up -d postgres

echo "  → Waiting for PostgreSQL to be healthy..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker compose ps postgres | grep -q "healthy"; then
        echo "  ✓ PostgreSQL is healthy"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "  ✗ ERROR: PostgreSQL failed to start"
    docker compose logs postgres
    exit 1
fi

echo "  → Initializing database..."
docker compose up db-init
echo "  ✓ Database initialized"

echo "  → Starting Flask application..."
docker compose --profile docker up -d flask-app
echo "  ✓ Flask application started"
echo ""

# ============================================================================
# Step 5: Wait for Application to be Ready
# ============================================================================
echo "⏳ Step 5: Waiting for application to be ready..."
timeout=30
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "  ✓ Application is responding"
        break
    fi
    if [ $elapsed -eq 0 ]; then
        echo "  → Waiting for Flask app to start..."
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "  ⚠️  Warning: Application may still be starting"
    echo "  → Check logs with: docker compose logs flask-app"
fi
echo ""

# ============================================================================
# Step 6: Display Status
# ============================================================================
echo "=============================================="
echo "  DEPLOYMENT COMPLETE"
echo "=============================================="
echo ""
echo "✅ Services Status:"
docker compose ps
echo ""
echo "📝 Access the application at:"
echo "   http://localhost:8080"
echo ""
echo "📊 Useful Commands:"
echo "   View logs:        docker compose logs -f"
echo "   View Flask logs:  docker compose logs -f flask-app"
echo "   Stop services:    docker compose down"
echo "   Restart:          docker compose restart"
echo "   Rebuild:          docker compose build --no-cache"
echo ""
echo "🛑 To stop all services:"
echo "   docker compose down"
echo ""
echo "🗑️  To stop and remove volumes (clean slate):"
echo "   docker compose down -v"
echo ""
echo "=============================================="
