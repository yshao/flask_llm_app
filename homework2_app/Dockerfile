FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (add curl and postgresql-client for AWS deployment)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=app
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check for AWS ECS
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with Gunicorn and Gevent for production with WebSocket support
# Added --timeout 120 for long LLM API requests
CMD ["gunicorn", "--worker-class", "gevent.pygevent.GeventWorker", "--workers", "1", "--worker-connections", "1000", "--bind", "0.0.0.0:8080", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]