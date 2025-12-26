# Local Development Setup Guide

This guide explains how to run PostgreSQL in Docker and the Flask application locally for development.

## Architecture

- **PostgreSQL**: Running in Docker container with pgvector extension
- **Flask App**: Running natively on your local machine
- **Benefits**: Fast Flask development with auto-reload, easy debugging, persistent database

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Python 3.8+** installed
3. **pip** package manager

## Quick Start

### 1. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The `.env` file is already configured for local development with PostgreSQL in Docker. Verify the settings:

```bash
cat .env
```

Key settings for local development:
- `DATABASE_HOST=localhost` (PostgreSQL runs in Docker but is accessible via localhost)
- `DATABASE_PORT=5432` (Exposed from Docker container)
- `DATABASE_NAME=db`
- `DATABASE_USER=postgres`
- `DATABASE_PASSWORD=iamsosecure`
- `FLASK_HOST=127.0.0.1`
- `FLASK_PORT=8080`

**Important**: Make sure to set your own `GEMINI_API_KEY` in the `.env` file.

### 3. Start PostgreSQL in Docker

```bash
# Start PostgreSQL and initialize database
docker-compose -f docker-compose-local.yml up -d

# Check container status
docker ps
```

You should see two containers:
- `flask_llm_postgres` - PostgreSQL database server
- `flask_llm_db_init` - Database initialization (will exit after completion)

### 4. Initialize Database Tables

```bash
# Run the database initialization script
python init_local_db.py

# To drop existing tables and recreate (use with caution):
python init_local_db.py --purge
```

This script will:
- Wait for PostgreSQL to be ready
- Create all database tables
- Import initial data from CSV files
- Enable pgvector extension

### 5. Run Flask Application

```bash
# Start the Flask development server
python app.py
```

The application will be available at: http://127.0.0.1:8080

## Development Workflow

### Starting Your Development Session

```bash
# 1. Start Docker containers (if not already running)
docker-compose -f docker-compose-local.yml up -d

# 2. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# 3. Start Flask app
python app.py
```

### Stopping Your Development Session

```bash
# 1. Stop Flask app (Ctrl+C in the terminal)

# 2. Stop Docker containers (optional - can keep running)
docker-compose -f docker-compose-local.yml down

# 3. Deactivate virtual environment
deactivate
```

## Database Management

### Accessing PostgreSQL

```bash
# Connect to PostgreSQL using psql
docker exec -it flask_llm_postgres psql -U postgres -d db

# Or from your local machine (if you have psql installed)
psql -h localhost -p 5432 -U postgres -d db
# Password: iamsosecure
```

### Resetting Database

```bash
# Option 1: Reinitialize with purge flag
python init_local_db.py --purge

# Option 2: Destroy and recreate containers
docker-compose -f docker-compose-local.yml down -v
docker-compose -f docker-compose-local.yml up -d
python init_local_db.py
```

### Viewing Logs

```bash
# PostgreSQL logs
docker logs flask_llm_postgres

# Database initialization logs
docker logs flask_llm_db_init

# Flask logs (in terminal where app.py is running)
```

## Troubleshooting

### Port 5432 Already in Use

If you have PostgreSQL installed locally and running on port 5432:

**Option 1**: Stop local PostgreSQL
```bash
# Linux/Mac
sudo systemctl stop postgresql

# Mac with Homebrew
brew services stop postgresql
```

**Option 2**: Change Docker port mapping in `.env`
```bash
POSTGRES_PORT=5433  # Use different port
DATABASE_PORT=5433  # Update Flask connection port
```

Then update `docker-compose-local.yml`:
```yaml
ports:
  - "5433:5432"
```

### Database Connection Errors

```bash
# Check if containers are running
docker ps

# Check PostgreSQL health
docker exec -it flask_llm_postgres pg_isready -U postgres -d db

# Restart containers
docker-compose -f docker-compose-local.yml restart
```

### Flask Can't Import Modules

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Denied on Scripts

```bash
# Make scripts executable
chmod +x init_local_db.py
chmod +x init-db.sh
```

## Project Structure

```
homework1_app/
├── .env                      # Environment configuration
├── docker-compose-local.yml  # Docker config for PostgreSQL only
├── init-db.sh               # Shell script for pgvector setup
├── init_local_db.py         # Python script for table creation
├── app.py                   # Flask application entry point
├── requirements.txt         # Python dependencies
├── flask_app/
│   ├── __init__.py         # Flask app factory
│   ├── routes.py           # Application routes
│   ├── config.py           # Configuration management
│   ├── utils/
│   │   ├── database.py     # Database operations
│   │   ├── llm.py          # LLM integration
│   │   └── embeddings.py   # Vector embeddings
│   └── database/
│       ├── create_tables/  # SQL table schemas
│       └── initial_data/   # CSV data files
└── venv/                   # Virtual environment
```

## Tips for Development

1. **Auto-reload**: Flask runs with `debug=True` and `use_reloader=True`, so code changes are automatically detected.

2. **Database Persistence**: Data persists in Docker volume even when containers stop. Use `docker-compose down -v` to remove volumes.

3. **VS Code Integration**:
   - Use Python extension for debugging
   - Set interpreter to `./venv/bin/python`
   - Use integrated terminal for Flask app

4. **Environment Variables**: Changes to `.env` require restarting Flask app but not Docker containers.

5. **Testing**: You can run tests while Flask is running since they connect to the same database.

## Switching to Full Docker Deployment

To run both PostgreSQL and Flask in Docker:

```bash
# Stop local Flask app (Ctrl+C)

# Stop local PostgreSQL containers
docker-compose -f docker-compose-local.yml down

# Start full Docker deployment
docker-compose up -d
```

## Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector
- Docker Compose: https://docs.docker.com/compose/
