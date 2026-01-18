FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including build essentials
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libev-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies - cache busting with comment
# Updated 2025-01-18: Fixed gevent package name
COPY requirements.txt .
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=app
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Health check (works with Railway, AWS ECS, etc.)
# Uses PORT environment variable, defaults to 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run with Gunicorn and Gevent for production with WebSocket support
# --timeout 120 for long LLM API requests
# Uses PORT environment variable (Railway injects this automatically)
# Updated 2025-01-18: Using standard gevent worker
CMD sh -c "gunicorn \
    --worker-class gevent \
    --workers 1 \
    --worker-connections 1000 \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --worker-tmp-dir /dev/shm \
    app:app"