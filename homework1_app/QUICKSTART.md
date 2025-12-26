# Quick Start Guide

Get your development environment running in 3 simple steps!

## Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ installed

## Step 1: Start PostgreSQL in Docker

```bash
# Start PostgreSQL with pgvector extension
docker-compose -f docker-compose-local.yml up -d
```

This will:
- Start PostgreSQL on port 5432
- Enable pgvector extension
- Create the database

## Step 2: Initialize Database Tables

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create tables and import data
python init_local_db.py
```

## Step 3: Run Flask Application

```bash
# Start the Flask development server
python app.py
```

Access the application at: **http://127.0.0.1:8080**

---

## Verify Setup

Check that everything is working:

```bash
# Check Docker containers
docker ps

# Check database tables
docker exec flask_llm_postgres psql -U postgres -d db -c "\dt"

# Check pgvector extension
docker exec flask_llm_postgres psql -U postgres -d db -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

## Common Commands

```bash
# Stop containers
docker-compose -f docker-compose-local.yml down

# Restart containers
docker-compose -f docker-compose-local.yml restart

# Reinitialize database
python init_local_db.py --purge

# View PostgreSQL logs
docker logs flask_llm_postgres
```

## Troubleshooting

**Port 5432 already in use?**
```bash
# Check what's using port 5432
sudo lsof -i :5432

# Stop local PostgreSQL
sudo systemctl stop postgresql
```

**Can't connect to database?**
```bash
# Verify containers are running
docker ps

# Check PostgreSQL is accepting connections
docker exec flask_llm_postgres pg_isready -U postgres -d db
```

For detailed setup instructions, see [LOCAL_SETUP.md](./LOCAL_SETUP.md)
