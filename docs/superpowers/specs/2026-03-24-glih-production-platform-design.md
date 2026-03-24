# GLIH Production Platform — Design Specification

**Date:** 2026-03-24
**Status:** Approved
**Project:** GenAI Logistics Intelligence Hub (GLIH)
**Target:** Cold chain logistics operations — production-grade platform

---

## 1. Problem Statement

The existing GLIH codebase has a solid RAG backend and four well-structured AI agents (`AnomalyResponder`, `RouteAdvisor`, `CustomerNotifier`, `OpsSummarizer`) but they are completely disconnected. Agents accept `vector_search_fn` and `llm_generate_fn` as callbacks, but nothing in the system ever passes real values — every agent run executes with `None` callbacks, making them useless. All data is hardcoded/simulated. There is no frontend beyond a basic Streamlit prototype, no authentication, no observability, and no deployment story.

This specification defines the production-grade platform that:
1. Wires the existing agents to the real RAG + LLM providers via a new `api/agents.py` router
2. Adds a per-connection Demo/Real toggle (WMS, IoT, Docs) so the platform runs entirely on demo data today and switches to real integrations when client-approved
3. Replaces the Streamlit UI with a production Next.js 14 frontend
4. Adds authentication (JWT + OAuth2 + API keys), observability (Langfuse + Locust), database migrations, and full multi-cloud deployment

---

## 2. Architecture Decision

**Chosen approach:** Modular Monolith + MCP Connector Layer

A single FastAPI backend with clean internal module boundaries. Agents, connectors, auth, and streaming are separate modules within one deployable service. MCP servers run as separate lightweight FastAPI services. Any backend module can be extracted to a microservice later without rewriting agent or connector code.

**Rationale:** Microservices would add 8+ services to orchestrate before a single agent runs. The modular monolith gives full microservices-grade internal structure at monolith deployment simplicity. The connector abstraction ensures the Demo/Real split is a database flag — not a code branch.

---

## 3. Service Inventory & Port Assignments

All services run in the 9000–9009 range to avoid conflicts with existing applications. There are **10 services** total in `docker-compose.yml`.

| Port | Service | Stack | Scope |
|------|---------|-------|-------|
| 9000 | Next.js frontend | Next.js 14, App Router | Always |
| 9001 | FastAPI backend | Python 3.11, async | Always |
| 9002 | WMS MCP server | FastAPI (re-ported) | Always |
| 9003 | IoT MCP server | FastAPI (re-ported) | Always |
| 9004 | Docs MCP server | FastAPI (re-ported) | Always |
| 9005 | MQTT broker | Mosquitto | Always |
| 9006 | PostgreSQL | postgres:16 | Always |
| 9007 | Redis | redis:7 | Always |
| 9008 | Langfuse web UI | `langfuse/langfuse` image | Dev only |
| 9009 | Locust web UI | `locustio/locust` | Dev only |

**Langfuse in development:** The `langfuse/langfuse` Docker image bundles its own internal PostgreSQL on a non-exposed port — it does **not** share port 9006. Port 9008 exposes only the Langfuse web interface.

**Langfuse in production:** The `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` env vars point to `cloud.langfuse.com`. The Langfuse container is excluded from `docker-compose.prod.yml`. No code changes required to switch.

**Locust** is a dev/test-only service. It is excluded from `docker-compose.prod.yml`.

---

## 4. Database Schema & Migrations

### Migration Strategy

Alembic manages all schema migrations. The directory lives at `glih-backend/alembic/`. On `make dev`, the startup sequence runs `alembic upgrade head` before the FastAPI process starts. `make migrate` runs migrations manually.

```
glih-backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_users_and_auth.py
│       ├── 002_connector_settings.py
│       ├── 003_audit_log_and_agent_runs.py  # audit_log + agent_runs tables
│       └── 004_seed_test_users.py           # dev only, gated on APP_ENV=development
└── alembic.ini
```

### Core Tables

```sql
-- Users and RBAC
CREATE TABLE users (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email        VARCHAR(255) UNIQUE NOT NULL,
  display_name VARCHAR(255),
  password_hash VARCHAR(255),           -- NULL for OAuth-only accounts
  role         VARCHAR(32) NOT NULL DEFAULT 'viewer',  -- admin|ops-manager|analyst|viewer
  oauth_provider VARCHAR(32),           -- 'entra' | 'google' | NULL
  oauth_subject  VARCHAR(255),          -- provider's sub claim
  force_password_change BOOLEAN DEFAULT false,
  created_at   TIMESTAMPTZ DEFAULT now(),
  updated_at   TIMESTAMPTZ DEFAULT now()
);

-- API Keys
CREATE TABLE api_keys (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name         VARCHAR(100) NOT NULL,
  key_hash     VARCHAR(255) NOT NULL,   -- bcrypt hash; shown to user once
  scopes       TEXT[] NOT NULL DEFAULT '{}',  -- e.g. ['iot:ingest', 'agents:run']
  last_used_at TIMESTAMPTZ,
  expires_at   TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Per-connection Demo/Real toggle
CREATE TABLE connector_settings (
  connection_id   VARCHAR(32) PRIMARY KEY,  -- 'wms' | 'iot' | 'docs'
  connector_mode  VARCHAR(8)  NOT NULL DEFAULT 'demo',  -- 'demo' | 'real'
  config_json     JSONB,                    -- endpoint URLs, env var refs for credentials
  updated_by      UUID REFERENCES users(id),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Seed on first run
INSERT INTO connector_settings (connection_id, connector_mode)
VALUES ('wms', 'demo'), ('iot', 'demo'), ('docs', 'demo')
ON CONFLICT DO NOTHING;

-- Audit log
CREATE TABLE audit_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES users(id),
  action       VARCHAR(100) NOT NULL,   -- e.g. 'anomaly_agent', 'connector_toggle'
  resource     VARCHAR(255),
  payload      JSONB,
  result       JSONB,
  ip_address   INET,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Agent execution history
CREATE TABLE agent_runs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES users(id),
  agent_name   VARCHAR(50) NOT NULL,    -- anomaly|route|notify|ops-summary
  trace_id     VARCHAR(100),            -- Langfuse trace ID
  input        JSONB NOT NULL,
  output       JSONB,
  status       VARCHAR(20) DEFAULT 'pending',  -- pending|running|success|error
  duration_ms  INTEGER,
  created_at   TIMESTAMPTZ DEFAULT now()
);
```

---

## 5. Demo / Real Connection Switching

### Per-Domain Connector Interfaces

Three separate abstract base classes — one per integration domain:

```python
# connectors/base.py
class BaseWmsConnector(ABC):
    @abstractmethod
    async def get_shipment(self, shipment_id: str) -> dict: ...
    @abstractmethod
    async def list_shipments(self, filters: dict) -> list[dict]: ...
    @abstractmethod
    async def get_shipment_events(self, shipment_id: str) -> list[dict]: ...

class BaseIotConnector(ABC):
    @abstractmethod
    async def get_latest_reading(self, device_id: str) -> dict: ...
    @abstractmethod
    async def get_gps_location(self, shipment_id: str) -> dict: ...
    @abstractmethod
    async def subscribe_to_stream(self, callback: Callable) -> None: ...

class BaseDocsConnector(ABC):
    @abstractmethod
    async def get_document(self, doc_id: str) -> dict: ...
    @abstractmethod
    async def search_documents(self, query: str, limit: int = 5) -> list[dict]: ...
    @abstractmethod
    async def get_sop(self, product_type: str, event_type: str) -> str: ...
```

### Connector Factory

```python
# connectors/factory.py
async def get_wms_connector(db: AsyncSession = Depends(get_db)) -> BaseWmsConnector:
    row = await db.get(ConnectorSettings, "wms")
    if row.connector_mode == "real":
        return RealWmsConnector(config=row.config_json)
    return DemoWmsConnector()          # calls MCP :9002

async def get_iot_connector(db: AsyncSession = Depends(get_db)) -> BaseIotConnector:
    row = await db.get(ConnectorSettings, "iot")
    if row.connector_mode == "real":
        return RealIotConnector(mqtt_url=row.config_json["mqtt_url"])
    return DemoIotConnector()          # reads from Redis simulator stream

async def get_docs_connector(db: AsyncSession = Depends(get_db)) -> BaseDocsConnector:
    row = await db.get(ConnectorSettings, "docs")
    if row.connector_mode == "real":
        return RealDocsConnector(config=row.config_json)
    return DemoDocsConnector()         # calls MCP :9004
```

Factory functions are FastAPI dependencies — injected into route handlers via `Depends()`.

### Toggle Source of Truth

`connector_settings.connector_mode` in PostgreSQL. Changed via `PATCH /api/settings/connectors/{connection_id}` (requires `ops-manager` role or above). Cached in Redis for 60 seconds per connection to avoid a DB query on every request.

---

## 6. The Critical Agent Wiring Fix

### `providers.py` — Existing Module

`providers.py` exports three classes: `EmbeddingsProvider`, `VectorStore`, and `LLMProvider`. All three are instantiated as module-level singletons at application startup in `main.py`:

```python
# main.py (startup)
_emb = make_embeddings_provider(cfg)
_vs  = make_vector_store(cfg)
_llm = make_llm_provider(cfg)
```

These singletons are imported directly by `api/agents.py` (not injected as FastAPI dependencies — they are stateless configuration objects that do not change at request time).

### Langfuse Tracing — `new_trace()` Helper

```python
# observability/tracing.py
from langfuse import Langfuse

_langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,   # http://localhost:9008 in dev, cloud.langfuse.com in prod
)

def new_trace(user_id: str, agent_name: str) -> str:
    """Create a Langfuse trace and return its trace_id string."""
    trace = _langfuse.trace(
        name=agent_name,
        user_id=user_id,
        metadata={"platform": "glih"},
    )
    return trace.id   # UUID string passed to llm.generate()

def flush_traces() -> None:
    """Call on application shutdown to flush buffered events."""
    _langfuse.flush()
```

`LLMProvider.generate()` accepts an optional `trace_id: str` parameter. When provided, it wraps the LLM call in a Langfuse generation event capturing prompt, response, token counts, and cost. This is added to the existing `providers.py` without changing any external interface.

### All Four Agent Endpoint Signatures

```python
# api/agents.py

# 1 — AnomalyResponder
class AnomalyEvent(BaseModel):
    shipment_id: str                 # e.g. "CHI-ATL-2025-089"
    temperature_c: float
    threshold_min_c: float
    threshold_max_c: float
    location: str
    breach_duration_min: int

@router.post("/agents/anomaly", response_model=AgentRunResponse)
async def run_anomaly_agent(
    event: AnomalyEvent,
    user=Depends(require_auth),
    wms=Depends(get_wms_connector),
):

# 2 — RouteAdvisor
class RouteRequest(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    product_type: str
    start_time: datetime             # ISO8601
    constraints: dict = {}

@router.post("/agents/route", response_model=AgentRunResponse)
async def run_route_agent(
    request: RouteRequest,
    user=Depends(require_auth),
    wms=Depends(get_wms_connector),
):

# 3 — CustomerNotifier
class NotifyRequest(BaseModel):
    shipment_id: str
    customer_id: str                 # e.g. "CUST-001"
    notification_type: str           # delay|arrival|issue|temperature_breach|delivered
    severity: str = "low"            # low|medium|high|critical
    details: dict = {}

@router.post("/agents/notify", response_model=AgentRunResponse)
async def run_notify_agent(
    request: NotifyRequest,
    user=Depends(require_auth),
    wms=Depends(get_wms_connector),    # fetch shipment + customer data
    docs=Depends(get_docs_connector),  # retrieve notification SOPs if needed
):

# 4 — OpsSummarizer
class OpsSummaryRequest(BaseModel):
    time_window: str = "24h"         # 8h|24h|7d
    facility: str = "all"

@router.post("/agents/ops-summary", response_model=AgentRunResponse)
async def run_ops_summary_agent(
    request: OpsSummaryRequest,
    user=Depends(require_auth),
    wms=Depends(get_wms_connector),    # fetch shipment events for the time window
    iot=Depends(get_iot_connector),    # fetch sensor history + incident data
):

# Shared response model
class AgentRunResponse(BaseModel):
    run_id: str                      # UUID from agent_runs table
    agent_name: str
    status: str                      # success|error
    result: dict
    trace_id: str                    # Langfuse trace ID
    duration_ms: int
```

Each handler follows this pattern:
1. Create Langfuse trace via `new_trace(user.id, agent_name)`
2. Fetch live data from connector (`wms.get_shipment(...)` etc.)
3. Build `vector_search_fn` and `llm_generate_fn` closures referencing `_vs`, `_emb`, `_llm`, and `trace_id`
4. Call the agent's main method
5. Publish result to SSE stream via Redis pub/sub
6. Write to `agent_runs` and `audit_log` tables
7. Return `AgentRunResponse`

---

## 7. Real-Time Data Pipeline

**Frontend dashboard updates:** Server-Sent Events (SSE) via `/api/stream/*` endpoints. The frontend `useSSE` hook connects and reconnects automatically on disconnect.

**Production IoT ingestion:** MQTT broker on port 9005 (Mosquitto). The `RealIotConnector` subscribes to sensor topics (e.g., `lineage/truck/{shipment_id}/temp`) and re-publishes normalised readings to Redis pub/sub channel `glih:stream:sensors`.

**Demo IoT simulator:** A FastAPI background task (`demo/simulator.py`) activates when `IotConnector` is in demo mode. It publishes to the same `glih:stream:sensors` Redis channel — the SSE endpoint is identical in both modes.

Simulated outputs per tick (every 5 seconds):
- Temperature drift: ±0.3°C from baseline, clipped to product thresholds
- GPS position: incremental movement along a pre-defined route polygon
- Door events: random open/close at configurable probability
- Auto-breach: injected every ~5 minutes on one random active shipment

---

## 8. Authentication

### Layer 1 — JWT (always active)

- Tokens issued as httpOnly `SameSite=Strict` cookies (not `Authorization` header) to prevent XSS token theft
- Access token: 15 minutes. Refresh token: 7 days, stored in `redis` with `jti` claim for revocation
- `POST /auth/login` → `{access_token, refresh_token}` in cookies
- `POST /auth/refresh` → new access token (reads refresh token from cookie)
- `POST /auth/logout` → revokes refresh token in Redis, clears cookies

### Layer 2 — OAuth2 SSO (feature-flagged via `OAUTH_ENABLED=true`)

**Flow for Microsoft Entra ID (same pattern for Google):**

```
1. Browser: GET /auth/oauth/entra
2. Backend: generate state (UUID, stored in Redis 10 min), redirect to Entra /authorize
3. Entra: user authenticates, redirects to GET /auth/oauth/callback?code=...&state=...
4. Backend: verify state from Redis, exchange code for id_token via Entra /token endpoint
5. Backend: decode id_token claims (sub, email, name)
6. Backend: upsert user row (INSERT ... ON CONFLICT (oauth_subject) DO UPDATE)
7. Backend: issue JWT cookies (same as password login), redirect to /dashboard
```

State parameter stored in Redis with 10-minute TTL to prevent CSRF. OAuth client credentials (`OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`) in `.env` — never committed.

### Layer 3 — API Keys

```python
# Scope definitions
API_KEY_SCOPES = [
    "iot:ingest",      # publish sensor readings via POST /api/stream/ingest
    "agents:run",      # call agent endpoints
    "rag:query",       # query only
    "rag:ingest",      # ingest documents
    "admin",           # all operations
]
```

FastAPI dependency:
```python
def require_scope(scope: str):
    async def _check(api_key: str = Header(None, alias="X-API-Key"), db=Depends(get_db)):
        key_row = await verify_api_key(api_key, db)        # lookup by hash
        if scope not in key_row.scopes:
            raise HTTPException(403, "Insufficient scope")
        return key_row
    return _check
```

### RBAC Roles

| Role | Permissions |
|---|---|
| `admin` | All actions including user management, connector toggles, API key management |
| `ops-manager` | Run agents, view all data, toggle connectors, export reports |
| `analyst` | View all data, run agents, query RAG |
| `viewer` | View dashboard and shipments only |

---

## 9. Observability

### Langfuse (port 9008 — dev only)

Every LLM call carries a `trace_id` generated by `new_trace()`. The trace captures:
- User who triggered the call (linked to Langfuse user profile)
- Agent name and input payload
- RAG retrieval: documents retrieved, cosine distances, collection queried
- LLM prompt and full response text
- Token usage (prompt + completion) and estimated cost
- End-to-end latency per agent run

**Viewing traces:** `http://localhost:9008` in dev. In production, `https://cloud.langfuse.com`.

Langfuse events are buffered in-process and flushed on application shutdown via `flush_traces()` registered in FastAPI's `@app.on_event("shutdown")` handler.

### Locust (port 9009 — dev only)

Pre-built scenarios in `tests/load/locustfile.py`. All scenarios authenticate via `on_start()` using a seeded test user (`locust@glih.test` / `LocustTest123!`) created by `alembic/versions/003_seed_test_users.py` (active only when `APP_ENV=development`).

| Scenario | Locust class | Users | Duration | Pass criteria |
|---|---|---|---|---|
| Normal ops | `NormalOpsUser` | 20 | 2 min | p95 < 3s, 0 errors |
| Spike | `SpikeUser` | 100 (30s ramp) | 3 min | p95 < 8s, error rate < 1% |
| Soak | `SoakUser` | 50 | 10 min | No memory growth > 50 MB |
| WebSocket stress | `SSEUser` | 200 connections | 5 min | No dropped connections |
| Agent concurrent | `AgentConcurrentUser` | 50 | 2 min | p95 < 5s per agent call |
| Auth load | `AuthLoadUser` | 100 | 2 min | p95 < 500ms for token ops |

`make test-load` starts Locust in headless mode and exits non-zero on failure.

---

## 10. Frontend — Next.js 14

**Theme:** Dark Ops Command Centre — `#070d1a` background, `#22d3ee` teal accents, `#f59e0b` amber alerts, `#10b981` green compliance indicators.

### Pages

| Route | Purpose | Min role |
|---|---|---|
| `/(auth)/login` | JWT login + OAuth2 buttons | Public |
| `/dashboard` | Live KPIs, sensor feed, agent activity, alert ticker (SSE) | `viewer` |
| `/agents` | Agent runner + demo presets + run history | `analyst` |
| `/shipments` | Searchable table, detail modal with temp history chart | `viewer` |
| `/alerts` | Alert list, SOP citations, resolution status | `viewer` |
| `/analytics` | Recharts KPI trends, export PDF/CSV | `analyst` |
| `/documents` | Drag-drop ingest, RAG query, SOP viewer | `analyst` |
| `/settings` | Connector Demo/Real toggles, LLM selection, notifications | `ops-manager` |
| `/admin` | Users, RBAC, API keys, audit log, Langfuse link, system health | `admin` |

### Live Data

`useSSE(endpoint)` custom hook (in `lib/useSSE.ts`) connects to `/api/stream/{sensors|alerts|shipments}`. Reconnects with exponential backoff. Updates React state directly — no polling, no full page reload.

---

## 11. Demo Scenarios — Pre-Wired Fixture Data

All six scenarios are selectable from the Agents page under "Demo Presets." Payloads are defined in `glih-backend/src/glih_backend/demo/scenarios.py`.

### Scenario 1 — Temperature Breach Response
```python
SCENARIO_1_ANOMALY = AnomalyEvent(
    shipment_id="DEMO-SHP-CHI-ATL-001",
    temperature_c=5.2,
    threshold_min_c=0.0,
    threshold_max_c=4.0,
    location="Atlanta Cold Hub, GA",
    breach_duration_min=22,
)
SCENARIO_1_NOTIFY = NotifyRequest(
    shipment_id="DEMO-SHP-CHI-ATL-001",
    customer_id="CUST-001",          # Whole Foods
    notification_type="temperature_breach",
    severity="high",
    details={"temperature_c": 5.2, "expected_range": "0–4°C"},
)
```

### Scenario 2 — Route Optimisation Under Risk
```python
SCENARIO_2 = RouteRequest(
    shipment_id="DEMO-SHP-TX-CHI-001",
    origin="Dallas, TX",
    destination="Chicago, IL",
    product_type="Seafood",
    start_time=datetime.utcnow() - timedelta(hours=10),
    constraints={"max_transit_hours": 16},
)
```

### Scenario 3 — Shift Handoff Report
```python
SCENARIO_3 = OpsSummaryRequest(time_window="24h", facility="Chicago")
```

### Scenario 4 — SOP Natural Language Query
```python
SCENARIO_4_QUERY = "What are the required actions if seafood exceeds 4°C for more than 30 minutes?"
SCENARIO_4_COLLECTION = "lineage-sops"
```

### Scenario 5 — Live IoT Simulator
Activated automatically when `IotConnector` is in demo mode. No manual trigger — the dashboard is always live with drifting sensor data. A temperature breach fires automatically every ~5 minutes, triggering Scenarios 1+1a (AnomalyResponder → CustomerNotifier) without user interaction.

### Scenario 6 — Locust Load Test
```bash
make test-load SCENARIO=normal   # or spike|soak|sse|agent|auth
# Opens results in Locust web UI at localhost:9009
```

---

## 12. Cloud Deployment

### Local Development
```bash
cp .env.example .env        # configure API keys
make dev                    # alembic upgrade head → start all 10 services
# open localhost:9000
```

`make dev` sequence:
1. `docker-compose up -d postgres redis mqtt` (data layer first)
2. `docker-compose run --rm backend alembic upgrade head` (migrations)
3. `docker-compose up -d` (all remaining services)

### CI/CD (GitHub Actions)

- `ci.yml` — triggers on every PR: `pytest --cov`, `ruff check`, `mypy`, `npm run build`, `make test-load SCENARIO=normal`
- `deploy.yml` — triggers on merge to `main`: builds Docker images, tags with git SHA, pushes to registry (ECR / Artifact Registry / ACR depending on `CLOUD_TARGET` env var)

### Cloud Terraform

```bash
make deploy-aws     # → deploy/aws/  : terraform init + plan + apply + kubectl apply
make deploy-gcp     # → deploy/gcp/  : terraform init + plan + apply + kubectl apply
make deploy-azure   # → deploy/azure/: terraform init + plan + apply + kubectl apply
```

| Cloud | Kubernetes | Database | Cache | Container Registry | Ingress |
|---|---|---|---|---|---|
| AWS | EKS (managed node group) | RDS PostgreSQL 16 | ElastiCache Redis | ECR | ALB + ACM TLS |
| GCP | GKE Autopilot | Cloud SQL PostgreSQL 16 | Memorystore Redis | Artifact Registry | Cloud LB + managed cert |
| Azure | AKS (system node pool) | Azure Database for PostgreSQL Flex | Azure Cache for Redis | ACR | App Gateway + Key Vault cert |

Terraform state stored in cloud-native backend: S3 (AWS), GCS (GCP), Azure Blob Storage (Azure). Never apply Terraform manually outside of the `make deploy-*` targets — they run `plan` and prompt for confirmation before `apply`.

Shared Kubernetes manifests in `deploy/k8s/`: `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`, `configmap.yaml`, `secrets.yaml` (sealed with `kubeseal`).

---

## 13. File Structure

```
genai_logistic-intelligent-hub/
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml             # 10 services (dev, includes Langfuse + Locust)
├── docker-compose.prod.yml        # 8 services (excludes Langfuse + Locust)
├── Makefile
│
├── glih-frontend/                 # Next.js 14 :9000
│   ├── app/
│   │   ├── (auth)/login/
│   │   ├── dashboard/
│   │   ├── agents/
│   │   ├── shipments/
│   │   ├── alerts/
│   │   ├── analytics/
│   │   ├── documents/
│   │   ├── settings/
│   │   └── admin/
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── LiveSensorFeed.tsx
│   │   ├── TempGauge.tsx
│   │   └── AlertTicker.tsx
│   └── lib/
│       ├── api.ts                 # typed API client
│       ├── useSSE.ts              # SSE hook with reconnect
│       └── auth.ts                # token utils, route guard
│
├── glih-backend/                  # FastAPI :9001
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 001_users_and_auth.py
│   │       ├── 002_connector_settings.py
│   │       ├── 003_audit_log_and_agent_runs.py
│   │       └── 004_seed_test_users.py  # dev only, gated on APP_ENV=development
│   ├── alembic.ini
│   └── src/glih_backend/
│       ├── api/
│       │   ├── rag.py
│       │   ├── agents.py          # NEW — critical wiring
│       │   ├── stream.py          # NEW — SSE endpoints
│       │   └── auth.py            # NEW — JWT + OAuth2 + API keys
│       ├── connectors/
│       │   ├── base.py            # BaseWmsConnector, BaseIotConnector, BaseDocsConnector
│       │   ├── factory.py         # get_wms_connector(), get_iot_connector(), get_docs_connector()
│       │   ├── wms.py             # DemoWmsConnector + RealWmsConnector
│       │   ├── iot.py             # DemoIotConnector + RealIotConnector
│       │   └── docs.py            # DemoDocsConnector + RealDocsConnector
│       ├── demo/
│       │   ├── simulator.py       # IoT background task
│       │   └── scenarios.py       # 6 pre-wired fixture payloads
│       ├── auth/
│       │   ├── jwt.py
│       │   ├── oauth.py
│       │   ├── apikeys.py
│       │   └── rbac.py
│       ├── observability/
│       │   └── tracing.py         # new_trace(), flush_traces(), LangfuseMiddleware
│       ├── models.py              # SQLAlchemy ORM models
│       ├── providers.py           # existing — unchanged
│       └── main.py                # updated: registers all routers + startup/shutdown hooks
│
├── glih-agents/                   # Existing — no changes
├── mcp-servers/                   # Re-ported: wms :9002, iot :9003, docs :9004
│
├── tests/
│   ├── unit/
│   │   ├── test_providers.py
│   │   ├── test_agents.py
│   │   └── test_connectors.py
│   ├── integration/
│   │   ├── test_rag_pipeline.py
│   │   ├── test_agent_endpoints.py
│   │   └── test_connector_toggle.py
│   └── load/
│       └── locustfile.py
│
├── deploy/
│   ├── aws/
│   ├── gcp/
│   ├── azure/
│   ├── k8s/
│   └── scripts/
│       ├── deploy-aws.sh
│       ├── deploy-gcp.sh
│       └── deploy-azure.sh
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 14. CLAUDE.md Conventions Summary

- **Ports:** 9000–9009 exclusively. Document any new service in CLAUDE.md before allocating a port.
- **Startup:** `make dev` starts all services with migrations. Never start services individually.
- **Connector pattern:** All external data flows through a connector. Never hardcode data or bypass via direct MCP HTTP calls outside of `connectors/`.
- **Agent pattern:** Agents never import connectors. Callbacks always injected by `api/agents.py`. Agent classes in `glih-agents/` are not modified.
- **LLM calls:** Every `llm.generate()` call must include a `trace_id` from `new_trace()`. No exceptions.
- **Auth:** All `/api/*` routes require `Depends(require_auth)`. Exceptions: `/api/health`, `/api/auth/login`, `/api/auth/oauth/*`.
- **Migrations:** Schema changes go through Alembic. Never modify the database directly.
- **Testing:** `make test` must pass before any PR. `make test-load SCENARIO=normal` must pass at 20 users.
- **Terraform:** Never `terraform apply` manually. Use `make deploy-{cloud}` which runs plan + prompts.

---

## 15. Non-Goals (Explicitly Out of Scope)

- Native mobile application or push notifications (in-app SSE alerts only; SMTP for email)
- Multi-tenancy — the platform is single-tenant; facility-level isolation is via RBAC roles, not schema separation
- Audit log archival or data retention policies — retention period is operator-configured at the database level; no built-in archival pipeline
- Disaster recovery configuration — cloud-native defaults (RDS automated backups, GCS object versioning, Azure geo-redundancy) are relied upon; no custom DR scripts
- Billing or invoicing system
- Inventory management beyond what the WMS connector provides
- Video / camera feeds from warehouse or vehicle cameras

---

*Spec approved 2026-03-24. Implementation plan to follow.*
