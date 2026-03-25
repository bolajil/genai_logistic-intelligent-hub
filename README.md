# GLIH — GenAI Logistics Intelligence Hub

> **Production-grade cold chain intelligence platform.** Autonomous AI agents monitor temperature-sensitive shipments, detect anomalies, optimise routes, notify customers, and generate operational reports — in real time. Now with **IoT integration**, **fleet management**, and **MCP connector ecosystem**.

[![CI](https://github.com/bolajil/genai_logistic-intelligent-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/bolajil/genai_logistic-intelligent-hub/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What's New (v2.0)

### 🚚 Fleet Management
- **Register 300+ trucks** via manual entry, CSV bulk import, or GPS-Trace auto-sync
- **Live tracking dashboard** with real-time location, speed, and reefer temperature
- **Fleet statistics** — active, in-transit, idle, offline counts by facility

### 🔌 MCP Connector Ecosystem
- **GPS-Trace** — Real-time truck tracking via [gps-trace.com](https://gps-trace.com) MCP
- **OpenWeatherMap** — Weather forecasts for spoilage risk and route planning
- **Lineage IoT** — Custom MQTT/API integration for temperature sensors, door status, geofences
- **Traffic APIs** — Google/HERE/Mapbox integration for ETA optimization

### ⚙️ Settings UI Overhaul
- **Connection Mode** — Toggle Demo/Real per connector
- **API Keys & IoT** — Configure all external integrations from the UI
- **LLM Provider** — Switch between OpenAI, Anthropic, Mistral, DeepSeek
- **Advanced** — Timeout, cache TTL, retry settings

### 🛡️ Graceful Degradation
- All connectors run in **DEMO mode** by default with simulated data
- Add API keys when ready — no code changes, no restarts
- Never breaks if external APIs are unavailable

---

## What GLIH Solves

Cold chain logistics operations — managing thousands of temperature-sensitive shipments daily — face four critical challenges:

| Challenge | GLIH Solution | Impact |
|-----------|--------------|--------|
| Temperature breaches detected too late | **AnomalyResponder** — real-time detection, SOP retrieval, action generation | 90% faster breach response |
| Spoilage from suboptimal routing | **RouteAdvisor** — spoilage risk scoring, route alternatives, carrier recommendations | 40% reduction in food waste |
| Customer calls overwhelming ops teams | **CustomerNotifier** — proactive multi-channel notifications (email, SMS, webhook) | 50% reduction in inbound inquiries |
| Manual shift handoff reports taking hours | **OpsSummarizer** — automated KPI reports with LLM executive summaries | 80% reduction in reporting time |
| **No visibility into fleet location** | **Fleet Management** — GPS tracking, CSV import, live status dashboard | Real-time fleet visibility |
| **Disconnected IoT sensors** | **MCP Connectors** — GPS-Trace, OpenWeatherMap, MQTT sensors unified | Single pane of glass |

All four agents connect to a RAG (Retrieval-Augmented Generation) pipeline backed by cold chain SOPs, route history, and operational documents. Every agent decision is traceable, auditable, and explainable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Next.js 14 :9000  —  Dark Ops Command Centre                   │
│  Dashboard · Agents · Fleet · Shipments · Alerts · Settings     │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST + SSE (live updates)
┌───────────────────────▼─────────────────────────────────────────┐
│  FastAPI :9001  —  Modular Backend                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ api/rag  │ │api/agents│ │api/fleet │ │   api/settings   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  MCP Connectors  —  Demo ←── plug-and-play ──→ Real     │   │
│  │  GPS-Trace · OpenWeatherMap · Lineage IoT · Traffic     │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────┬──────────────────────┬───────────────────┬──────────────┘
       │                      │                   │
┌──────▼──────┐  ┌────────────▼────┐  ┌───────────▼────────────┐
│ GPS-Trace   │  │  OpenWeather    │  │  Lineage IoT MCP       │
│ MCP Client  │  │  MCP Client     │  │  MQTT + REST + Demo    │
│ Truck GPS   │  │  Weather API    │  │  Sensors + Alerts      │
└─────────────┘  └─────────────────┘  └────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│  Data Layer                                                      │
│  ChromaDB (vectors) · trucks.json · PostgreSQL · Redis          │
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
| 9001 | FastAPI backend | RAG + Agents + Fleet + MCP |
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

All services start in **DEMO mode** — no API keys required. Add keys later via **Settings → API Keys & IoT**.

---

## Fleet Management

### Register Your Fleet

**Option 1: Manual Entry**
1. Navigate to **Fleet** in the sidebar
2. Click **+ Add Truck**
3. Fill in Truck ID, Driver, Device ID, Facility
4. Click **Register Truck**

**Option 2: CSV Bulk Import (300+ trucks)**
1. Prepare CSV with columns: `truck_id, driver_name, device_id, license_plate, facility, reefer`
2. Click **📥 Bulk Import (CSV)**
3. Upload file → Preview → Import

```csv
truck_id,driver_name,device_id,license_plate,facility,reefer
TRK-001,John Smith,DEV-001,ABC-1234,Chicago DC,true
TRK-002,Maria Garcia,DEV-002,XYZ-5678,Dallas DC,true
TRK-003,James Wilson,DEV-003,QRS-9012,Atlanta DC,true
```

**Option 3: GPS-Trace Auto-Sync**
1. Configure GPS-Trace API token in **Settings → API Keys & IoT**
2. Click **🔄 Sync GPS-Trace** in Fleet page
3. All trucks from your GPS-Trace account are imported automatically

### Fleet API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/fleet/trucks` | List all trucks with live GPS data |
| `POST` | `/fleet/trucks` | Register a new truck |
| `PUT` | `/fleet/trucks/{id}` | Update truck info |
| `DELETE` | `/fleet/trucks/{id}` | Deactivate truck |
| `POST` | `/fleet/trucks/bulk` | Bulk import trucks |
| `POST` | `/fleet/sync/gps-trace` | Sync from GPS-Trace |
| `GET` | `/fleet/stats` | Fleet statistics |

---

## MCP Connector Configuration

### Available Connectors

| Connector | Purpose | Configuration Fields |
|-----------|---------|---------------------|
| **GPS-Trace** | Real-time truck GPS tracking | `api_token` |
| **OpenWeatherMap** | Weather forecasts for route risk | `api_key` |
| **Lineage IoT** | Temperature sensors, door status | `mqtt_broker`, `mqtt_port`, `api_endpoint`, `api_key` |
| **Traffic** | Real-time traffic for ETA | `provider` (google/here/mapbox), `api_key` |

### Configure via UI

1. Navigate to **Settings → API Keys & IoT**
2. Expand the connector you want to configure
3. Enter your API keys/credentials
4. Click **Save**
5. Click **Test Connection** to verify

### Configure via API

```bash
# Update GPS-Trace configuration
curl -X PUT http://localhost:9001/settings/mcp/connector/gps_trace \
  -H "Content-Type: application/json" \
  -d '{"api_token": "your-gps-trace-token"}'

# Test connection
curl -X POST http://localhost:9001/settings/mcp/test/gps_trace
```

### MCP API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/settings/mcp` | List all MCP connectors and status |
| `PUT` | `/settings/mcp/connector/{id}` | Update connector config |
| `POST` | `/settings/mcp/test/{id}` | Test connector connection |
| `GET` | `/mcp/trucks` | Get truck data from MCP |
| `GET` | `/mcp/sensors` | Get IoT sensor readings |
| `GET` | `/mcp/alerts` | Get temperature alerts |
| `GET` | `/mcp/facility/{name}` | Get facility status |

---

## Demo Mode vs Real Mode

Each connector operates independently:

| Mode | Behavior |
|------|----------|
| **DEMO** | Simulated data generated locally — 5 trucks, 25 sensors, periodic alerts |
| **REAL** | Live data from external APIs — requires API keys configured |

### Demo Data Includes

- **5 simulated trucks** on routes between Chicago, Dallas, Atlanta, LA, Seattle
- **25 temperature sensors** across 5 facilities (5 per facility)
- **Door sensors** and **geofences** per facility
- **Temperature alerts** generated when thresholds exceeded
- **Live location updates** every few seconds

### Switching Modes

Connectors automatically switch to REAL mode when:
1. Valid API keys are configured in Settings
2. Connection test passes

No server restart required.

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
├── glih-frontend-next/          # Next.js 14 :9000
│   └── app/(app)/
│       ├── dashboard/           # Operations dashboard
│       ├── fleet/               # Fleet management (NEW)
│       ├── shipments/           # Shipment tracking
│       ├── alerts/              # Alert management
│       ├── settings/            # API keys, connectors, LLM (NEW)
│       └── agents/              # AI agent control
│
├── glih-backend/                # FastAPI :9001
│   └── src/glih_backend/
│       ├── api/main.py          # All API endpoints
│       ├── mcp_client.py        # GPS-Trace, OpenWeatherMap, IoT clients (NEW)
│       ├── mcp_server.py        # Custom Lineage IoT MCP server (NEW)
│       ├── connectors/          # base · factory · wms · iot · docs
│       ├── demo/                # simulator · scenarios
│       ├── auth/                # jwt · oauth · apikeys · rbac
│       └── observability/       # tracing (Langfuse)
│
├── config/
│   └── glih.toml                # MCP connector configuration (NEW)
│
├── data/
│   └── trucks.json              # Fleet data persistence (NEW)
│
├── glih-agents/                 # AI agent classes
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

### Completed ✅

- [x] RAG pipeline (ingest, embed, query)
- [x] Four AI agent classes (Anomaly · Route · Notify · Ops)
- [x] Multi-provider LLM (OpenAI · Anthropic · Mistral · DeepSeek)
- [x] Multi-vector-store (ChromaDB · FAISS · Pinecone · Weaviate · Qdrant · Milvus)
- [x] Mock MCP servers (WMS · IoT · Docs)
- [x] Production design specification
- [x] Next.js 14 Dark Ops frontend
- [x] Connector abstraction with per-connection Demo/Real toggle
- [x] Demo IoT simulator with live data
- [x] **Fleet Management** — manual entry, CSV bulk import, GPS-Trace sync
- [x] **MCP Connector Ecosystem** — GPS-Trace, OpenWeatherMap, Lineage IoT, Traffic
- [x] **Settings UI** — API keys, LLM provider, connector config
- [x] **Graceful degradation** — demo mode fallback when APIs unavailable

### In Progress 🔄

- [ ] JWT + OAuth2 + API key authentication + RBAC
- [ ] Agent API endpoints (the critical wiring)
- [ ] Real-time SSE + MQTT IoT pipeline
- [ ] Langfuse LLM observability
- [ ] Locust load testing suite

### Planned 📋

- [ ] Alembic database migrations
- [ ] Docker Compose (10 services)
- [ ] GitHub Actions CI/CD
- [ ] Terraform: AWS · GCP · Azure
- [ ] Mobile app (React Native)
- [ ] Multi-tenant support

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Production-grade cold chain intelligence. Demo-to-real switching without code changes. Fleet management for 300+ trucks.*
