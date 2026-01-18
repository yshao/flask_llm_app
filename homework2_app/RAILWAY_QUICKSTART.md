# Railway Deployment Quickstart Guide with Managed PostgreSQL

Complete step-by-step guide to deploy Flask LLM App on Railway with managed PostgreSQL.

---

## Prerequisites

Before starting, ensure you have:
- ✅ GitHub account with repository access
- ✅ Railway account ([sign up here](https://railway.app))
- ✅ Google Gemini API key ([get here](https://makersuite.google.com/app/apikey))
- ✅ Groq API key ([get here](https://console.groq.com))

---

## Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Search for and select your `flask_llm_app` repository
5. Click **"Import"**

Railway will clone your repository and detect the `railway.toml` configuration.

---

## Step 2: Add Managed PostgreSQL Service

1. In your new Railway project, click **"New Service"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Leave the default settings (pgvector is included)
4. Click **"Add PostgreSQL"**

Railway will create a PostgreSQL service named `Postgres` (or `Postgres1` if you have multiple).

**Important**: Note the service name - you'll need it for environment variable references.

---

## Step 3: Configure Flask Service Environment Variables

1. Click on your Flask service (the one created from GitHub)
2. Go to the **"Variables"** tab
3. Add the following variables:

### Database Variables (Use Railway References)

```bash
# Copy and paste these exactly
DATABASE_HOST=${{Postgres.HOSTNAME}}
DATABASE_PORT=${{Postgres.PORT}}
DATABASE_NAME=${{Postgres.DATABASE}}
DATABASE_USER=${{Postgres.USERNAME}}
DATABASE_PASSWORD=${{Postgres.PASSWORD}}
```

**⚠️ CRITICAL**: Use the exact `${{Service.Variable}}` syntax. Railway will replace these with actual values at runtime.

### Flask Configuration

```bash
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
PORT=8080
```

### Generate Secure Keys

Run this Python script to generate secure values:

```bash
python3 -c "
import secrets
from cryptography.fernet import Fernet
print('SECRET_KEY:', secrets.token_urlsafe(32))
print('ENCRYPTION_ONEWAY_SALT:', secrets.token_urlsafe(32))
print('ENCRYPTION_REVERSIBLE_KEY:', Fernet.generate_key().decode())
"
```

Replace `your_secret_key_here` with the generated SECRET_KEY.

### Encryption Keys

```bash
ENCRYPTION_ONEWAY_SALT=your_generated_salt
ENCRYPTION_REVERSIBLE_KEY=your_generated_key
```

### API Keys

```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## Step 4: Verify Configuration

Your Variables tab should look like this:

```
DATABASE_HOST     ${{Postgres.HOSTNAME}}
DATABASE_PORT     ${{Postgres.PORT}}
DATABASE_NAME     ${{Postgres.DATABASE}}
DATABASE_USER     ${{Postgres.USERNAME}}
DATABASE_PASSWORD  ${{Postgres.PASSWORD}}
FLASK_ENV         production
SECRET_KEY        <generated_value>
ENCRYPTION_ONEWAY_SALT  <generated_value>
ENCRYPTION_REVERSIBLE_KEY  <generated_value>
GEMINI_API_KEY    <your_key>
GEMINI_MODEL      gemini-2.5-flash
GROQ_API_KEY      <your_key>
GROQ_MODEL        llama-3.3-70b-versatile
```

Click **"Save Changes"** when done.

---

## Step 5: Deploy

Railway will automatically deploy when you save changes.

1. Click on **"Deployments"** tab
2. Watch the deployment progress
3. Wait for: ✅ "Deployment succeeded"

---

## Step 6: Initialize Database

The first deployment will fail because the database tables haven't been created yet.

### Method A: Using Railway Exec Shell (Recommended)

1. Go to **Deployments** tab
2. Click on the latest deployment
3. Click **"Exec"** button (opens shell in container)
4. Run the initialization command:

```bash
python scripts/init_railway_db.py
```

You should see:
```
==========================================
Railway PostgreSQL Initialization
==========================================
✓ Connected successfully!
✓ pgvector extension enabled!
==========================================
Initialization Complete!
==========================================
```

### Method B: Using Railway Variables (Automatic)

The Flask app will auto-initialize the database on startup. If it fails, Railway will restart the container automatically (up to 3 times). After the retries, the app should connect successfully.

---

## Step 7: Verify Deployment

1. Go to the **"Domains"** tab in your Flask service
2. Click on your generated domain
3. The app should load successfully

Test the health endpoint:
```bash
curl https://your-domain.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## Complete Environment Variables Reference

Copy this entire block to Railway Variables tab:

```bash
# === DATABASE (Railway Managed PostgreSQL) ===
DATABASE_HOST=${{Postgres.HOSTNAME}}
DATABASE_PORT=${{Postgres.PORT}}
DATABASE_NAME=${{Postgres.DATABASE}}
DATABASE_USER=${{Postgres.USERNAME}}
DATABASE_PASSWORD=${{Postgres.PASSWORD}}

# === FLASK CONFIGURATION ===
FLASK_ENV=production
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING
PORT=8080

# === ENCRYPTION KEYS (Generate with Python script below) ===
ENCRYPTION_ONEWAY_SALT=CHANGE_THIS_TO_A_RANDOM_STRING
ENCRYPTION_REVERSIBLE_KEY=CHANGE_THIS_TO_A_FERNET_KEY

# === GEMINI API ===
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_TOKENS=4000
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_CONVERSATION_HISTORY=1

# === GROQ API ===
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MAX_TOKENS=4000
GROQ_TEMPERATURE=0.7
GROQ_MAX_CONVERSATION_HISTORY=1

# === RATE LIMITING ===
RATE_LIMIT_QUOTA=1000
RATE_LIMIT_INTERVAL=1
```

---

## Generate Secure Keys

Run this to generate all required keys:

```bash
python3 << 'EOF'
import secrets
from cryptography.fernet import Fernet

print("=== COPY THESE TO RAILWAY VARIABLES ===")
print()
print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"ENCRYPTION_ONEWAY_SALT={secrets.token_urlsafe(32)}")
print(f"ENCRYPTION_REVERSIBLE_KEY={Fernet.generate_key().decode()}")
print()
print("==========================================")
print("API keys you need to get yourself:")
print("  - GEMINI_API_KEY from https://makersuite.google.com/app/apikey")
print("  - GROQ_API_KEY from https://console.groq.com")
EOF
```

---

## Troubleshooting

### Error: "could not translate host name"

**Cause**: `DATABASE_HOST` is not set correctly.

**Fix**: Make sure you're using `${{Postgres.HOSTNAME}}` exactly (case-sensitive).

### Error: "relation does not exist"

**Cause**: Database tables haven't been created.

**Fix**: Run the initialization script in Railway Exec shell:
```bash
python scripts/init_railway_db.py
```

### Error: "FATAL: database "homework_db" does not exist"

**Cause**: The database name in Railway's PostgreSQL is different.

**Fix**: Check Railway's PostgreSQL service to see the actual database name, or create the database:
```bash
# In Railway Exec shell
psql -U postgres -c "CREATE DATABASE homework_db;"
```

Then update `DATABASE_NAME=${{Postgres.DATABASE}}` in variables.

### Health check failing

**Check logs**: Go to **Deployments** → Click deployment → **View Logs**

**Common issues**:
- API keys not set or invalid
- Database connection failed
- App crashed during startup

---

## Railway Dashboard Navigation

```
Railway Project
├── flask-llm-app (Flask service)
│   ├── Variables (configure env vars here)
│   ├── Deployments (view deployment logs)
│   ├── Domains (get your app URL)
│   ├── Metrics (usage stats)
│   └── Settings (config)
└── Postgres (PostgreSQL service)
    ├── Variables (view connection details)
    ├── Metrics (database stats)
    └── Connect (get connection strings)
```

---

## Cost Summary

| Service | Monthly Cost |
|---------|--------------|
| Flask App (compute) | ~$5-15/month |
| PostgreSQL (database) | ~$5-10/month |
| **Total** | **~$10-25/month** |

---

## Next Steps After Deployment

1. ✅ Your app is live at `https://flask-llm-app.up.railway.app` (or similar)
2. ✅ Database is managed by Railway
3. ✅ Backups are automatic
4. ✅ Scaling is handled automatically

---

## Quick Checklist

- [ ] Railway project created
- [ ] PostgreSQL service added
- [ ] Flask service added from GitHub
- [ ] Environment variables configured (use Railway references!)
- [ ] API keys added (Gemini, Groq)
- [ ] Secure keys generated (SECRET_KEY, encryption)
- [ ] Deployed successfully
- [ ] Database initialized (ran init script or auto)
- [ ] Health check passing
- [ ] App accessible via domain

---

## Local vs Railway Deployment

| Aspect | Local (Docker) | Railway (Managed) |
|--------|----------------|-------------------|
| **Database** | Docker postgres locally | Railway managed PostgreSQL |
| **App** | Native Python on host | Docker container |
| **Cost** | Free | ~$10-25/month |
| **Backups** | Manual (volume) | Automatic |
| **Scaling** | Manual | Automatic |

**Switching between local and Railway**:
```bash
# Local development
make deploy

# Railway deployment
# (push to GitHub, Railway auto-deploys)
```

---

Need help? Check:
- Railway documentation: https://docs.railway.app
- Troubleshooting section above
- Deployment logs in Railway dashboard
