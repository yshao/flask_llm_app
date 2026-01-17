# Flask LLM Application - Deployment Instructions

Complete guide for deploying the Flask-based AI agent application with multi-expert LLM system, semantic search, and real-time chat capabilities.

---

## Table of Contents

1. [Application Overview](#application-overview)
2. [Prerequisites](#prerequisites)
3. [Local Deployment](#local-deployment)
4. [Docker Deployment](#docker-deployment)
5. [AWS EC2 Deployment (Free Tier)](#aws-ec2-deployment-free-tier)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Development](#development)

---

## Application Overview

### What This Application Does

A sophisticated AI agent system featuring:
- **Multi-Expert AI Agents**: Specialized agents for database queries, content analysis, and web crawling
- **Semantic Search**: Vector-based similarity search using pgvector
- **Real-time Chat**: WebSocket-based chat interface with Socket.IO
- **ReAct Pattern**: AI agents that reason and act systematically
- **Resume Analysis**: AI-powered resume evaluation and benchmarking
- **Web Crawling**: Automated content extraction and embedding generation

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Flask 3.x with Socket.IO |
| **Frontend** | Vue.js 3, Tailwind CSS |
| **Database** | PostgreSQL 16 with pgvector |
| **LLM Providers** | Groq (LLaMA), Google Gemini |
| **Container** | Docker + Docker Compose |
| **Production Server** | Gunicorn with Gevent |

---

## Prerequisites

### Required Software

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **Python**: 3.11+ (for local development)
- **Git**: For cloning repositories

### Required API Keys

| Service | Purpose | How to Get |
|---------|---------|------------|
| **Groq** | Main LLM (LLaMA 3.3) | https://console.groq.com/keys |
| **Gemini** | Embeddings | https://makersuite.google.com/app/apikey |

### Hardware Requirements

- **Local**: 4GB RAM minimum, 8GB recommended
- **EC2 Free Tier**: t2.micro (1GB RAM) - functional but may be slow
- **EC2 Recommended**: t2.small (2GB RAM) or t2.medium (4GB RAM)

---

## Local Deployment

### Option 1: Docker Compose (Recommended)

#### Step 1: Clone and Navigate
```bash
cd homework2_app
```

#### Step 2: Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required settings in `.env`:
```bash
# API Keys (REQUIRED)
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Database (can use defaults for local)
DATABASE_NAME=homework_db
DATABASE_USER=postgres
DATABASE_PASSWORD=changeme
DATABASE_HOST=postgres
DATABASE_PORT=5432

# Flask Security
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_REVERSIBLE_KEY=$(openssl rand -hex 32)
```

#### Step 3: Start Services
```bash
# Start PostgreSQL and Flask app
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

#### Step 4: Access Application
```
URL: http://localhost:8080
```

#### Step 5: Stop Services
```bash
docker-compose down

# To remove database data
docker-compose down -v
```

### Option 2: Native Python (Development)

#### Step 1: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt
```

#### Step 2: Start PostgreSQL
```bash
# Using Docker
docker run -d \
  --name homework-postgres \
  -e POSTGRES_DB=homework_db \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Wait for database to be ready
docker logs -f homework-postgres
```

#### Step 3: Set Environment Variables
```bash
export DATABASE_HOST=localhost
export DATABASE_NAME=homework_db
export DATABASE_USER=postgres
export DATABASE_PASSWORD=changeme
export GROQ_API_KEY=gsk_your_key
export GEMINI_API_KEY=your_key
export SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_REVERSIBLE_KEY=$(openssl rand -hex 32)
```

#### Step 4: Run Application
```bash
cd flask_app
python -m app
```

Access at: `http://localhost:8080`

---

## Docker Deployment

### Full Containerization

The `docker_deploy.sh` script automates full Docker deployment:

```bash
# Deploy everything in Docker
./docker_deploy.sh

# Or with options
./docker_deploy.sh --rebuild --clean
```

### Manual Docker Steps

#### 1. Build Flask Image
```bash
docker build -t flask-llm-app:latest .
```

#### 2. Start Database
```bash
docker run -d \
  --name homework-postgres \
  -e POSTGRES_DB=homework_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=secure_password \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

#### 3. Run Flask App
```bash
docker run -d \
  --name homework-flask \
  --link homework-postgres:postgres \
  -p 8080:8080 \
  -e DATABASE_HOST=postgres \
  -e DATABASE_NAME=homework_db \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=secure_password \
  -e GROQ_API_KEY=gsk_your_key \
  -e GEMINI_API_KEY=your_key \
  flask-llm-app:latest
```

---

## AWS EC2 Deployment (Free Tier)

Deploy to AWS cloud completely within free tier limits ($0/month).

### Quick Deploy Method

#### Step 1: Push Docker Image
```bash
# Login to Docker Hub
docker login

# Build and tag
docker build -t flask-llm-app:latest .
docker tag flask-llm-app:latest your-username/flask-llm-app:latest

# Push
docker push your-username/flask-llm-app:latest
```

#### Step 2: Edit Deployment Script
```bash
nano deploy-ec2-quick.sh
```

Set these variables:
```bash
DOCKERHUB_USERNAME="your-dockerhub-username"
GROQ_API_KEY="gsk_your_actual_api_key"
GEMINI_API_KEY="your_actual_gemini_key"
DB_PASSWORD="secure_password_here"
```

#### Step 3: Deploy
```bash
chmod +x deploy-ec2-quick.sh
./deploy-ec2-quick.sh
```

#### Step 4: Access Application
The script will output:
```
Instance ID: i-xxxxxxxx
Public IP: xx.xx.xx.xx
URL: http://xx.xx.xx.xx
```

Wait 3-5 minutes for Docker setup, then access at the provided URL.

### Interactive Deploy Method

```bash
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

Follow the prompts to enter API keys and configuration.

### Managing EC2 Deployment

#### SSH Into Instance
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
```

#### Check Container Status
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'docker ps'
```

#### View Logs
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'docker logs flask-app'
```

#### Update Application
```bash
# Build and push new version
docker build -t flask-llm-app:v2 .
docker push your-username/flask-llm-app:latest

# Pull and restart on EC2
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
cd /home/ec2-user/flask-app
docker-compose pull
docker-compose up -d
```

#### Stop/Start Instance
```bash
# Stop (save free tier hours)
aws ec2 stop-instances --instance-ids <INSTANCE_ID>

# Start
aws ec2 start-instances --instance-ids <INSTANCE_ID>
```

### EC2 Cost Management

**Free Tier Limits:**
- EC2 t2.micro: 750 hours/month × 12 months
- After free tier: ~$8-10/month
- Data transfer: 100 GB/month free

**Monitor Usage:**
```bash
# Check running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# Set billing alert in AWS Console → Billing → Budgets
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | None | Groq API key for LLM |
| `GEMINI_API_KEY` | ✅ Yes | None | Gemini API key for embeddings |
| `DATABASE_NAME` | No | homework_db | PostgreSQL database name |
| `DATABASE_HOST` | No | postgres | Database host |
| `DATABASE_USER` | No | postgres | Database user |
| `DATABASE_PASSWORD` | No | changeme | Database password |
| `DATABASE_PORT` | No | 5432 | Database port |
| `SECRET_KEY` | No | auto-generated | Flask session encryption |
| `ENCRYPTION_REVERSIBLE_KEY` | No | auto-generated | Password encryption |
| `GROQ_MODEL` | No | llama-3.3-70b-versatile | Groq model to use |

### Database Initialization

The database automatically initializes on first run:
1. Creates tables with pgvector extension
2. Imports sample resume data (institutions, positions, experiences, skills)
3. Configures LLM roles for multi-expert system
4. Generates vector embeddings for semantic search

### Initial Data

Located in `flask_app/database/initial_data/`:
- `institutions.csv`: Academic institutions
- `positions.csv`: Job positions and titles
- `experiences.csv`: Sample work experiences
- `skills.csv`: Technical and soft skills

---

## Troubleshooting

### Common Issues

#### 1. "API Key Not Found" Error

**Problem:** Application fails to start with missing API key error.

**Solution:**
```bash
# Check .env file exists
cat .env

# Verify API keys are set
grep GROQ_API_KEY .env
grep GEMINI_API_KEY .env

# Restart application
docker-compose restart flask-app
```

#### 2. Database Connection Failed

**Problem:** Flask app cannot connect to PostgreSQL.

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs homework-postgres

# Verify database is ready
docker exec homework-postgres pg_isready -U postgres

# Restart services
docker-compose restart
```

#### 3. "Out of Memory" on EC2 t2.micro

**Problem:** Application crashes or runs very slowly on 1GB RAM instance.

**Solution:**
```bash
# Upgrade to t2.small (2GB RAM, ~$15/month)
aws ec2 modify-instance-attribute \
  --instance-id <INSTANCE_ID> \
  --instance-type "{\"Value\": \"t2.small\"}"

# Or stop when not using
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
```

#### 4. WebSocket Connection Fails

**Problem:** Chat interface not connecting or messages not sending.

**Solution:**
```bash
# Check if using correct URL (not HTTPS)
# WebSocket requires HTTP or WSS protocol

# Check nginx configuration on EC2
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
cat /etc/nginx/conf.d/flask-app.conf

# Restart nginx
systemctl restart nginx
```

#### 5. Vector Search Not Working

**Problem:** Semantic search returns no results.

**Solution:**
```bash
# Connect to database
docker exec -it homework-postgres psql -U postgres -d homework_db

# Check pgvector extension
SELECT extname FROM pg_extension WHERE extname = 'vector';

# Check for vector columns
\d documents

# Manually enable extension if needed
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 6. Docker Build Fails

**Problem:** Docker build fails with dependency errors.

**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t flask-llm-app:latest .

# Check for specific package errors
docker build -t flask-llm-app:debug . 2>&1 | tee build.log
```

### Health Checks

#### Local Deployment
```bash
# Check health endpoint
curl http://localhost:8080/health

# Expected response
{
  "status": "healthy",
  "flask_app": "running",
  "database": "connected"
}
```

#### Docker Deployment
```bash
# Check container health
docker ps

# Check logs
docker logs homework-flask
docker logs homework-postgres

# Run health check
docker exec homework-flask curl -f http://localhost:8080/health
```

#### EC2 Deployment
```bash
# SSH into instance
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>

# Check services
docker ps
docker logs flask-app
docker logs flask-postgres

# Check nginx
systemctl status nginx
curl http://localhost/health
```

### Debug Mode

Enable debug logging:

```bash
# In .env
FLASK_DEBUG=true
FLASK_ENV=development

# Restart application
docker-compose restart flask-app

# View logs
docker logs -f flask-app
```

---

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_llm.py

# Run with coverage
python -m pytest --cov=flask_app tests/
```

### Database Management

```bash
# Access database shell
docker exec -it homework-postgres psql -U postgres -d homework_db

# Backup database
docker exec homework-postgres pg_dump -U postgres homework_db > backup.sql

# Restore database
docker exec -i homework-postgres psql -U postgres homework_db < backup.sql

# Reset database (WARNING: deletes all data)
docker exec homework-postgres psql -U postgres -c "DROP DATABASE homework_db;"
docker exec homework-postgres psql -U postgres -c "CREATE DATABASE homework_db;"
```

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild Docker image
docker build -t flask-llm-app:latest .

# Restart with new image
docker-compose up -d --force-recreate
```

### Adding New Features

1. **Add new route** in `flask_app/routes.py`
2. **Add new utility** in `flask_app/utils/`
3. **Update database schema** in `flask_app/database/create_tables/`
4. **Rebuild and restart**

---

## Performance Tuning

### For t2.micro (1GB RAM)

Edit `docker-compose.yml`:
```yaml
services:
  flask-app:
    deploy:
      resources:
        limits:
          memory: 512M
  postgres:
    deploy:
      resources:
        limits:
          memory: 256M
```

### For t2.small (2GB RAM)

```yaml
services:
  flask-app:
    deploy:
      resources:
        limits:
          memory: 1024M
  postgres:
    deploy:
      resources:
        limits:
          memory: 512M
```

### Database Performance

```sql
-- Add indexes for common queries
CREATE INDEX idx_documents_title ON documents(title);
CREATE INDEX idx_documents_content ON documents USING gin(to_tsvector('english', content));

-- Vacuum and analyze
VACUUM ANALYZE;
```

---

## Security Best Practices

1. **Never commit .env file** to version control
2. **Use strong passwords** for production database
3. **Enable HTTPS** for production (see EC2_DEPLOYMENT.md)
4. **Rotate API keys** regularly
5. **Use AWS Secrets Manager** for production deployments
6. **Enable firewall rules** to restrict access
7. **Keep dependencies updated** regularly

---

## Support and Resources

### Documentation Files

- `README_EC2.md` - Quick EC2 deployment guide
- `EC2_DEPLOYMENT.md` - Comprehensive AWS documentation
- `QUICKSTART.md` - Quick start guide
- `.env.example` - Environment variable template

### Getting Help

1. Check logs: `docker logs flask-app`
2. Health check: `curl http://localhost:8080/health`
3. Database status: `docker exec homework-postgres pg_isready`

### Useful Links

- [Groq Documentation](https://console.groq.com/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Socket.IO Documentation](https://socket.io/docs/)

---

## Summary

### Quick Deployment Options

| Method | Time | Cost | Complexity |
|--------|------|------|------------|
| **Local Docker** | 5 min | Free | ⭐ Simple |
| **EC2 Free Tier** | 10 min | $0/mo | ⭐⭐ Medium |
| **EC2 Production** | 15 min | $15-50/mo | ⭐⭐ Medium |

### What You Get

✅ Multi-expert AI agent system
✅ Semantic search with vector embeddings
✅ Real-time chat with WebSocket support
✅ Resume analysis and benchmarking
✅ Web crawling and content extraction
✅ Production-ready Docker deployment
✅ Free-tier cloud deployment option

---

**Last Updated:** 2025-01-05
**Application Version:** 1.0.0
