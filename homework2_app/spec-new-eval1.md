# Specification: Fix Homework 1 Evaluation Issues

**Version:** 3.0 - INFRASTRUCTURE FIX
**Date:** 2025-12-31
**Based on:** `eval1_report.md`
**Reference:** `backup_md/homework1_evaluation_todo.md`

---

## Overview

This specification proposes fixes for the **critical infrastructure issue** preventing the Homework 1 evaluation from running in `homework2_app`. The Flask app cannot connect to the database from within its Docker container, blocking 3 of 4 evaluation tests.

---

## Problem Statement

### Current State: 25/100 (BLOCKED)

| Test | Score | Issue |
|------|-------|-------|
| Test 1: Database Read Expert | 0/25 | 405 METHOD NOT ALLOWED - Flask app not responding |
| Test 2: Database Write Expert | 0/25 | 405 METHOD NOT ALLOWED - Flask app not responding |
| Test 3: Orchestrator Coordination | 0/25 | 405 METHOD NOT ALLOWED - Flask app not responding |
| Test 4: Database Schema | 25/25 | PASSED | Database connection works from host |

### Root Cause Identified

**Critical Infrastructure Issue:**

```
psycopg2.OperationalError: connection to server at "postgres" (172.18.0.2), port 5432 failed:
  FATAL: password authentication failed for user "postgres"
```

**Location:** `flask_app/__init__.py:42` (`initialize_database()`)

The Flask app attempts database connection during initialization, but authentication fails from within the Docker container. This prevents the app from starting properly.

---

## Proposed Fixes

### Fix 1: Update docker-compose.yml Environment Variable Mounting

**File:** `homework2_app/docker-compose.yml`

**Current Issue:** Environment variables may not be correctly mounted into Flask container.

**Fix:**
```yaml
services:
  flask-app:
    env_file:
      - .env  # Ensure .env file is mounted
    environment:
      DATABASE_PASSWORD: ${DATABASE_PASSWORD:-iamsoecure}  # Provide fallback
```

**Expected Result:** Flask container receives correct DATABASE_PASSWORD environment variable.

---

### Fix 2: Reset Database with Known Credentials

**File:** Database + Docker containers

**Issue:** Database may have been created with a different password than what's in .env

**Steps:**
1. Stop all containers:
   ```bash
   docker compose down
   ```

2. Recreate database with known password:
   ```bash
   docker compose up -d postgres
   docker compose exec -T postgres psql -U postgres -d db -c "ALTER USER postgres WITH PASSWORD 'iamsoecure';"
   ```

3. Restart Flask app:
   ```bash
   docker compose restart flask-app
   ```

**Expected Result:** Database accepts password `iamsoecure` from both host and container.

---

### Fix 3: Verify Environment Variables in Flask Container

**Steps:**
1. Check Flask container environment:
   ```bash
   docker exec flask_llm_app printenv | grep PASSWORD
   ```

2. If not found, recreate Flask container:
   ```bash
   docker compose down flask-app
   docker compose up -d flask-app
   ```

**Expected Result:** `DATABASE_PASSWORD=iamsoecure` is set in Flask container.

---

### Fix 4: Add Database Connection Retry Logic

**File:** `homework2_app/flask_app/utils/database.py`

**Current Code (Line 89):**
```python
cnx = psycopg2.connect(
    host=self.host,
    user=self.user,
    password=self.password,
    port=self.port,
    database=self.database
)
```

**Improved Code:**
```python
retry = 3
for attempt in range(retry):
    try:
        cnx = psycopg2.connect(
            host=self.host,
            user=self.port,
            password=self.password,
            port=self.port,
            database=self.database
        )
        break  # Connection successful
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e) and attempt < retry - 1:
            logger.warning(f"Database connection attempt {attempt + 1} failed (auth), retrying...")
            import time
            time.sleep(2)
        else:
            raise
```

**Expected Result:** Connection retries on authentication failures.

---

### Fix 5: Add Health Check Endpoint

**File:** `homework2_app/flask_app/routes.py`

**Add:**
```python
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for testing if Flask app is running."""
    try:
        # Test database connection
        db = database()
        conn = db.query("SELECT 1")
        return jsonify({
            "status": "healthy",
            "flask_app": "running",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

**Usage:**
```bash
curl http://localhost:8080/health
```

**Expected Result:** Returns 200 when Flask app is fully started and connected.

---

## Implementation Steps

### Step 1: Backup Current State

```bash
# Save current .env file
cp .env .env.backup
```

---

### Step 2: Fix docker-compose.yml

**Edit:** `homework2_app/docker-compose.yml`

Add explicit environment variable fallback:
```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-iamsoecure}
```

---

### Step 3: Reset Database and Containers

```bash
# Stop everything
docker compose down

# Recreate database with known credentials
docker compose up -d postgres
docker compose exec -T postgres psql -U postgres -d db -c "ALTER USER postgres WITH PASSWORD 'iamsoecure';"

# Start Flask app
docker compose up -d flask-app
```

---

### Step 4: Verify Flask Container Environment

```bash
# Check Flask container has correct password
docker exec flask_llm_app printenv | grep DATABASE_PASSWORD
```

Expected: `DATABASE_PASSWORD=iamsoecure`

---

### Step 5: Verify Database Connection from Container

```bash
# Test database from within Flask container
docker exec flask_llm_app python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    port=5432,
    user='postgres',
    password='iamsoecure',
    database='db'
)
print('✓ Database connection works from container!')
conn.close()
"
```

Expected: `✓ Database connection works from container!`

---

### Step 6: Verify Flask App Startup

```bash
# Check Flask app logs
docker logs flask_llm_app 2>&1 | tail -20
```

Expected:
- No password errors
- No initialization errors
- Server started successfully

---

### Step 7: Test Health Endpoint

```bash
# Test health endpoint
curl http://localhost:8080/health
```

Expected: Returns JSON with `status: "healthy"`

---

### Step 8: Re-run Evaluation

```bash
# Run evaluation from homework2_app directory
DATABASE_PASSWORD=iamsoecure python3 ../scripts/evaluate_homework1.py
```

Expected: All tests should run with 100/100 score.

---

## Verification Checklist

After implementing fixes:

- [ ] Flask app logs show successful database connection
- [ ] curl http://localhost:8080/health returns 200
- [ ] curl http://localhost:8080/ returns 200
- [ ] POST http://localhost:8080/chat/ai with JSON returns 200
- [ ] Evaluation script runs without 405 errors
- [ ] All 4 tests pass with 25/25 each
- [ ] Total score = 100/100

---

## Expected Final Results

### After Infrastructure Fix

| Test | Score | Status |
|------|-------|--------|
| Test 1: Database Read Expert | 25/25 | PASSED |
| Test 2: Database Write Expert | 25/25 | PASSED |
| Test 3: Orchestrator Coordination | 25/25 | PASSED |
| Test 4: Database Schema | 25/25 | PASSED |
| **TOTAL** | **100/100** | **ALL TESTS PASSED** |

---

## Summary

The evaluation script is well-implemented and correctly follows the spec. The 405 errors are caused by a Flask app infrastructure issue, not evaluation script problems.

**Priority:** CRITICAL - Fix database connection issue to allow evaluation to run.

**Expected After Fix:** 100/100

**Date:** 2025-12-31
