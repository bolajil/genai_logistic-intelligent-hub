# GLIH OPS — Production Readiness Guide

> **Who this is for:** Anyone deploying GLIH OPS to a live environment serving real users.
> **What this covers:** Code quality checks, testing, infrastructure, monitoring, and scaling to 1M+ users.

---

## Table of Contents

1. [Why Production Readiness Matters](#1-why-production-readiness-matters)
2. [Current State vs Production State](#2-current-state-vs-production-state)
3. [Priority 1 — Already Fixed (Do These Now)](#3-priority-1--already-fixed-do-these-now)
4. [Priority 2 — Database Migration](#4-priority-2--database-migration)
5. [Priority 3 — Redis for Shared State](#5-priority-3--redis-for-shared-state)
6. [Priority 4 — Code Quality Checks](#6-priority-4--code-quality-checks)
7. [Priority 5 — Testing Strategy](#7-priority-5--testing-strategy)
8. [Priority 6 — Load Testing](#8-priority-6--load-testing)
9. [Priority 7 — Monitoring & Alerting](#9-priority-7--monitoring--alerting)
10. [Priority 8 — Infrastructure Scaling](#10-priority-8--infrastructure-scaling)
11. [Deployment Commands](#11-deployment-commands)
12. [The 6 Numbers You Must Know Before Go-Live](#12-the-6-numbers-you-must-know-before-go-live)

---

## 1. Why Production Readiness Matters

When a system is running on your laptop for a demo it only handles **1 user — you**.

Production means:
- **1,000 users** hitting `/query` at the same time
- A dispatcher in Chicago and one in Dallas both running agents simultaneously
- The backend crashing at 2am while a temperature breach alert is in flight
- A bad actor hammering your API with 10,000 requests to exhaust your OpenAI quota

Every item in this guide is a **specific failure mode** that will happen without it.

---

## 2. Current State vs Production State

| Component | Current (Dev) | Production Target |
|---|---|---|
| User store | `glih_users.json` flat file | PostgreSQL database |
| Agent progress store | In-memory Python dict | Redis (shared across all servers) |
| JWT secret | Hardcoded string ✅ Fixed | Environment variable ✅ Fixed |
| Rate limiting | None ✅ Fixed | 30 req/min per IP ✅ Fixed |
| Error tracking | None ✅ Fixed | Sentry ✅ Fixed |
| Web server | Single uvicorn process | Gunicorn + multiple workers ✅ Fixed |
| Vector store | Local ChromaDB | Hosted Qdrant / Pinecone |
| Secrets | Mixed | All in `.env` / AWS Secrets Manager |
| Monitoring | None | Prometheus + Grafana |
| Load testing | None | Locust ✅ Created |

---

## 3. Priority 1 — Already Fixed (Do These Now)

These changes are already in the codebase. You just need to **install** and **configure** them.

### 3.1 Install New Dependencies

```bash
# Activate your conda environment first
conda activate genai_project2

# Install from backend directory
cd glih-backend
pip install slowapi sentry-sdk[fastapi] gunicorn
```

**What each does:**
- `slowapi` — Rate limiting middleware. Stops any one IP from flooding your API
- `sentry-sdk` — Automatic error capturing. Every crash gets reported with full stack trace
- `gunicorn` — Production-grade process manager. Runs multiple workers so one crash doesn't kill everything

### 3.2 Update Your .env File

Open `.env` in the project root and add/update these values:

```bash
# ── Security (CRITICAL — change these before ANY deployment) ──────────────────
JWT_SECRET=your-secure-random-string-minimum-32-characters-long

# Generate a secure value with:
# python -c "import secrets; print(secrets.token_hex(32))"

# ── Rate limiting (requests per minute per IP) ────────────────────────────────
RATE_LIMIT_QUERY=30/minute
RATE_LIMIT_AGENTS=20/minute
RATE_LIMIT_INGEST=10/minute

# ── Sentry (get DSN from sentry.io — free tier available) ────────────────────
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/123456

# ── Environment ───────────────────────────────────────────────────────────────
GLIH_ENV=production

# ── Gunicorn workers ──────────────────────────────────────────────────────────
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
```

**Why JWT_SECRET matters:** If this is left as the default string, anyone who knows it can forge tokens and log in as any user. Generate a new one for every environment.

**Expected output after setup:**
```
✓ GLIH Backend starting — workers: 4
✓ Sentry initialized (environment: production)
✓ Rate limiter active: 30/min query, 20/min agents
```

### 3.3 Start with Gunicorn Instead of Uvicorn

Replace your current start command:

```bash
# ❌ Old (single process — dies under load)
uvicorn glih_backend.api.main:app --host 0.0.0.0 --port 9001

# ✅ New (multi-process — survives load)
cd glih-backend
gunicorn -c gunicorn.conf.py glih_backend.api.main:app
```

**What this does:** Gunicorn spawns `(2 × CPU cores) + 1` worker processes. On a 4-core server that's 9 workers. If one worker crashes handling a bad request, the other 8 keep serving traffic. Users never see the crash.

### 3.4 Set Up Sentry (5 minutes)

1. Go to [sentry.io](https://sentry.io) → Create free account
2. Create new project → Select **Python** → **FastAPI**
3. Copy the DSN value it gives you
4. Paste it in `.env` as `SENTRY_DSN=...`
5. Restart the backend

**Expected output in Sentry:** Every 500 error now appears in your Sentry dashboard with:
- Full Python stack trace
- The request that caused it
- User info (if logged in)
- Environment (production vs dev)

---

## 4. Priority 2 — Database Migration

### The Problem

`glih_users.json` is a flat file. Under load:
- Two requests writing simultaneously corrupt the file
- File locks cause requests to queue up and time out
- Does not scale across multiple servers

### The Fix — PostgreSQL

#### Step 1: Install PostgreSQL

```bash
# Windows — download installer from postgresql.org
# Or use Docker:
docker run -d \
  --name glih-postgres \
  -e POSTGRES_USER=glih \
  -e POSTGRES_PASSWORD=your-secure-password \
  -e POSTGRES_DB=glih \
  -p 5432:5432 \
  postgres:15
```

#### Step 2: Install Python driver

```bash
pip install asyncpg psycopg2-binary sqlalchemy[asyncio]
```

#### Step 3: Create the users table

```sql
-- Run this in psql or any SQL client
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role        VARCHAR(50) DEFAULT 'user',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    force_password_change BOOLEAN DEFAULT FALSE,
    last_login  TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    token       TEXT PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### Step 4: Replace the file-backed store in auth_utils.py

```python
# Replace _load_db / _save_db / store_user / get_user_by_email
# with SQLAlchemy calls

import sqlalchemy as sa
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://glih:password@localhost:5432/glih")
_engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

def store_user(user: dict) -> None:
    with _engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO users (id, name, email, hashed_password, role, created_at, force_password_change)
            VALUES (:id, :name, :email, :hashed_password, :role, :created_at, :force_password_change)
            ON CONFLICT (email) DO UPDATE SET
                name = EXCLUDED.name,
                hashed_password = EXCLUDED.hashed_password,
                role = EXCLUDED.role
        """), user)
        conn.commit()

def get_user_by_email(email: str) -> Optional[dict]:
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email.lower()}
        ).fetchone()
        return dict(row._mapping) if row else None

def get_user_by_id(user_id: str) -> Optional[dict]:
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()
        return dict(row._mapping) if row else None
```

#### Step 5: Update .env

```bash
DATABASE_URL=postgresql://glih:your-password@localhost:5432/glih
```

**Expected result:** User data survives backend restarts, handles 1,000 concurrent logins, and never corrupts on parallel writes.

---

## 5. Priority 3 — Redis for Shared State

### The Problem

`_progress_store` is a Python dict in memory. If you run 4 Gunicorn workers:
- Worker 1 starts an agent run and stores events in its own memory
- Worker 2 handles the polling request — it has NO events (different process)
- Dispatcher sees nothing in the live event feed

### The Fix — Redis

#### Step 1: Install Redis

```bash
# Docker (easiest)
docker run -d \
  --name glih-redis \
  -p 6379:6379 \
  redis:7-alpine

# Or Windows native: download from redis.io/download
```

#### Step 2: Install Python client

```bash
pip install redis
```

#### Step 3: Replace in-memory progress store

```python
# In main.py — replace _progress_store dict with Redis

import redis as _redis
import json as _json

_redis_client = _redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)
_PROGRESS_TTL = 3600  # events expire after 1 hour

def _init_run(run_id: str) -> None:
    data = {"events": [], "status": "running", "result": None, "error": None}
    _redis_client.setex(f"run:{run_id}", _PROGRESS_TTL, _json.dumps(data))

def emit_progress(run_id: str, step: str, message: str, data: dict = None) -> None:
    key = f"run:{run_id}"
    raw = _redis_client.get(key)
    if raw:
        stored = _json.loads(raw)
        stored["events"].append({
            "step": step, "message": message,
            "data": data or {}, "ts": _datetime.utcnow().isoformat()
        })
        _redis_client.setex(key, _PROGRESS_TTL, _json.dumps(stored))
    logger.info(f"[{run_id[:8]}] {step}: {message}")

def _complete_run(run_id: str, result: dict = None, error: str = None) -> None:
    key = f"run:{run_id}"
    raw = _redis_client.get(key)
    if raw:
        stored = _json.loads(raw)
        stored["status"] = "error" if error else "complete"
        stored["result"] = result
        stored["error"] = error
        _redis_client.setex(key, _PROGRESS_TTL, _json.dumps(stored))

@app.get("/agents/progress/{run_id}")
def get_agent_progress(run_id: str):
    raw = _redis_client.get(f"run:{run_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="run_id not found")
    return _json.loads(raw)
```

#### Step 4: Update .env

```bash
REDIS_URL=redis://localhost:6379
```

**Expected result:** All 4 Gunicorn workers share the same event store. Polling works correctly regardless of which worker handles the request.

---

## 6. Priority 4 — Code Quality Checks

Run these before every deployment. They catch bugs that tests miss.

### Setup

```bash
pip install ruff mypy
```

### Ruff — Python Linting

```bash
# Run from glih-backend/
ruff check src/

# Auto-fix safe issues
ruff check src/ --fix
```

**What it catches:**
- Unused imports (wasted memory)
- Undefined variables (runtime crashes)
- Security anti-patterns (using `eval`, bare `except`)
- Style violations that make code hard to read

**Expected clean output:**
```
All checks passed.
```

### Mypy — Type Checking

```bash
mypy src/glih_backend/api/main.py --ignore-missing-imports
```

**What it catches:**
- Passing a string where an int is expected
- Calling `.lower()` on something that might be None
- Missing return statements

### Frontend — ESLint

```bash
cd glih-frontend-next
npm run lint
```

**Expected output:**
```
✓ No ESLint warnings or errors
```

---

## 7. Priority 5 — Testing Strategy

Tests are your safety net. They catch regressions — breaking something that used to work.

### Setup

```bash
pip install pytest pytest-asyncio httpx
```

Create the test directory structure:
```
glih-backend/
  tests/
    test_auth.py
    test_query.py
    test_agents.py
    test_chunking.py
```

### Unit Tests

```python
# tests/test_chunking.py
# Tests the sentence-boundary chunker — if this breaks, ingestion breaks

from glih_backend.api.main import _chunk_text

def test_chunk_respects_sentence_boundaries():
    text = "First sentence. Second sentence. Third sentence."
    chunks = _chunk_text(text, max_chars=30)
    for chunk in chunks:
        # No chunk should end mid-word
        assert not chunk[-1].isalpha() or chunk.endswith((".", "!", "?"))

def test_chunk_minimum_size():
    text = "A" * 2000
    chunks = _chunk_text(text, max_chars=500)
    assert all(len(c) <= 600 for c in chunks)  # allow 20% overflow for sentence boundary
```

```python
# tests/test_auth.py
# Tests the JWT auth system

from glih_backend.api.auth_utils import (
    hash_password, verify_password,
    create_access_token, decode_access_token
)

def test_password_hash_and_verify():
    plain = "MySecurePassword123!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_access_token_roundtrip():
    token = create_access_token("user-123", "test@example.com", "Test User")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"
    assert payload["type"] == "access"
```

```python
# tests/test_query.py
# Integration test — requires backend running

from fastapi.testclient import TestClient
from glih_backend.api.main import app

client = TestClient(app)

def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200

def test_query_returns_answer():
    resp = client.get("/query", params={"q": "temperature breach", "k": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)

def test_query_rate_limit():
    """Fire 35 requests — should get 429 after 30."""
    responses = [client.get("/query", params={"q": "test"}) for _ in range(35)]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, "Rate limiter did not trigger"
```

### Run All Tests

```bash
cd glih-backend
pytest tests/ -v

# Expected output:
# tests/test_auth.py::test_password_hash_and_verify PASSED
# tests/test_auth.py::test_access_token_roundtrip PASSED
# tests/test_chunking.py::test_chunk_respects_sentence_boundaries PASSED
# tests/test_query.py::test_health_returns_200 PASSED
# tests/test_query.py::test_query_returns_answer PASSED
# tests/test_query.py::test_query_rate_limit PASSED
# 6 passed in 4.2s
```

---

## 8. Priority 6 — Load Testing

Load testing simulates hundreds of real users hitting the system simultaneously. It finds breaking points before your users do.

### Setup

```bash
pip install locust
```

The load test file is already created at `tests/load_test.py`.

### Run the Load Test

```bash
# Start the backend first, then:
locust -f tests/load_test.py --host http://localhost:9001
```

Open your browser at `http://localhost:8089`

**Settings to use:**
| Scenario | Users | Spawn Rate | Duration |
|---|---|---|---|
| Baseline | 10 | 2/sec | 2 min |
| Normal load | 100 | 10/sec | 5 min |
| Stress test | 500 | 50/sec | 5 min |
| Spike test | 1000 | 200/sec | 2 min |

### What to Look For

**Green (passing):**
```
✓ P95 response time < 3,000ms
✓ Error rate < 1%
✓ RPS (requests/sec) stable, not dropping
```

**Red (failing):**
```
✗ P95 response time > 8,000ms  → add workers or cache
✗ Error rate > 1%               → check logs for 500 errors
✗ 429 Too Many Requests         → adjust RATE_LIMIT_QUERY
✗ Connection refused            → server ran out of file descriptors
```

### Fix Connection Limits on Linux (required for 10k+ users)

```bash
# Increase open file descriptor limit
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Apply without reboot
ulimit -n 65536
```

---

## 9. Priority 7 — Monitoring & Alerting

### Sentry — Error Tracking (Already Configured)

What happens when you set `SENTRY_DSN`:
1. Every unhandled exception is captured automatically
2. You get an email/Slack alert within 60 seconds
3. Each error shows: full stack trace, request payload, user info, environment

**Setup:** Free tier at [sentry.io](https://sentry.io) — no credit card required.

### Health Check Endpoints

Already exist in the codebase:

```bash
# Basic liveness check (used by load balancers)
GET /health
# Returns: {"status": "ok"}

# Detailed readiness check (checks all dependencies)
GET /health/detailed
# Returns: {"llm": "ok", "embeddings": "ok", "vector_store": "ok"}
```

**Why both matter:**
- Load balancers use `/health` — if it fails, traffic is routed away
- `/health/detailed` tells you WHICH component is broken (LLM? ChromaDB? Auth?)

### Add Prometheus Metrics (Optional but Powerful)

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# Add to main.py after app creation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

This exposes `/metrics` which Grafana can scrape to show:
- Requests per second
- P50 / P95 / P99 response times
- Error rate per endpoint
- Active connections

### Logging Best Practices

The backend already logs to stdout. In production, pipe it to a log aggregator:

```bash
# With Gunicorn — logs go to stdout/stderr
# Docker collects them automatically
# Or redirect to a file:
gunicorn -c gunicorn.conf.py glih_backend.api.main:app \
  --access-logfile /var/log/glih/access.log \
  --error-logfile /var/log/glih/error.log
```

---

## 10. Priority 8 — Infrastructure Scaling

### For 1,000 Users — Single Server

```
┌─────────────────────────────────────┐
│           Nginx (reverse proxy)      │
│       SSL termination + static files │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Gunicorn (9 workers)           │
│      glih_backend.api.main:app      │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
PostgreSQL   Redis    ChromaDB
(users)   (progress) (vectors)
```

**Nginx config:**
```nginx
upstream glih_backend {
    server 127.0.0.1:9001;
    keepalive 32;
}

server {
    listen 443 ssl;
    server_name glih.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/glih.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/glih.yourdomain.com/privkey.pem;

    # Rate limiting at Nginx level (first line of defence)
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://glih_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;    # match Gunicorn timeout
    }

    location / {
        root /var/www/glih-frontend;
        try_files $uri /index.html;
    }
}
```

### For 100,000+ Users — Kubernetes

The IaC is already in `deploy/` from the previous session:
- `deploy/aws/` — EKS cluster + RDS + ElastiCache
- `deploy/gcp/` — GKE Autopilot
- `deploy/azure/` — AKS

**Key settings to configure before scaling:**

```yaml
# deploy/kubernetes/backend-deployment.yaml
spec:
  replicas: 4            # start here, autoscale from 2-20
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"
  env:
    - name: REDIS_URL
      valueFrom:
        secretKeyRef:
          name: glih-secrets
          key: redis-url
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: glih-secrets
          key: database-url
```

**Horizontal Pod Autoscaler:**
```yaml
# Automatically add pods when CPU hits 70%
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: glih-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: glih-backend
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 11. Deployment Commands

### Development (current)

```bash
conda activate genai_project2
cd glih-backend
uvicorn glih_backend.api.main:app --host 0.0.0.0 --port 9001 --reload
```

### Staging (test before production)

```bash
conda activate genai_project2
cd glih-backend
GLIH_ENV=staging gunicorn -c gunicorn.conf.py glih_backend.api.main:app
```

### Production (single server)

```bash
conda activate genai_project2
cd glih-backend

# Set environment
export GLIH_ENV=production
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# Start with Gunicorn
gunicorn -c gunicorn.conf.py glih_backend.api.main:app \
  --daemon \
  --pid /var/run/glih.pid
```

### Docker Production

```bash
# Build
docker build -t glih-backend:latest ./glih-backend

# Run
docker run -d \
  --name glih-backend \
  --env-file .env \
  -p 9001:9001 \
  --restart unless-stopped \
  glih-backend:latest
```

### Docker Compose (full stack)

```bash
# Start everything: backend + frontend + postgres + redis
docker-compose up -d

# Check logs
docker-compose logs -f glih-backend

# Restart just backend after code change
docker-compose restart glih-backend
```

---

## 12. The 6 Numbers You Must Know Before Go-Live

Run a load test with 100 users and record these. If any are in the red, do not go live.

| # | Metric | Green ✓ | Yellow ⚠ | Red ✗ | How to Fix |
|---|---|---|---|---|---|
| 1 | P95 `/query` response | < 3s | 3–8s | > 8s | Add Redis cache for repeated queries |
| 2 | P95 `/agents/*` response | < 15s | 15–30s | > 30s | Increase Gunicorn workers |
| 3 | Error rate | < 0.1% | 0.1–1% | > 1% | Check Sentry for root cause |
| 4 | 429 rate limit hits | 0% normal use | — | > 5% | Adjust RATE_LIMIT_QUERY |
| 5 | Server CPU under 100 users | < 60% | 60–80% | > 80% | Scale up server or add workers |
| 6 | Memory under 100 users | < 70% | 70–85% | > 85% | Check for memory leaks in BM25 index |

---

## Quick Reference — Commands Cheat Sheet

```bash
# Install production deps
pip install slowapi sentry-sdk[fastapi] gunicorn psycopg2-binary redis locust ruff mypy

# Generate secure JWT secret
python -c "import secrets; print(secrets.token_hex(32))"

# Start production server
gunicorn -c glih-backend/gunicorn.conf.py glih_backend.api.main:app

# Run all tests
cd glih-backend && pytest tests/ -v

# Run linter
ruff check glih-backend/src/

# Run load test (100 users)
locust -f tests/load_test.py --host http://localhost:9001 --headless -u 100 -r 10 --run-time 2m

# Check health
curl http://localhost:9001/health
curl http://localhost:9001/health/detailed
```

---

*Last updated: 2026-03-27 | GLIH OPS v0.1.0 | Author: Lanre Bolaji*
