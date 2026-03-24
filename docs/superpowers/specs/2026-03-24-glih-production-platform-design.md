# GLIH Production Platform — Design Specification

**Date:** 2026-03-24
**Status:** Approved
**Project:** GenAI Logistics Intelligence Hub (GLIH)
**Target:** Cold chain logistics operations — production-grade platform

---

## 1. Problem Statement

The existing GLIH codebase has a solid RAG backend and four well-structured AI agents (`AnomalyResponder`, `RouteAdvisor`, `CustomerNotifier`, `OpsSummarizer`) but they are completely disconnected. Agents accept `vector_search_fn` and `llm_generate_fn` as callbacks, but nothing in the system ever passes real values — every agent run executes with `None` callbacks, making them useless. All data is hardcoded/simulated. There is no frontend beyond a basic Streamlit prototype, no authentication, no observability, and no deployment story.

This specification defines the production-grade platform that:
1. Wires the existing agents to the real RAG + LLM providers
2. Adds a per-connection Demo/Real toggle so the platform can run entirely on demo data today and switch to real integrations when approved
3. Replaces the Streamlit UI with a production Next.js frontend
4. Adds authentication, observability (Langfuse), load testing (Locust), and full cloud deployment

---

## 2. Architecture Decision

**Chosen approach:** Modular Monolith + MCP Connector Layer

A single FastAPI backend with clean internal module boundaries. Agents, connectors, auth, and streaming are separate modules within one deployable service. MCP servers run as separate lightweight services. Any backend module can be extracted to a microservice later without rewriting agent or connector code.

**Rationale:** Microservices would add 8+ services to orchestrate before a single agent runs. The monolith gives full microservices-grade internal structure at monolith deployment simplicity. The connector abstraction means the Demo/Real split is a database flag — not a code branch.

---

## 3. Port Assignments

All services run in the 9000–9009 range to avoid conflicts with existing running applications.

| Port | Service | Stack |
|------|---------|-------|
| 9000 | Next.js frontend | Next.js 14, App Router |
| 9001 | FastAPI backend | Python 3.11, async |
| 9002 | WMS MCP server | FastAPI (existing, re-ported) |
| 9003 | IoT MCP server | FastAPI (existing, re-ported) |
| 9004 | Docs MCP server | FastAPI (existing, re-ported) |
| 9005 | MQTT broker | Mosquitto |
| 9006 | PostgreSQL | postgres:16 |
| 9007 | Redis | redis:7 |
| 9008 | Langfuse | Self-hosted (dev), cloud.langfuse.com (prod) |
| 9009 | Locust | Load testing web UI |

---

## 4. Demo / Real Connection Switching

Each of the three external integrations (WMS, IoT, Docs) has an independent Demo/Real toggle stored in PostgreSQL. The toggle is changed via the Settings page (admin or ops-manager role required). No server restart is needed.

### Connector Interface

Each connector implements a common abstract base:

```python
class BaseConnector(ABC):
    @abstractmethod
    async def get_shipment(self, shipment_id: str) -> dict: ...

    @abstractmethod
    async def list_shipments(self, filters: dict) -> list: ...
```

### Toggle Behaviour

| Connection | Demo source | Real source |
|---|---|---|
| WMS | MCP server :9002 (mock shipments) | Real WMS REST API (configurable endpoint) |
| IoT | Built-in simulator (temp drift, GPS) | MQTT broker :9005 subscribing to real sensors |
| Docs | MCP server :9004 (mock SOPs/BOLs) | SharePoint / DMS API (configurable) |

Toggle stored as `connector_mode` per `connection_id` in PostgreSQL. Factory function reads the flag and returns the correct connector implementation at request time.

---

## 5. The Critical Agent Wiring Fix

**Root cause of disconnection:** The existing agent classes are correct but isolated. They never receive real callbacks.

**Fix:** `api/agents.py` is a new FastAPI router that creates real closures from the instantiated providers and injects them when calling each agent. The existing agent classes are not modified.

```python
@router.post("/agents/anomaly")
async def run_anomaly_agent(event: AnomalyEvent, user=Depends(require_auth)):
    # 1. Build real callbacks from providers
    vector_search_fn = lambda q, col, k: rag.search(q, col, k)
    llm_generate_fn  = lambda prompt: llm.generate(prompt, trace_id=new_trace(user))
    # 2. Fetch live data from connector (demo or real)
    shipment = await wms_connector.get_shipment(event.shipment_id)
    # 3. Run agent with real context
    result = agent.respond_to_anomaly({**event.dict(), **shipment}, vector_search_fn, llm_generate_fn)
    # 4. Publish to SSE stream + audit log
    await stream.publish("alerts", result)
    await audit.log(user, "anomaly_agent", event, result)
    return result
```

All four agent endpoints follow the same pattern. The agent classes in `glih-agents/` are preserved exactly as-is.

---

## 6. Real-Time Data Pipeline

**Frontend dashboard updates:** Server-Sent Events (SSE) via `/api/stream/*` endpoints.
**Production IoT ingestion:** MQTT broker on port 9005. The `IotConnector` (real mode) subscribes to sensor topics and re-publishes to Redis pub/sub. The SSE endpoint reads from Redis pub/sub and streams to connected browsers.

**Demo mode IoT simulator:**
A background task (`demo/simulator.py`) runs when IoT connector is in demo mode. It generates:
- Temperature readings with realistic drift (±0.3°C/minute)
- GPS position updates along a pre-defined route
- Door open/close events at simulated stops
- One automatic temperature breach every ~5 minutes

The simulator publishes to the same Redis pub/sub channel as the real MQTT connector — the SSE endpoint and frontend are identical in both modes.

---

## 7. Authentication

Three-layer auth system, all opt-in per deployment:

### Layer 1 — JWT (always active)
- `POST /auth/login` — username/password → access token (15 min) + refresh token (7 days)
- `POST /auth/refresh` — refresh → new access token
- All `/api/*` routes protected except `/api/health` and `/auth/login`
- Tokens stored in httpOnly cookies (not localStorage)

### Layer 2 — OAuth2 SSO (feature-flagged)
- Enabled via `OAUTH_ENABLED=true` in `.env`
- Supports Microsoft Entra ID and Google Workspace
- On first OAuth login, account auto-provisioned with `viewer` role
- Admin can promote role afterwards

### Layer 3 — API Keys (always active)
- Generated per user via `/auth/apikeys`
- Scoped to specific endpoints (e.g., IoT ingest only)
- Used by MCP servers and IoT devices for service-to-service auth
- Stored as bcrypt-hashed values, shown to user once on creation

### RBAC Roles

| Role | Permissions |
|---|---|
| `admin` | All actions including user management, connector toggles, API key management |
| `ops-manager` | Run agents, view all data, toggle connectors, export reports |
| `analyst` | View all data, run agents, query RAG |
| `viewer` | View dashboard and shipments only |

---

## 8. Observability

### Langfuse (port 9008)
Every LLM call carries a `trace_id`. The trace captures:
- User who triggered the call
- Agent name and input event
- RAG retrieval results (documents retrieved, distances)
- LLM prompt and response
- Token usage and cost
- End-to-end latency

Self-hosted via Docker in development. Switch to `cloud.langfuse.com` in production by setting `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` — no code change.

### Locust (port 9009)
Pre-built load test scenarios in `tests/load/locustfile.py`:

| Scenario | Users | Target |
|---|---|---|
| Normal ops | 20 | All 4 agent endpoints + RAG query |
| Spike | 100 (30s ramp) | Agent endpoints + SSE connections |
| Soak | 50 for 10 min | All endpoints, measure memory leak |
| WebSocket stress | 200 SSE connections | Stream stability |
| Agent concurrent | 50 parallel agent runs | Response time < 5s p95 |
| Auth load | 100 login/refresh cycles | Token throughput |

### Structured Logging
All backend logs are JSON with `correlation_id`, `user_id`, `agent_name`, `connector_mode`, and `duration_ms` fields. Compatible with Datadog, CloudWatch, and GCP Logging without modification.

---

## 9. Frontend — Next.js 14

**Theme:** Dark Ops Command Centre — deep navy (`#070d1a`) with teal (`#22d3ee`) accents, amber alerts, green compliance indicators.

### Pages

| Route | Component | Auth required |
|---|---|---|
| `/` | Redirect to `/dashboard` | Yes |
| `/(auth)/login` | Login form + OAuth buttons | No |
| `/dashboard` | Live KPIs, sensor feed, agent activity, alert ticker | `viewer`+ |
| `/agents` | Agent runner with demo presets + history | `analyst`+ |
| `/shipments` | Searchable table + detail modal | `viewer`+ |
| `/alerts` | Alert list with SOP citations + resolution | `viewer`+ |
| `/analytics` | Charts (Recharts), KPI trends, export | `analyst`+ |
| `/documents` | Drag-drop ingest, RAG query, SOP viewer | `analyst`+ |
| `/settings` | Connector toggles, LLM selection, notifications | `ops-manager`+ |
| `/admin` | Users, roles, API keys, audit log, system health | `admin` |

### Live Data
Dashboard uses `useSSE` custom hook connecting to `/api/stream/sensors`, `/api/stream/alerts`, and `/api/stream/shipments`. Reconnects automatically on disconnect. No polling.

---

## 10. Demo Scenarios (Pre-Wired)

All six scenarios are available from the Agents page under "Demo Presets." No manual data entry required.

| # | Name | Agents triggered | Duration |
|---|---|---|---|
| 1 | Temperature Breach Response | AnomalyResponder → CustomerNotifier | ~8s |
| 2 | Route Optimisation Under Risk | RouteAdvisor | ~6s |
| 3 | Shift Handoff Report | OpsSummarizer | ~10s |
| 4 | SOP Natural Language Query | RAG only | ~3s |
| 5 | Live IoT Simulator | Automatic (background) | Continuous |
| 6 | Locust Load Test | Locust → all agents | ~2 min |

---

## 11. Cloud Deployment

### Local Development
```bash
cp .env.example .env        # configure API keys
make dev                    # starts all 10 Docker Compose services
# open localhost:9000
```

### CI/CD (GitHub Actions)
- `ci.yml` — runs on every PR: `pytest`, `ruff`, `mypy`, `npm run build`
- `deploy.yml` — runs on merge to `main`: builds Docker images, pushes to registry

### Cloud Terraform (one command per cloud)
```bash
make deploy-aws     # → deploy/aws/ terraform + kubectl apply
make deploy-gcp     # → deploy/gcp/ terraform + kubectl apply
make deploy-azure   # → deploy/azure/ terraform + kubectl apply
```

| Cloud | Kubernetes | Database | Cache | Registry |
|---|---|---|---|---|
| AWS | EKS + ALB | RDS PostgreSQL | ElastiCache Redis | ECR |
| GCP | GKE Autopilot | Cloud SQL | Memorystore | Artifact Registry |
| Azure | AKS + App Gateway | Azure Database for PG | Azure Cache | ACR |

Terraform state stored in cloud-native backend (S3 / GCS / Azure Blob). Kubernetes manifests in `deploy/k8s/` are cloud-agnostic and shared across all three providers.

---

## 12. File Structure

```
genai_logistic-intelligent-hub/
├── CLAUDE.md                          # Dev conventions
├── README.md                          # Production documentation
├── .env.example                       # All env vars documented
├── docker-compose.yml                 # All 10 services
├── docker-compose.prod.yml            # Production overrides
├── Makefile                           # make dev|test|deploy-aws|deploy-gcp|deploy-azure
│
├── glih-frontend/                     # Next.js 14 :9000
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
│   ├── components/                    # Sidebar, Header, LiveFeed, TempGauge, AlertTicker
│   └── lib/                           # API client, useSSE hook, auth utils
│
├── glih-backend/                      # FastAPI :9001
│   └── src/glih_backend/
│       ├── api/
│       │   ├── rag.py                 # existing + batch endpoint
│       │   ├── agents.py              # NEW — critical wiring
│       │   ├── stream.py              # NEW — SSE endpoints
│       │   └── auth.py                # NEW — JWT + OAuth2 + API keys
│       ├── connectors/
│       │   ├── base.py                # Abstract interface
│       │   ├── wms.py                 # WmsConnector (demo + real)
│       │   ├── iot.py                 # IotConnector (demo + real)
│       │   └── docs.py                # DocsConnector (demo + real)
│       ├── demo/
│       │   ├── simulator.py           # IoT background task
│       │   └── scenarios.py           # 6 pre-wired demo presets
│       ├── auth/
│       │   ├── jwt.py
│       │   ├── oauth.py
│       │   ├── apikeys.py
│       │   └── rbac.py
│       └── providers.py               # existing — unchanged
│
├── glih-agents/                       # Existing — no changes
├── mcp-servers/                       # Re-ported to 9002–9004
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
│       └── locustfile.py              # 6 load scenarios
│
├── deploy/
│   ├── aws/                           # Terraform: EKS, RDS, ElastiCache, ALB, ECR
│   ├── gcp/                           # Terraform: GKE, Cloud SQL, Memorystore, AR
│   ├── azure/                         # Terraform: AKS, Azure DB, Azure Cache, ACR
│   ├── k8s/                           # Shared: deployment, service, ingress, hpa, secrets
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

## 13. CLAUDE.md Conventions Summary

- **Ports:** 9000–9009 exclusively. Document any new service in CLAUDE.md before using a port.
- **Startup:** `make dev` starts all services. Never start services individually during development.
- **Connector pattern:** All external data flows through a connector. Never bypass with hardcoded data.
- **Agent pattern:** Agents never import connectors. Callbacks always injected by `api/agents.py`.
- **LLM calls:** Every `llm.generate()` call must include a `trace_id` for Langfuse. No exceptions.
- **Auth:** All `/api/*` routes require JWT. Add `Depends(require_auth)` to every new endpoint.
- **Testing:** `make test` must pass before any PR. Locust normal-ops scenario must pass at 20 users.
- **Terraform:** Never `terraform apply` manually. Use `make deploy-{cloud}` which runs plan first.

---

## 14. Non-Goals (Explicitly Out of Scope)

- Native mobile application
- Real-time video / camera feeds
- Billing / invoicing system
- Inventory management beyond what WMS provides
- Email server (uses external SMTP provider)

---

*Spec approved 2026-03-24. Implementation plan to follow.*
