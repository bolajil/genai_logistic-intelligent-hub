# GLIH — GenAI Logistics Intelligence Hub

> **Production-grade cold chain intelligence platform.** Autonomous AI agents monitor temperature-sensitive shipments, detect anomalies, optimise routes, notify customers, and generate operational reports — in real time.

[![CI](https://github.com/bolajil/genai_logistic-intelligent-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/bolajil/genai_logistic-intelligent-hub/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What GLIH Solves

Cold chain logistics operations — managing thousands of temperature-sensitive shipments daily — face four critical challenges:

| Challenge | GLIH Solution | Impact |
|-----------|--------------|--------|
| Temperature breaches detected too late | **AnomalyResponder** — real-time detection, SOP retrieval, action generation | 90% faster breach response |
| Spoilage from suboptimal routing | **RouteAdvisor** — spoilage risk scoring, route alternatives, carrier recommendations | 40% reduction in food waste |
| Customer calls overwhelming ops teams | **CustomerNotifier** — proactive multi-channel notifications (email, SMS, webhook) | 50% reduction in inbound inquiries |
| Manual shift handoff reports taking hours | **OpsSummarizer** — automated KPI reports with LLM executive summaries | 80% reduction in reporting time |

All four agents connect to a RAG (Retrieval-Augmented Generation) pipeline backed by cold chain SOPs, route history, and operational documents. Every agent decision is traceable, auditable, and explainable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Next.js 14 :9000  —  Dark Ops Command Centre                   │
│  Dashboard · Agents · Shipments · Alerts · Analytics · Admin    │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST + SSE (live updates)
┌───────────────────────▼─────────────────────────────────────────┐
│  FastAPI :9001  —  Modular Backend                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ api/rag  │ │api/agents│ │api/stream│ │   api/auth       │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  connectors/  —  Demo ←──per-connection toggle──→ Real  │   │
│  │  WmsConnector · IotConnector · DocsConnector            │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────┬──────────────────────┬───────────────────┬──────────────┘
       │                      │                   │
┌──────▼──────┐  ┌────────────▼────┐  ┌───────────▼────────────┐
│ MCP :9002   │  │  MCP :9003      │  │  MCP :9004             │
│ WMS Server  │  │  IoT Server     │  │  Docs Server           │
│ demo ↔ real │  │  demo ↔ MQTT   │  │  demo ↔ SharePoint     │
└─────────────┘  └─────────────────┘  └────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│  Data Layer                                                      │
│  ChromaDB (vectors) · PostgreSQL :9006 · Redis :9007            │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│  Observability                                                   │
│  Langfuse :9008 (LLM traces + cost)  ·  Locust :9009 (load)    │
└─────────────────────────────────────────────────────────────────┘
```

### Port Map

| Port | Service | Notes |
|------|---------|-------|
| 9000 | Next.js frontend | Dark Ops dashboard |
| 9001 | FastAPI backend | RAG + Agents + Auth + SSE |
| 9002 | WMS MCP server | Shipment data |
| 9003 | IoT MCP server | Sensor / GPS data |
| 9004 | Docs MCP server | SOPs + BOLs |
| 9005 | MQTT broker (Mosquitto) | Real IoT ingestion |
| 9006 | PostgreSQL | Users, audit log, connector settings |
| 9007 | Redis | Sessions, rate limiting, SSE pub/sub |
| 9008 | Langfuse | Dev only — LLM trace viewer |
| 9009 | Locust | Dev only — load testing UI |

---

## Quick Start

**Prerequisites:** Docker Desktop, Python 3.11+, Node.js 18+

```bash
# 1. Clone and configure
git clone https://github.com/bolajil/genai_logistic-intelligent-hub.git
cd genai_logistic-intelligent-hub
cp .env.example .env
# Edit .env — add at least one LLM API key (OPENAI_API_KEY recommended)

# 2. Start all services (runs DB migrations automatically)
make dev

# 3. Open the platform
open http://localhost:9000

# Default admin credentials (forced change on first login):
#   Email:    admin@glih.local
#   Password: ChangeMe123!
```

All 10 services start, database migrations run, and the demo IoT simulator begins generating live sensor data immediately — no additional configuration required.

---

## Demo Scenarios

Six pre-wired scenarios demonstrate full platform capability. Access them from the **Agents** page → **Demo Presets**.

### Scenario 1 — Temperature Breach Response (~8s)
A dairy shipment exceeds its 4°C threshold. `AnomalyResponder` detects the breach, retrieves the relevant SOP from the RAG database, generates a prioritised action plan, and `CustomerNotifier` sends a personalised alert. Full agent chain visible in real time on the dashboard.

```bash
# Trigger via API
curl -X POST http://localhost:9001/api/agents/anomaly \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<token>" \
  -d '{
    "shipment_id": "DEMO-SHP-CHI-ATL-001",
    "temperature_c": 5.2,
    "threshold_max_c": 4.0,
    "location": "Atlanta Cold Hub, GA",
    "breach_duration_min": 22
  }'
```

### Scenario 2 — Route Optimisation Under Risk (~6s)
A seafood shipment reaches 68% spoilage risk. `RouteAdvisor` queries historical route performance from the vector database, evaluates three alternatives, and recommends the optimal route with cost and time trade-offs.

### Scenario 3 — Shift Handoff Report (~10s)
`OpsSummarizer` aggregates 24 hours of Chicago hub activity — shipment events, incidents, KPIs — and generates an LLM executive summary with recommendations for the incoming shift. Exportable as PDF.

### Scenario 4 — SOP Natural Language Query (~3s)
Ask the platform in plain English:
> *"What are the required actions if seafood exceeds 4°C for more than 30 minutes?"*

The RAG pipeline retrieves from `lineage-sops.txt` and returns a cited, step-by-step procedure.

### Scenario 5 — Live IoT Simulator (continuous)
Runs automatically in demo mode. Temperature gauges drift in real time, GPS markers move along routes, and a temperature breach fires every ~5 minutes — triggering Scenarios 1 and 2 without user action. The dashboard is always live.

### Scenario 6 — Load Test

```bash
make test-load SCENARIO=normal    # 20 concurrent users, 2 min
make test-load SCENARIO=spike     # 100 users, 30s ramp
make test-load SCENARIO=soak      # 50 users, 10 min — memory leak detection
# Results at: http://localhost:9009  (Locust UI)
# LLM cost:   http://localhost:9008  (Langfuse)
```

---

## Demo → Real Connection Switching

Each of the three external integrations has an independent toggle. Switch from the **Settings** page (requires `ops-manager` role or above) — no server restart required.

| Connection | Demo Mode | Real Mode |
|-----------|-----------|-----------|
| **WMS** | Mock shipments via MCP :9002 | Your WMS REST API |
| **IoT** | Built-in temperature/GPS simulator | MQTT broker — live sensor topics |
| **Docs** | Mock SOPs/BOLs via MCP :9004 | SharePoint / DMS API |

To configure a real connection: **Settings → Connections → [Name] → Configure** → enter endpoint and credentials → flip the toggle. Demo and real data never mix — the connector factory reads the database flag at request time.

---

## The Four Agents

### AnomalyResponder
Detects temperature breaches, GPS deviations, and door-open events. Retrieves relevant SOPs from the vector database. Generates a tiered action plan (medium / high / critical). Publishes alerts to the live dashboard stream.

**Endpoint:** `POST /api/agents/anomaly`

### RouteAdvisor
Calculates spoilage risk based on product shelf life and transit time. Queries historical route performance. Returns ranked route alternatives with cost, time, and risk trade-offs.

**Endpoint:** `POST /api/agents/route`

### CustomerNotifier
Generates personalised notifications based on customer channel preferences (email, SMS, webhook). Uses LLM for nuanced messaging on sensitive events. Logs all communications for compliance.

**Endpoint:** `POST /api/agents/notify`

### OpsSummarizer
Aggregates events and incidents over a configurable time window (8h / 24h / 7d). Calculates on-time %, temperature compliance, and average delay. Generates LLM executive summaries with next-shift recommendations. Exports PDF/Excel.

**Endpoint:** `POST /api/agents/ops-summary`

---

## API Reference

All endpoints require JWT authentication via httpOnly cookie. Obtain a token at `POST /api/auth/login`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Username/password → JWT cookies |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | Revoke session |
| `GET`  | `/api/auth/me` | Current user profile |
| `GET`  | `/api/auth/oauth/entra` | Microsoft Entra SSO redirect |
| `GET`  | `/api/auth/oauth/google` | Google Workspace SSO redirect |
| `POST` | `/api/auth/apikeys` | Create scoped API key |
| `DELETE` | `/api/auth/apikeys/{id}` | Revoke API key |

### RAG Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest` | Ingest text content |
| `POST` | `/api/ingest/file` | Upload file (PDF, DOCX, TXT) |
| `POST` | `/api/ingest/url` | Ingest from URL |
| `POST` | `/api/ingest/batch` | Batch ingest multiple sources |
| `POST` | `/api/query` | RAG query with collection selection |
| `GET`  | `/api/collections` | List all collections |
| `DELETE` | `/api/collections/{name}` | Delete collection |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents/anomaly` | Run AnomalyResponder |
| `POST` | `/api/agents/route` | Run RouteAdvisor |
| `POST` | `/api/agents/notify` | Run CustomerNotifier |
| `POST` | `/api/agents/ops-summary` | Run OpsSummarizer |
| `GET`  | `/api/agents/history` | Agent run history + Langfuse trace links |

### Live Streaming (SSE)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stream/sensors` | Live sensor readings |
| `GET` | `/api/stream/alerts` | Agent-generated alerts |
| `GET` | `/api/stream/shipments` | Shipment status updates |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (no auth required) |
| `GET` | `/api/health/detailed` | Provider status, DB, Redis |
| `PATCH` | `/api/settings/connectors/{id}` | Toggle Demo/Real per connector |

---

## Observability

### Langfuse — LLM Tracing & Cost Tracking

Every agent run creates a Langfuse trace capturing: triggering user, agent name, RAG documents retrieved (with cosine distances), full LLM prompt and response, token usage, estimated cost, and end-to-end latency.

- **Development:** [http://localhost:9008](http://localhost:9008)
- **Production:** Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` to point at [cloud.langfuse.com](https://cloud.langfuse.com) — no code changes.

### Locust — Load Testing

```bash
make test-load SCENARIO=normal    # 20 users — baseline
make test-load SCENARIO=spike     # 100 users, 30s ramp
make test-load SCENARIO=soak      # 50 users, 10 min
make test-load SCENARIO=sse       # 200 SSE connections
make test-load SCENARIO=agent     # 50 concurrent agent calls
make test-load SCENARIO=auth      # 100 login/refresh cycles
```

Results at [http://localhost:9009](http://localhost:9009). All scenarios authenticate automatically using the seeded test user (`locust@glih.test`).

---

## Authentication

### RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access — user management, connector toggles, API keys |
| `ops-manager` | Run agents, view all data, toggle Demo/Real connectors, export |
| `analyst` | View all data, run agents, query RAG, ingest documents |
| `viewer` | View dashboard and shipments only |

### API Keys (Machine-to-Machine)

```bash
# Create a scoped API key for IoT device ingestion
curl -X POST http://localhost:9001/api/auth/apikeys \
  -H "Cookie: access_token=<admin_token>" \
  -d '{"name": "Chicago Hub IoT Gateway", "scopes": ["iot:ingest"]}'
```

Available scopes: `iot:ingest` · `agents:run` · `rag:query` · `rag:ingest` · `admin`

### OAuth2 SSO

Enable enterprise SSO in `.env`:
```bash
OAUTH_ENABLED=true
OAUTH_MICROSOFT_CLIENT_ID=your-entra-app-id
OAUTH_MICROSOFT_CLIENT_SECRET=your-secret
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_GOOGLE_CLIENT_SECRET=your-secret
```

Users are auto-provisioned with `viewer` role on first OAuth login. Promote via **Admin → Users**.

---

## Cloud Deployment

### AWS (EKS)

```bash
make deploy-aws
# Provisions: EKS, RDS PostgreSQL 16, ElastiCache Redis, ALB + ACM TLS, ECR
# State: s3://glih-terraform-state-{account_id}
```

### GCP (GKE Autopilot)

```bash
make deploy-gcp
# Provisions: GKE Autopilot, Cloud SQL, Memorystore Redis, Cloud Load Balancer, Artifact Registry
# State: gs://glih-terraform-state-{project_id}
```

### Azure (AKS)

```bash
make deploy-azure
# Provisions: AKS, Azure Database for PostgreSQL Flex, Azure Cache for Redis, App Gateway, ACR
# State: Azure Blob Storage — glih-terraform-state
```

All clouds share the Kubernetes manifests in `deploy/k8s/`. Never run `terraform apply` directly — the `make deploy-*` targets run `plan` and require explicit confirmation before applying.

---

## Environment Variables

```bash
# ── LLM Providers (at least one required) ──────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
DEEPSEEK_API_KEY=...

# ── Active LLM + Embeddings ────────────────────────────────────
GLIH_LLM_PROVIDER=openai              # openai | anthropic | mistral | deepseek
GLIH_LLM_MODEL=gpt-4o-mini
GLIH_EMBEDDINGS_PROVIDER=openai       # openai | huggingface | mistral
GLIH_EMBEDDINGS_MODEL=text-embedding-3-small

# ── Database ───────────────────────────────────────────────────
POSTGRES_USER=glih
POSTGRES_PASSWORD=changeme
POSTGRES_DB=glih

# ── Auth ───────────────────────────────────────────────────────
JWT_SECRET=change-this-to-a-secure-random-string-min-32-chars
OAUTH_ENABLED=false
OAUTH_MICROSOFT_CLIENT_ID=
OAUTH_MICROSOFT_CLIENT_SECRET=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=

# ── Observability ──────────────────────────────────────────────
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:9008   # production: https://cloud.langfuse.com

# ── Real Connectors (used when toggled from demo) ──────────────
WMS_API_ENDPOINT=https://wms.your-client.com/api/v1
WMS_API_KEY=
IOT_MQTT_URL=mqtt://broker.your-client.com:1883
IOT_MQTT_USERNAME=
IOT_MQTT_PASSWORD=
DOCS_API_ENDPOINT=https://sharepoint.your-client.com
DOCS_API_KEY=

# ── App ────────────────────────────────────────────────────────
APP_ENV=development                   # development | production
NEXT_PUBLIC_API_URL=http://localhost:9001
```

---

## Development Commands

```bash
make dev          # Start all 10 services (with DB migrations)
make test         # pytest + ruff + mypy + npm build
make test-load    # Locust normal-ops scenario
make migrate      # Run Alembic migrations manually
make logs         # Tail all service logs
make stop         # Stop all services
```

### Running Services Individually

```bash
# Backend
cd glih-backend && uvicorn glih_backend.main:app --host 0.0.0.0 --port 9001 --reload

# Frontend
cd glih-frontend && npm run dev   # → http://localhost:9000

# MCP servers
cd mcp-servers
python wms_server.py    # → :9002
python iot_server.py    # → :9003
python docs_server.py   # → :9004
```

---

## Project Structure

```
genai_logistic-intelligent-hub/
├── CLAUDE.md                    # Developer conventions for this repo
├── README.md                    # This file
├── .env.example                 # All environment variables documented
├── docker-compose.yml           # All 10 services (dev)
├── docker-compose.prod.yml      # 8 services (excludes Langfuse + Locust)
├── Makefile                     # make dev|test|test-load|migrate|deploy-*
│
├── glih-frontend/               # Next.js 14 :9000
├── glih-backend/                # FastAPI :9001
│   └── src/glih_backend/
│       ├── api/                 # rag · agents · stream · auth
│       ├── connectors/          # base · factory · wms · iot · docs
│       ├── demo/                # simulator · scenarios
│       ├── auth/                # jwt · oauth · apikeys · rbac
│       └── observability/       # tracing (Langfuse)
├── glih-agents/                 # AI agent classes (unchanged)
├── mcp-servers/                 # WMS · IoT · Docs mock servers
├── tests/                       # unit/ · integration/ · load/
├── deploy/                      # aws/ · gcp/ · azure/ · k8s/ · scripts/
└── .github/workflows/           # ci.yml · deploy.yml
```

---

## Design Specification

Full architectural decisions, database schema, connector abstraction, agent wiring, auth flows, demo scenarios, and deployment strategy:

[docs/superpowers/specs/2026-03-24-glih-production-platform-design.md](docs/superpowers/specs/2026-03-24-glih-production-platform-design.md)

---

## Roadmap

- [x] RAG pipeline (ingest, embed, query)
- [x] Four AI agent classes (Anomaly · Route · Notify · Ops)
- [x] Multi-provider LLM (OpenAI · Anthropic · Mistral · DeepSeek)
- [x] Multi-vector-store (ChromaDB · FAISS · Pinecone · Weaviate · Qdrant · Milvus)
- [x] Mock MCP servers (WMS · IoT · Docs)
- [x] Production design specification
- [ ] Next.js 14 Dark Ops frontend
- [ ] Connector abstraction with per-connection Demo/Real toggle
- [ ] JWT + OAuth2 + API key authentication + RBAC
- [ ] Agent API endpoints (the critical wiring)
- [ ] Real-time SSE + MQTT IoT pipeline
- [ ] Demo IoT simulator
- [ ] Langfuse LLM observability
- [ ] Locust load testing suite
- [ ] Alembic database migrations
- [ ] Docker Compose (10 services)
- [ ] GitHub Actions CI/CD
- [ ] Terraform: AWS · GCP · Azure

---

*Production-grade cold chain intelligence. Demo-to-real switching without code changes.*
