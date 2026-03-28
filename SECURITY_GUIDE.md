# GLIH Platform — Security Guide

> **Status:** Production-ready hardening applied
> **Framework:** OWASP Top 10 (2021)
> **Last updated:** 2026-03-27

This document covers every security measure applied to the GLIH platform, why each one matters, how to verify it works, and what to check before going live. Follow this guide before any production deployment.

---

## Table of Contents

1. [Security Audit Summary](#1-security-audit-summary)
2. [OWASP Top 10 Coverage](#2-owasp-top-10-coverage)
3. [Authentication & JWT Hardening](#3-authentication--jwt-hardening)
4. [Password Security (bcrypt)](#4-password-security-bcrypt)
5. [File Upload Security](#5-file-upload-security)
6. [Rate Limiting (Brute-Force Protection)](#6-rate-limiting-brute-force-protection)
7. [HTTP Security Headers](#7-http-security-headers)
8. [CORS Hardening](#8-cors-hardening)
9. [TLS & Transport Security](#9-tls--transport-security)
10. [Secrets Management](#10-secrets-management)
11. [Dependency Security](#11-dependency-security)
12. [Penetration Testing Checklist](#12-penetration-testing-checklist)
13. [Security Go/No-Go Checklist](#13-security-gono-go-checklist)

---

## 1. Security Audit Summary

The following vulnerabilities were identified and remediated. Severity follows CVSS 3.1 scoring.

| # | Vulnerability | OWASP | Severity | Status |
|---|---------------|-------|----------|--------|
| 1 | Hardcoded admin password in source code | A02 | **Critical** | ✅ Fixed |
| 2 | SHA-256 used for password hashing (not bcrypt) | A02 | **Critical** | ✅ Fixed |
| 3 | JWT secret with no env var enforcement | A02 | **High** | ✅ Fixed |
| 4 | `verify=False` in outbound HTTP requests (SSRF risk) | A10 | **High** | ✅ Fixed |
| 5 | No rate limiting on login endpoint | A07 | **High** | ✅ Fixed |
| 6 | File upload with no type or size validation | A04 | **High** | ✅ Fixed |
| 7 | Wildcard CORS `allow_origins=["*"]` | A05 | **High** | ✅ Fixed |
| 8 | No security headers (X-Frame-Options, CSP, etc.) | A05 | **Medium** | ✅ Fixed |
| 9 | Unprotected `/debug/bm25` and `/config` endpoints | A01 | **Medium** | ⚠️ Pending |
| 10 | No auth event logging (failed logins, changes) | A09 | **Medium** | ⚠️ Pending |
| 11 | Bare `except:` clauses hiding errors | A05 | **Medium** | ⚠️ Pending |
| 12 | In-memory refresh token store (lost on restart) | A07 | **Low** | 📋 Planned |
| 13 | No refresh token TTL enforcement | A07 | **Low** | 📋 Planned |
| 14 | Dispatcher accounts have no password storage | A02 | **Low** | ✅ Fixed |
| 15 | Admin dispatcher login disabled if env var missing | A02 | **Low** | ✅ Fixed |

**Legend:**
- ✅ Fixed — Code change applied and committed
- ⚠️ Pending — Identified, not yet implemented
- 📋 Planned — In backlog for next sprint

---

## 2. OWASP Top 10 Coverage

### A01 — Broken Access Control
**Risk:** Unauthenticated users accessing admin features or internal debug endpoints.

**What we did:**
- All agent endpoints require valid JWT Bearer token via `get_current_user` dependency
- All admin management routes (user CRUD, dispatcher CRUD) require `role == "admin"` check
- File ingest endpoints require authentication

**What remains:**
```python
# TODO: Add auth to these endpoints in main.py
@app.get("/debug/bm25")          # Currently unprotected
@app.get("/config")              # Currently unprotected
```
**Fix (add to each):**
```python
from glih_backend.api.auth_utils import get_current_user

@app.get("/debug/bm25")
async def debug_bm25(current_user: dict = Depends(get_current_user)):
    ...
```

---

### A02 — Cryptographic Failures
**Risk:** Weak password hashing means compromised database exposes all passwords.

**What we did:** See [Section 4 — Password Security](#4-password-security-bcrypt).

**Verify:**
```bash
# Correct: bcrypt hash starts with $2b$
python -c "from glih_backend.dispatchers import hash_password; print(hash_password('test'))"
# Output: $2b$12$...  ✅

# Wrong: SHA-256 hash is 64 hex chars
# Output: 098f...     ❌
```

---

### A03 — Injection
**Risk:** SQL injection, prompt injection, path traversal.

**What we did:**
- No raw SQL — uses in-memory stores and ChromaDB (no SQL injection surface)
- File paths sanitized through `pathlib.Path` (no traversal)
- LLM prompts constructed with f-strings (not user-controlled templates)

**Remaining vigilance:** If PostgreSQL is added (see PRODUCTION_GUIDE.md), always use parameterized queries:
```python
# SAFE
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# UNSAFE — never do this
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

---

### A04 — Insecure Design
**Risk:** Architectural weaknesses that can't be patched later.

**What we did:**
- File uploads capped at 20 MB (`MAX_UPLOAD_MB` env var)
- File type validated by magic bytes, not filename extension
- PDF content verified before processing
- Background tasks prevent DoS via long-running synchronous requests

---

### A05 — Security Misconfiguration
**Risk:** Default settings, open CORS, missing headers let attackers exploit the platform.

**What we did:** See [Section 7 — HTTP Headers](#7-http-security-headers) and [Section 8 — CORS](#8-cors-hardening).

---

### A07 — Identification and Authentication Failures
**Risk:** Weak credentials, no brute-force protection, session hijacking.

**What we did:** See [Section 3 — JWT](#3-authentication--jwt-hardening) and [Section 6 — Rate Limiting](#6-rate-limiting-brute-force-protection).

---

### A09 — Security Logging and Monitoring Failures
**Risk:** Attackers go undetected; no audit trail for incident response.

**What remains to implement:**
```python
# Add to auth_utils.py — log all auth events
import logging
audit_log = logging.getLogger("glih.audit")

def log_auth_event(event: str, user_id: str, ip: str, success: bool):
    audit_log.info(
        f"AUTH_EVENT event={event} user={user_id} ip={ip} success={success}"
    )

# Call on every login attempt, password change, token refresh
```

---

### A10 — Server-Side Request Forgery (SSRF)
**Risk:** Backend fetches attacker-controlled URLs, potentially reaching internal services.

**What we did:**
```python
# Before (VULNERABLE):
session.get(url, verify=False)  # Disables TLS cert check, enables MITM

# After (FIXED):
session.get(url, verify=True)   # Validates cert chain properly
```

For production, consider also whitelisting allowed URL domains for the `/ingest/url` endpoint.

---

## 3. Authentication & JWT Hardening

### What Changed

**File:** `glih-backend/src/glih_backend/api/auth_utils.py`

```python
# JWT secret enforcement (production blocks startup if missing)
_JWT_SECRET_RAW = os.getenv("JWT_SECRET", "")
_GLIH_ENV       = os.getenv("GLIH_ENV", "development")

if not _JWT_SECRET_RAW:
    if _GLIH_ENV == "production":
        raise RuntimeError(
            "JWT_SECRET env var is required in production. Set it before starting."
        )
    # Dev fallback — safe to use locally
    _JWT_SECRET_RAW = "glih-dev-only-insecure-secret-do-not-use-in-production"
    logger.warning("JWT_SECRET not set — using insecure dev default.")

if len(_JWT_SECRET_RAW) < 32:
    logger.warning("JWT_SECRET is shorter than 32 characters — use a longer secret.")

JWT_SECRET_KEY = _JWT_SECRET_RAW
```

**Why this matters:**
- Without this, deploying to production without setting `JWT_SECRET` would use a known public default. Any attacker with the source code can forge admin tokens.
- Hard failure in production is intentional — better to not start than to start insecurely.

### Token Configuration

| Setting | Default | Env Var | Recommendation |
|---------|---------|---------|----------------|
| Access token TTL | 60 min | `JWT_ACCESS_EXPIRE_MINUTES` | 15 min in prod |
| Refresh token TTL | 7 days | `JWT_REFRESH_EXPIRE_DAYS` | 7 days max |
| Algorithm | HS256 | (hardcoded) | RS256 for multi-service |

### How to Generate a Secure JWT Secret

```bash
# Linux/macOS
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Windows PowerShell
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Example output (use this as JWT_SECRET in .env):
# Xk9mP2vN7qL4rT8wA3bE6hF1jG5cD0yI
```

### Verify JWT Security

```bash
# 1. Start with no JWT_SECRET and GLIH_ENV=production — should fail
GLIH_ENV=production uvicorn glih_backend.api.main:app
# Expected: RuntimeError: JWT_SECRET env var is required in production.

# 2. Start with JWT_SECRET set — should succeed
JWT_SECRET=your-64-char-secret GLIH_ENV=production uvicorn glih_backend.api.main:app
# Expected: Uvicorn starts normally
```

---

## 4. Password Security (bcrypt)

### What Changed

**File:** `glih-backend/src/glih_backend/dispatchers.py`

```python
# Before (VULNERABLE — SHA-256 is fast, making brute-force trivial):
import hashlib
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# After (SECURE — bcrypt with cost factor 12, ~100ms per hash):
from passlib.context import CryptContext
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:  # Prevents login when admin password not configured
        return False
    return _pwd_ctx.verify(password, password_hash)
```

**Why bcrypt over SHA-256:**
- SHA-256 is designed to be fast — can test billions of passwords/second with a GPU
- bcrypt is designed to be slow — ~100ms per check, making brute-force infeasible
- bcrypt includes a salt automatically — no rainbow table attacks

### Admin Password Setup

```bash
# In .env (DO NOT commit this file):
DISPATCHER_ADMIN_PASSWORD=your-secure-admin-password-here

# Generate a strong password:
python -c "import secrets, string; chars=string.ascii_letters+string.digits+'!@#$'; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

**If `DISPATCHER_ADMIN_PASSWORD` is not set:**
- The system logs a warning at startup
- Admin login returns `False` for any password attempt (account disabled)
- No exception — this is intentional fail-safe behavior

---

## 5. File Upload Security

### What Changed

**File:** `glih-backend/src/glih_backend/api/main.py`

```python
_MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".md"}
_PDF_MAGIC = b"%PDF"

@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), ...):
    # 1. Check file extension
    suffix = pathlib.Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{suffix}' not allowed")

    # 2. Read and check file size
    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds {_MAX_UPLOAD_BYTES // 1024 // 1024} MB limit")

    # 3. Verify PDF magic bytes (prevent disguised files)
    if suffix == ".pdf" and not data.startswith(_PDF_MAGIC):
        raise HTTPException(400, "File does not appear to be a valid PDF")
```

**Why magic bytes matter:**
- A file named `malware.exe` renamed to `report.pdf` will fail the magic byte check
- Extension-only checking is trivially bypassed by renaming the file
- Real PDFs always start with `%PDF-1.` bytes

**Verify with a test:**
```bash
# Test: Upload a non-PDF disguised as PDF
echo "this is not a pdf" > fake.pdf
curl -X POST http://localhost:9001/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@fake.pdf"
# Expected: {"detail": "File does not appear to be a valid PDF"} ✅

# Test: Upload oversized file (>20MB)
dd if=/dev/zero bs=1M count=25 | base64 > big.txt
curl -X POST http://localhost:9001/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@big.txt"
# Expected: {"detail": "File exceeds 20 MB limit"} ✅
```

---

## 6. Rate Limiting (Brute-Force Protection)

### What Changed

**File:** `glih-backend/src/glih_backend/api/main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Applied to sensitive endpoints:
@app.post("/auth/login")
@limiter.limit("10/minute")     # Max 10 login attempts per minute per IP
async def login(request: Request, ...):

@app.post("/auth/register")
@limiter.limit("5/minute")      # Max 5 registrations per minute per IP

@app.post("/query")
@limiter.limit("30/minute")     # Max 30 queries per minute per IP

@app.post("/agents/anomaly")
@limiter.limit("20/minute")     # Max 20 agent calls per minute per IP
```

**Why rate limiting matters:**
- Without it, an attacker can try millions of passwords against `/auth/login` with no delay
- Bot accounts can abuse LLM endpoints, causing massive OpenAI API costs
- Rate limits are per-IP — legitimate users are unaffected

### Configure via Environment Variables

```bash
# In .env:
RATE_LIMIT_QUERY=30/minute
RATE_LIMIT_AGENTS=20/minute
RATE_LIMIT_INGEST=10/minute
```

**Verify:**
```bash
# Hit login 11 times rapidly — 11th should be blocked
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:9001/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
# Expected: 200 200 200 ... 429 (on 11th) ✅
```

---

## 7. HTTP Security Headers

### What Changed

**File:** `glih-backend/src/glih_backend/api/main.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        if os.getenv("GLIH_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**What each header does:**

| Header | What It Prevents |
|--------|-----------------|
| `X-Content-Type-Options: nosniff` | Browser won't guess content type — prevents MIME-type confusion attacks |
| `X-Frame-Options: DENY` | Page can't be embedded in iframes — prevents clickjacking |
| `X-XSS-Protection: 1; mode=block` | Legacy XSS filter in older browsers |
| `Referrer-Policy` | Doesn't leak full URL to third parties |
| `Permissions-Policy` | Blocks camera/mic access from page scripts |
| `Strict-Transport-Security` | Forces HTTPS for 1 year (production only — not dev) |

**Verify:**
```bash
curl -I http://localhost:9001/health
# Expected headers present:
# x-content-type-options: nosniff
# x-frame-options: DENY
# x-xss-protection: 1; mode=block
```

---

## 8. CORS Hardening

### What Changed

**File:** `glih-backend/src/glih_backend/api/main.py`

```python
# Before (DANGEROUS — any website can call your API):
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# After (production-safe):
_CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(CORSMiddleware,
    allow_origins=[o.strip() for o in _CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

**Why wildcard CORS is dangerous:**
- `allow_origins=["*"]` means any website on the internet can make authenticated requests to your API using a logged-in user's browser session
- This enables Cross-Site Request Forgery (CSRF) attacks
- Example: A malicious site embeds `fetch("https://your-api.com/delete-all-data", {credentials: "include"})`

**Configure for production:**
```bash
# In .env:
CORS_ORIGINS=https://glih.yourcompany.com,https://app.glih.io
```

---

## 9. TLS & Transport Security

### Why TLS is Required

All traffic in production must use HTTPS. Without it:
- Passwords and JWT tokens are visible in plaintext on the network
- Man-in-the-middle attackers can intercept and replay requests

### Nginx TLS Termination (Recommended Setup)

```nginx
# /etc/nginx/sites-available/glih
server {
    listen 80;
    server_name glih.yourcompany.com;
    return 301 https://$server_name$request_uri;  # Force HTTPS
}

server {
    listen 443 ssl http2;
    server_name glih.yourcompany.com;

    # SSL certificates (use Let's Encrypt — free)
    ssl_certificate     /etc/letsencrypt/live/glih.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/glih.yourcompany.com/privkey.pem;

    # Strong TLS settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Proxy to backend
    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Get a free certificate:**
```bash
certbot --nginx -d glih.yourcompany.com
```

---

## 10. Secrets Management

### Never Commit Secrets

`.gitignore` should include:
```
.env
*.env
.env.local
.env.production
```

### Required Environment Variables for Production

| Variable | Purpose | How to Generate |
|----------|---------|-----------------|
| `JWT_SECRET` | Signs all JWT tokens | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DISPATCHER_ADMIN_PASSWORD` | Admin login for dispatcher panel | Strong random password |
| `OPENAI_API_KEY` | GPT-4o for agents | From platform.openai.com |
| `SENTRY_DSN` | Error tracking | From sentry.io |
| `LANGFUSE_SECRET_KEY` | LLM observability | From cloud.langfuse.com |

### Cloud Secrets Management

For Kubernetes deployments, secrets are managed by cloud secret stores. See `deploy/aws/main.tf`, `deploy/gcp/main.tf`, `deploy/azure/main.tf` for the Terraform configuration that provisions:

- **AWS:** Secrets Manager → injected as env vars via External Secrets Operator
- **GCP:** Secret Manager → Workload Identity-based access
- **Azure:** Key Vault → Managed Identity access

**Never put real secrets in Terraform files** — use the `ignore_changes` lifecycle block and populate via the cloud console or CI pipeline.

---

## 11. Dependency Security

### Scan for Known Vulnerabilities

```bash
# Install pip-audit
pip install pip-audit

# Scan glih-backend dependencies
cd glih-backend
pip-audit

# Expected output: "No known vulnerabilities found" or a list to remediate
```

### Keep Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update a specific package
pip install --upgrade slowapi

# Update pyproject.toml version pin after testing:
# slowapi>=0.1.9   →  slowapi>=0.1.12
```

### Regular Security Scan Schedule

| Frequency | Action |
|-----------|--------|
| Every PR | `pip-audit` in CI (add to GitHub Actions) |
| Weekly | `pip list --outdated` review |
| Monthly | Review OWASP Top 10 for new guidance |

---

## 12. Penetration Testing Checklist

Run these tests against your staging environment before every production deployment.

### Authentication Tests

```bash
BASE=http://localhost:9001

# Test 1: Login with wrong password
curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@glih.ops","password":"wrongpassword"}'
# Expected: {"detail": "Invalid credentials"} (not which field is wrong)

# Test 2: Access protected endpoint without token
curl -s $BASE/agents/anomaly
# Expected: {"detail": "Not authenticated"}

# Test 3: Access protected endpoint with expired/forged token
curl -s -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrIn0.forged" \
  $BASE/agents/anomaly
# Expected: {"detail": "Invalid access token"}

# Test 4: Brute-force login — should get 429 after 10 attempts
for i in {1..12}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST $BASE/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@glih.ops","password":"wrong"}')
  echo "Attempt $i: HTTP $STATUS"
done
# Expected: First 10 = 401, attempts 11+ = 429
```

### File Upload Tests

```bash
# Test 5: Upload a file with disallowed extension
curl -s -X POST $BASE/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@malware.exe"
# Expected: {"detail": "File type '.exe' not allowed"}

# Test 6: Upload oversized file
python -c "open('big.txt','wb').write(b'A'*25*1024*1024)"
curl -s -X POST $BASE/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@big.txt"
# Expected: {"detail": "File exceeds 20 MB limit"}

# Test 7: Upload fake PDF
echo "I am not a PDF" > fake.pdf
curl -s -X POST $BASE/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@fake.pdf"
# Expected: {"detail": "File does not appear to be a valid PDF"}
```

### Security Headers Test

```bash
# Test 8: Verify security headers present
curl -I $BASE/health | grep -E "x-frame|x-content|x-xss|referrer"
# Expected: All 4 headers present

# Test 9: CORS rejection from unknown origin
curl -s -H "Origin: https://evil-site.com" \
  -H "Authorization: Bearer $TOKEN" \
  $BASE/query
# Expected: No "Access-Control-Allow-Origin: https://evil-site.com" in response
```

### Injection Tests

```bash
# Test 10: SQL injection attempt in query
curl -s -X POST $BASE/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "OR 1=1; DROP TABLE users; --"}'
# Expected: Normal response (no SQL — ChromaDB used), no 500 error

# Test 11: Path traversal in file name
curl -s -X POST $BASE/ingest/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@../../../etc/passwd;filename=../../etc/passwd"
# Expected: File rejected or sanitized
```

---

## 13. Security Go/No-Go Checklist

Complete **all Critical and High items** before production deployment.

### Critical (Blockers — Must Pass)

- [ ] `JWT_SECRET` set to 64+ char random string in production `.env`
- [ ] `DISPATCHER_ADMIN_PASSWORD` set in production `.env`
- [ ] `GLIH_ENV=production` set (triggers hard failures for missing secrets)
- [ ] Default admin password has been changed post-deploy
- [ ] HTTPS configured with valid TLS certificate (not self-signed)
- [ ] `.env` file not committed to git (`git log --all -- .env` shows nothing)

### High (Required Before Launch)

- [ ] `CORS_ORIGINS` set to exact production domain(s) (no wildcard)
- [ ] Rate limiting tested — login endpoint returns 429 after 10 attempts
- [ ] File upload rejects `.exe`, `.sh`, `.js` extensions
- [ ] File upload rejects fake PDFs (magic byte check passes)
- [ ] `pip-audit` shows no known vulnerabilities
- [ ] All agent endpoints return 401 without Authorization header
- [ ] Security headers present in curl output

### Medium (Complete Within 30 Days of Launch)

- [ ] `/debug/bm25` endpoint protected with `require_admin` dependency
- [ ] `/config` endpoint protected with `require_admin` dependency
- [ ] Auth event logging implemented (failed logins, password changes)
- [ ] Sentry DSN configured and test error visible in dashboard
- [ ] Bare `except:` clauses replaced with specific exception types

### Low (Next Sprint)

- [ ] Refresh tokens stored in Redis with TTL enforcement
- [ ] Refresh token rotation implemented (invalidate on use)
- [ ] Request ID propagation for distributed tracing
- [ ] URL ingest endpoint restricted to allowlisted domains

---

## Related Documents

- [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) — Full production deployment guide
- [.env.example](./.env.example) — All environment variables with descriptions
- `deploy/aws/main.tf` — AWS Secrets Manager configuration
- `deploy/gcp/main.tf` — GCP Secret Manager configuration
- `deploy/azure/main.tf` — Azure Key Vault configuration

---

*For questions or to report a security issue, contact the platform team through internal channels.*
