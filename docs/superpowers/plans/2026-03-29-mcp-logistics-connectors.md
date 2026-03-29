# MCP Logistics Connectors — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 10 new MCP connector clients to the GLIH platform, covering ELD compliance, load boards, TMS integration, geofencing, food safety compliance, fuel pricing, predictive maintenance, port status, customer POD notifications, and insurance claims.

**Architecture:** Each connector follows the 4-layer pattern: (1) client class in `mcp_client.py` with `connect()/disconnect()/get_status()`, (2) demo tool methods in `mcp_server.py` callable by AI agents, (3) REST endpoints in `main.py` for direct API access, (4) TOML config + Settings UI for API key management. All connectors gracefully fall back to realistic demo data when API keys are not configured.

**Tech Stack:** Python/FastAPI backend, httpx async HTTP client, Next.js/TypeScript settings UI, TOML config, Kubernetes/Terraform deploy configs

---

## File Structure

| File | Changes |
|------|---------|
| `glih-backend/src/glih_backend/mcp_client.py` | Add 10 client classes + MCPClientManager updates |
| `glih-backend/src/glih_backend/mcp_server.py` | Add 19 new tool methods + get_tools() + call_tool() |
| `glih-backend/src/glih_backend/api/main.py` | Add 20 new REST endpoints |
| `config/glih.toml` | Add 10 `[mcp.connectors.*]` sections |
| `glih-frontend-next/app/(app)/settings/page.tsx` | Add CONNECTOR_FIELDS + DEFAULT_CONNECTORS entries |
| `deploy/aws/variables.tf` | Add 9 new sensitive variable declarations |
| `deploy/gcp/main.tf` | Add 9 new Secret Manager secrets |
| `deploy/azure/main.tf` | Add 9 new Key Vault secrets |
| `deploy/k8s/secrets.yaml` | Add 9 new secret env vars |
| `docker-compose.yml` | Add 9 new env var pass-throughs |

---

## Connector Inventory

### Phase 1 — Core Operations

#### 1. Samsara ELD (Electronic Logging Device)
- **Class:** `SamsaraELDMCPClient`
- **API:** `https://api.samsara.com` (Bearer token)
- **Env var:** `SAMSARA_API_KEY`
- **TOML key:** `[mcp.connectors.samsara_eld]`
- **Tools:** `get_driver_hos_status`, `get_eld_violations`
- **Endpoints:** `GET /mcp/eld/hos`, `GET /mcp/eld/violations`

#### 2. DAT Load Board
- **Class:** `DATLoadBoardMCPClient`
- **API:** `https://api.dat.com` (username/password → bearer)
- **Env vars:** `DAT_USERNAME`, `DAT_PASSWORD`
- **TOML key:** `[mcp.connectors.dat_load_board]`
- **Tools:** `search_available_loads`, `get_lane_rate_forecast`
- **Endpoints:** `GET /mcp/loadboard/search`, `GET /mcp/loadboard/rates`

#### 3. TMS Integration (McLeod/Oracle)
- **Class:** `TMSIntegrationMCPClient`
- **API:** Customer-configured endpoint
- **Env vars:** `TMS_ENDPOINT`, `TMS_API_KEY`
- **TOML key:** `[mcp.connectors.tms]`
- **Tools:** `get_tms_shipments`
- **Endpoints:** `GET /mcp/tms/shipments`

#### 4. Geofence & POI (Google/HERE)
- **Class:** `GeofenceMCPClient`
- **API:** HERE Platform or Google Maps
- **Env vars:** `GEOFENCE_PROVIDER`, `GEOFENCE_API_KEY`
- **TOML key:** `[mcp.connectors.geofence]`
- **Tools:** `check_truck_geofences`, `get_nearby_fuel_stops`
- **Endpoints:** `GET /mcp/geofence/trucks`, `GET /mcp/geofence/fuel-stops/{truck_id}`

### Phase 2 — Compliance & Economics

#### 5. USDA/FDA Compliance
- **Class:** `USDAComplianceMCPClient`
- **API:** `https://api.fda.gov` (free, no key required)
- **Env var:** none
- **TOML key:** `[mcp.connectors.usda_compliance]`
- **Tools:** `get_compliance_status`, `get_recall_alerts`
- **Endpoints:** `GET /mcp/compliance/status`, `GET /mcp/compliance/recalls`

#### 6. EIA Fuel Prices
- **Class:** `EIAFuelPriceMCPClient`
- **API:** `https://api.eia.gov` (free, optional API key)
- **Env var:** `EIA_API_KEY` (optional)
- **TOML key:** `[mcp.connectors.eia_fuel]`
- **Tools:** `get_current_fuel_prices`, `calculate_fuel_surcharge`
- **Endpoints:** `GET /mcp/fuel/prices`, `POST /mcp/fuel/surcharge`

#### 7. Predictive Maintenance
- **Class:** `PredictiveMaintenanceMCPClient`
- **API:** Samsara or Fleet Complete
- **Env vars:** `MAINTENANCE_PROVIDER`, `MAINTENANCE_API_KEY`
- **TOML key:** `[mcp.connectors.predictive_maintenance]`
- **Tools:** `get_fleet_health`, `get_maintenance_alerts`
- **Endpoints:** `GET /mcp/maintenance/fleet-health`, `GET /mcp/maintenance/alerts`

### Phase 3 — Advanced Logistics

#### 8. Port & Intermodal Status
- **Class:** `PortStatusMCPClient`
- **API:** MarineTraffic / Portcast
- **Env var:** `PORT_STATUS_API_KEY`
- **TOML key:** `[mcp.connectors.port_status]`
- **Tools:** `get_port_status`, `get_intermodal_options`
- **Endpoints:** `GET /mcp/ports/status`, `GET /mcp/ports/intermodal`

#### 9. Twilio POD & Notifications
- **Class:** `TwilioPODMCPClient`
- **API:** `https://api.twilio.com`
- **Env vars:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- **TOML key:** `[mcp.connectors.twilio_pod]`
- **Tools:** `send_delivery_alert`, `generate_pod_document`
- **Endpoints:** `POST /mcp/notifications/delivery-alert`, `POST /mcp/notifications/pod`

#### 10. Insurance & Claims
- **Class:** `InsuranceClaimsMCPClient`
- **API:** Riskonnect or custom
- **Env vars:** `INSURANCE_ENDPOINT`, `INSURANCE_API_KEY`
- **TOML key:** `[mcp.connectors.insurance_claims]`
- **Tools:** `get_insurance_summary`, `file_cargo_claim`
- **Endpoints:** `GET /mcp/insurance/summary`, `POST /mcp/insurance/claim`

---

## Tasks

### Task 1: mcp_client.py — 10 new client classes

**Files:**
- Modify: `glih-backend/src/glih_backend/mcp_client.py`

- [x] **Step 1:** Add `import random` after existing imports
- [x] **Step 2:** Add all 10 client classes before MCPClientManager
- [x] **Step 3:** Update MCPClientManager.__init__ to initialize all 10 clients
- [x] **Step 4:** Update initialize() to connect all 10 clients
- [x] **Step 5:** Update shutdown() to disconnect all 10 clients
- [x] **Step 6:** Update get_all_status() to include all 10 clients

### Task 2: mcp_server.py — 19 new tool methods

**Files:**
- Modify: `glih-backend/src/glih_backend/mcp_server.py`

- [x] **Step 1:** Add all 19 new async tool methods after simulate_breach
- [x] **Step 2:** Add 19 tool definitions to get_tools()
- [x] **Step 3:** Add 19 entries to call_tool() lambda map

### Task 3: main.py — 20 new REST endpoints

**Files:**
- Modify: `glih-backend/src/glih_backend/api/main.py`

- [x] **Step 1:** Verify get_mcp_server import exists
- [x] **Step 2:** Add 20 new endpoint handlers after existing MCP endpoints

### Task 4: config/glih.toml — 10 connector sections

**Files:**
- Modify: `config/glih.toml`

- [x] **Step 1:** Add 10 `[mcp.connectors.*]` sections after `[mcp.connectors.traffic]`

### Task 5: settings/page.tsx — frontend connector cards

**Files:**
- Modify: `glih-frontend-next/app/(app)/settings/page.tsx`

- [x] **Step 1:** Add 10 entries to CONNECTOR_FIELDS
- [x] **Step 2:** Add 10 entries to DEFAULT_CONNECTORS

### Task 6: Deploy configs — secrets and env vars

**Files:**
- Modify: `deploy/aws/variables.tf`
- Modify: `deploy/gcp/main.tf`
- Modify: `deploy/azure/main.tf`
- Modify: `deploy/k8s/secrets.yaml`
- Modify: `docker-compose.yml`

- [x] **Step 1:** Add new sensitive variables to all deploy configs

---

## New Environment Variables

```
SAMSARA_API_KEY          # Samsara ELD/Maintenance
DAT_USERNAME             # DAT Load Board
DAT_PASSWORD             # DAT Load Board
TMS_ENDPOINT             # TMS Integration
TMS_API_KEY              # TMS Integration
GEOFENCE_API_KEY         # Geofencing & POI
EIA_API_KEY              # EIA Fuel (optional)
PORT_STATUS_API_KEY      # Port Status
TWILIO_ACCOUNT_SID       # Twilio POD
TWILIO_AUTH_TOKEN        # Twilio POD
TWILIO_FROM_NUMBER       # Twilio POD
INSURANCE_ENDPOINT       # Insurance Claims
INSURANCE_API_KEY        # Insurance Claims
```
