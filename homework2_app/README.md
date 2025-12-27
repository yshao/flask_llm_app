# Homework 1: Multi-Expert AI Agent System

A sophisticated AI chat application with multi-expert orchestration, real-time Socket.IO communication, and PostgreSQL database integration.

## Quick Start

Choose your deployment method:

### Option 1: Docker (Recommended for Production)
```bash
docker-compose up --build
# Access: http://localhost:8080
```

### Option 2: Local Flask (Recommended for Development)
```bash
# Linux/macOS
./run_local.sh

# Windows
run_local.bat

# Access: http://127.0.0.1:8080
```

---

## Features

### Multi-Expert AI System
- **Orchestrator AI**: Analyzes requests and coordinates expert agents
- **Database Read Expert**: Generates SQL queries for data retrieval
- **Database Write Expert**: Creates Python code for database modifications
- **Content Expert**: Analyzes current page content and provides contextual responses

### Real-Time Communication
- Socket.IO for bidirectional chat
- Automatic resume data reload after database changes
- Live typing indicators and status updates

### Database Integration
- PostgreSQL with structured resume data
- Automatic schema creation and data import
- Support for institutions, positions, experiences, and skills

### Modern Frontend
- Vue.js 3 (Composition API via CDN)
- Tailwind CSS for responsive design
- Real-time chat interface with message history

---

## Architecture

```
+---------------------------------------------------------+
|                     User Browser                        |
|  +-------------+  +-------------+  +-------------+      |
|  |   Home Page |  | Resume Page |  |  Chat Panel |      |
|  +-------------+  +-------------+  +-------------+      |
+-----------------------+---------------------------------+
                        | HTTP / WebSocket
+-----------------------+---------------------------------+
|                   Flask Backend                         |
|  +--------------------------------------------------+   |
|  |              Orchestrator AI                      |   |
|  |  +--------+  +--------+  +--------+             |   |
|  |  |DB Read |  |DB Write|  |Content |             |   |
|  |  | Expert |  | Expert |  | Expert |             |   |
|  |  +--------+  +--------+  +--------+             |   |
|  +--------------------------------------------------+   |
|  +--------------------------------------------------+   |
|  |           Google Gemini API                      |   |
|  +--------------------------------------------------+   |
+-----------------------+---------------------------------+
                        | SQL
+-----------------------+---------------------------------+
|                  PostgreSQL Database                    |
|  institutions | positions | experiences | skills        |
|  users | llm_roles | benchmark_test_cases              |
+---------------------------------------------------------+
```

---

## Project Structure

```
homework1_app/
+-- Configuration Files
|   +-- .env.local              # Local deployment template
|   +-- .env                    # Active environment config (create from .env.local)
|   +-- docker-compose.yml      # Docker orchestration
|   +-- Dockerfile              # Flask container definition
|   +-- requirements.txt        # Python dependencies
|
+-- Deployment Scripts
|   +-- run_local.sh           # Local deployment (Linux/macOS)
|   +-- run_local.bat          # Local deployment (Windows)
|   +-- init-db.sh             # Database initialization (Docker)
|
+-- Documentation
|   +-- README.md              # This file
|
+-- Application Code
|   +-- app.py                 # Entry point
|   +-- flask_app/
|       +-- __init__.py        # App factory with database init
|       +-- config.py          # Configuration management
|       +-- routes.py          # HTTP endpoints and chat logic
|       |
|       +-- database/          # Database schemas and data
|       |   +-- create_tables/ # SQL table definitions
|       |   +-- initial_data/  # CSV seed data
|       |
|       +-- utils/             # Core utilities
|       |   +-- database.py    # PostgreSQL wrapper
|       |   +-- llm.py         # Gemini API client & orchestrator
|       |   +-- socket_events.py  # Socket.IO handlers
|       |   +-- a2a_protocol.py   # Agent-to-agent protocol
|       |   +-- evaluation_agent.py  # Benchmark testing
|       |
|       +-- templates/         # HTML templates
|       +-- static/            # Frontend assets
|           +-- js/            # JavaScript components
|           +-- css/           # Stylesheets
|           +-- images/        # Images
|
+-- venv/                      # Python virtual environment (created by script)
```

---

## Technology Stack

### Backend
- **Flask 3.x** - Web framework
- **Flask-SocketIO** - Real-time bidirectional communication
- **PostgreSQL 15** - Relational database
- **psycopg2** - PostgreSQL adapter
- **Google Gemini API** - LLM integration
- **python-dotenv** - Environment management
- **BeautifulSoup4** - HTML parsing
- **Flask-Failsafe** - Error handling with stack traces

### Frontend
- **Vue.js 3** - Progressive JavaScript framework (CDN)
- **Socket.IO Client** - WebSocket client
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript** - ES6+ features

### DevOps
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - WSGI HTTP server
- **Eventlet** - Concurrent networking library

---

## Key Concepts

### Master Prompt Template System
Each AI expert has a structured prompt template stored in the database:

```python
MASTER_PROMPT_TEMPLATE = """
You are a {{role}} with expertise in {{domain}}.

Instructions:
{{specific_instructions}}

Context:
{{background_context}}

Examples:
{{few_shot_examples}}

Request:
{{request}}
"""
```

### Orchestrator Pattern
1. User sends message
2. Orchestrator analyzes request
3. Generates list of expert function calls
4. Executes each expert sequentially
5. Synthesizes final response
6. Emits to Socket.IO for real-time display

### Database Abstraction
Single `query()` method handles all operations:
```python
# Read operations
results = db.query("SELECT * FROM users")

# Write operations with parameters
db.query("INSERT INTO skills VALUES (%s, %s)", [name, level])

# Specialized methods
resume_data = db.getResumeData()
roles = db.getLLMRoles()
```

---

## Testing

### Manual Testing
1. Navigate to http://localhost:8080
2. Test AI chat with various queries:
   - "What skills does he have?" (Database Read)
   - "Add Python to first experience" (Database Write)
   - "Summarize this page" (Content Expert)
3. Verify resume page loads correctly
4. Check login/logout functionality

### Benchmark Testing
```python
# Database includes benchmark test cases
SELECT * FROM benchmark_test_cases;

# Test categories:
# - chat_functionality
# - resume_query
# - page_context
```

---

## Common Issues

### Docker Deployment

**Port conflicts**:
```bash
# Change in .env
POSTGRES_PORT=5433
FLASK_PORT=8081
```

**Containers won't stop**:
```bash
docker rm -f homework1-postgres homework1-flask-app
```

### Local Flask Deployment

**PostgreSQL not running**:
```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql@15
```

**Database connection refused**:
```bash
# Check PostgreSQL status
pg_isready

# Verify credentials in .env match PostgreSQL setup
```

**Module not found**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Security Notes

### Development Environment
- Default credentials are **for development only**
- `.env` files are **gitignored** (never commit API keys)
- Encryption keys should be **rotated for production**

### Production Deployment
- Use strong SECRET_KEY
- Enable HTTPS
- Use environment variables (not .env files)
- Restrict database access
- Implement rate limiting
- Enable CORS selectively
- Review and update dependencies regularly

---

## Contributing

This is a homework assignment project. For educational purposes:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit for review

---

## License

Educational project for CSE 491/895 - AI Agents course at Michigan State University.

---

## Author

**Prof. Mohammad M. Ghassemi**
- Course: CSE 491/895 - A Hands-on Introduction to AI Agents
- Institution: Michigan State University
- Email: ghassem3@msu.edu

---

## Acknowledgments

- Google Gemini API for LLM capabilities
- Flask and Flask-SocketIO communities
- Vue.js and Tailwind CSS teams
- PostgreSQL project
- MSU Computer Science Department
