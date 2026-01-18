# Railway Deployment with Managed PostgreSQL

Complete guide for deploying the Flask LLM App on Railway with managed PostgreSQL service.

---

## Overview

Railway provides managed PostgreSQL with pgvector support. This guide shows how to:

1. Add PostgreSQL service to your Railway project
2. Configure environment variables for database connection
3. Initialize the database with pgvector extension
4. Deploy the Flask application

---

## Step 1: Create Railway Project (if not already created)

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your `flask_llm_app` repository
5. Railway will create a service for your Flask app

---

## Step 2: Add PostgreSQL Service

1. In your Railway project, click **"New Service"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will create a PostgreSQL database with pgvector support

Railway will automatically assign a service name (typically `Postgres`).

---

## Step 3: Configure Flask Service Environment Variables

1. Click on your Flask service (not the Postgres service)
2. Go to **"Variables"** tab
3. Add the following variables:

### Database Variables (Use Railway References)

```
DATABASE_HOST=${{Postgres.HOSTNAME}}
DATABASE_PORT=${{Postgres.PORT}}
DATABASE_NAME=${{Postgres.DATABASE}}
DATABASE_USER=${{Postgres.USERNAME}}
DATABASE_PASSWORD=${{Postgres.PASSWORD}}
```

**Important**: Use the exact syntax `${{Postgres.VARIABLE}}`. Railway will replace these with actual values at runtime.

### Flask Configuration

```
FLASK_ENV=production
SECRET_KEY=your_generated_secret_key_here
PORT=8080
```

### Encryption Keys (Generate Secure Values)

```
ENCRYPTION_ONEWAY_SALT=your_generated_salt_here
ENCRYPTION_REVERSIBLE_KEY=your_generated_key_here
```

### API Keys

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## Step 4: Generate Secure Keys

Run this Python script to generate secure values:

```python
import secrets
from cryptography.fernet import Fernet

print("FLASK SECRET_KEY:", secrets.token_urlsafe(32))
print("ENCRYPTION ONEWAY SALT:", secrets.token_urlsafe(32))
print("ENCRYPTION REVERSIBLE KEY:", Fernet.generate_key().decode())
```

Copy the output to your Railway environment variables.

---

## Step 5: Deploy

After setting the variables, Railway will automatically redeploy.

Monitor the deployment logs at:
- **Deployments** tab → Click on latest deployment → **View Logs**

---

## Step 6: Initialize Database (First Time Only)

After the Flask app starts, you need to initialize the database:

### Option A: Use Railway Exec Shell

1. Go to **Deployments** tab
2. Click on your active deployment
3. Click **"Exec"** button (opens shell in container)
4. Run the initialization script:

```bash
python scripts/init_railway_db.py
```

### Option B: Automatic Initialization (Recommended)

The Flask app will try to initialize the database automatically on startup. If you see database connection errors, wait a few seconds and Railway will restart the container automatically.

---

## Step 7: Verify Deployment

1. Go to **Domains** tab in your Flask service
2. Click on your generated domain (e.g., `flask-llm-app.up.railway.app`)
3. The app should load successfully

### Health Check

Test the health endpoint:
```bash
curl https://your-domain.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## Troubleshooting

### "could not translate host name" Error

This means the DATABASE_HOST variable is not set correctly.

**Solution**: Make sure you're using Railway reference syntax:
```
DATABASE_HOST=${{Postgres.HOSTNAME}}
```

### "pg_isready: command not found" Error

The PostgreSQL client tools are not installed in the Flask container.

**Solution**: This is expected. Use Python to test the connection instead:
```bash
python -c "import psycopg2; psycopg2.connect(os.environ.get('DATABASE_HOST'), ...)"
```

### "relation does not exist" Error

The database tables haven't been created yet.

**Solution**: Run the initialization script:
```bash
python scripts/init_railway_db.py
```

### Database Initialization Failed

The pgvector extension might not be installed.

**Solution**: Railway's PostgreSQL includes pgvector by default. Verify by running:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## Railway Configuration Files

The following files were created for Railway deployment:

| File | Purpose |
|------|---------|
| `railway.toml` | Railway deployment configuration |
| `Dockerfile` | Container build instructions |
| `scripts/init_railway_db.py` | Database initialization script |
| `requirements.txt` | Python dependencies |

---

## Environment Variable Reference

Complete list of required variables:

| Variable | Railway Reference | Description |
|----------|-------------------|-------------|
| `DATABASE_HOST` | `${{Postgres.HOSTNAME}}` | PostgreSQL hostname |
| `DATABASE_PORT` | `${{Postgres.PORT}}` | PostgreSQL port |
| `DATABASE_NAME` | `${{Postgres.DATABASE}}` | Database name |
| `DATABASE_USER` | `${{Postgres.USERNAME}}` | Database user |
| `DATABASE_PASSWORD` | `${{Postgres.PASSWORD}}` | Database password |
| `FLASK_ENV` | - | Set to `production` |
| `SECRET_KEY` | - | Flask secret key |
| `PORT` | - | Set to `8080` (auto-set by Railway) |
| `ENCRYPTION_ONEWAY_SALT` | - | One-way encryption salt |
| `ENCRYPTION_REVERSIBLE_KEY` | - | Reversible encryption key |
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `GROQ_API_KEY` | - | Groq API key |

---

## Cost Estimate

Railway pricing (as of 2025):

| Service | Estimated Cost |
|---------|----------------|
| Flask App | ~$5-15/month |
| PostgreSQL | ~$5-10/month |
| **Total** | **~$10-25/month** |

---

## Summary

1. ✅ Add PostgreSQL service to Railway project
2. ✅ Configure DATABASE variables with Railway references
3. ✅ Add API keys and encryption keys
4. ✅ Deploy and initialize database
5. ✅ Access your app at Railway domain

For local development, continue using:
```bash
make deploy  # Uses Docker postgres locally
```
