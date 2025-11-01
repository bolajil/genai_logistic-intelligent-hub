# MCP UI Features Overview

Visual guide to what you'll see in the MCP tab.

---

## MCP Tab Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  GenAI Logistics Intelligence Hub (GLIH)                        │
│  Backend: http://localhost:8000                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Ingestion] [Query] [Configuration] [Admin] [MCP] ← NEW TAB   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 1: Server Status Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Model Context Protocol (MCP)                                   │
│  Standardized access to external data sources                   │
│                                                                  │
│  ### Server Status                                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ ✅ WMS Server│  │ ✅ IoT Server│  │ ✅ Docs Server│        │
│  │ Warehouse    │  │ IoT Sensor   │  │ Document     │         │
│  │ Management   │  │ Data         │  │ Storage      │         │
│  │ System       │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**If servers are not running:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ ❌ WMS Server│  │ ❌ IoT Server│  │ ❌ Docs Server│        │
│  │ Not running  │  │ Not running  │  │ Not running  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ⚠️ No MCP servers are running. Start them with:               │
│  cd mcp-servers                                                 │
│  ./start_all.ps1  # Windows                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 2: Resource Browser

### Shipments (WMS)

```
┌─────────────────────────────────────────────────────────────────┐
│  ### Resource Browser                                           │
│                                                                  │
│  Select Resource Type: [Shipments (WMS) ▼]                     │
│                                                                  │
│  Found 3 shipments                                              │
│                                                                  │
│  Select Shipment: [TX-CHI-2025-001 ▼]                          │
│                                                                  │
│  [Get Shipment Details]                                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Origin       │  │ Destination  │  │ Temperature  │         │
│  │ Dallas       │  │ Chicago      │  │ 0.5°C        │         │
│  │              │  │              │  │ ✅ OK        │         │
│  │ Product Type │  │ Status       │  │ Required:    │         │
│  │ Seafood      │  │ in_transit   │  │ -2°C to 2°C  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ▼ Full Shipment Data                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Temperature Breach Example (CHI-ATL-2025-089):**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Origin       │  │ Destination  │  │ Temperature  │         │
│  │ Chicago      │  │ Atlanta      │  │ 5.2°C        │         │
│  │              │  │              │  │ ⚠️ BREACH    │  ← RED  │
│  │ Product Type │  │ Status       │  │ Required:    │         │
│  │ Dairy        │  │ in_transit   │  │ 0°C to 4°C   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

### Sensors (IoT)

```
┌─────────────────────────────────────────────────────────────────┐
│  Select Resource Type: [Sensors (IoT) ▼]                       │
│                                                                  │
│  Found 9 sensors                                                │
│                                                                  │
│  Sensor Type: [temperature ▼]                                  │
│  Select Sensor: [TEMP-001 ▼]                                   │
│                                                                  │
│  [✓] Auto-refresh (5s)    [Get Sensor Reading]                 │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │Sensor ID│  │  Type   │  │  Value  │  │ Status  │          │
│  │TEMP-001 │  │temperat │  │ 0.5°C   │  │🟢 NORMAL│          │
│  │         │  │  ure    │  │ celsius │  │         │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                                  │
│  Shipment: TX-CHI-2025-001 | Timestamp: 2025-10-30T11:45:00Z  │
│                                                                  │
│  ▼ Full Sensor Data                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Critical Sensor Example (TEMP-002):**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │Sensor ID│  │  Type   │  │  Value  │  │ Status  │          │
│  │TEMP-002 │  │temperat │  │ 5.2°C   │  │🔴CRITICAL│ ← RED   │
│  │         │  │  ure    │  │ celsius │  │         │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

### Documents (Docs)

```
┌─────────────────────────────────────────────────────────────────┐
│  Select Resource Type: [Documents (Docs) ▼]                    │
│                                                                  │
│  Found 4 documents                                              │
│                                                                  │
│  Document Type: [sop ▼]                                        │
│  Select Document: [Temperature Breach Response Protocol ▼]     │
│                                                                  │
│  [Get Document]                                                 │
│                                                                  │
│  ### Temperature Breach Response Protocol                       │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────────────┐        │
│  │  Type   │  │ Created │  │ Tags: sop, temperature, │        │
│  │  SOP    │  │2024-01-15│  │ breach, response,       │        │
│  │         │  │         │  │ cold-chain              │        │
│  └─────────┘  └─────────┘  └─────────────────────────┘        │
│                                                                  │
│  #### Content                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ STANDARD OPERATING PROCEDURE: Temperature Breach Response │ │
│  │                                                           │ │
│  │ 1. IMMEDIATE ACTIONS (Within 5 minutes)                  │ │
│  │    - Document breach time, duration, and temperature     │ │
│  │    - Verify sensor accuracy with backup thermometer      │ │
│  │    - Notify shift supervisor immediately                 │ │
│  │                                                           │ │
│  │ 2. ASSESSMENT (Within 15 minutes)                        │ │
│  │    - Determine product type and temperature requirements │ │
│  │    - Calculate total exposure time above threshold       │ │
│  │    ...                                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ▼ Full Document Metadata                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 3: Quick Actions

```
┌─────────────────────────────────────────────────────────────────┐
│  ### Quick Actions                                              │
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │ 🔍 Search All Resources  │  │ 📊 View Analytics        │   │
│  │                          │  │    Dashboard             │   │
│  └──────────────────────────┘  └──────────────────────────┘   │
│                                                                  │
│  💡 Tip: MCP provides standardized access to WMS, IoT sensors, │
│  and documents. See MCP_SETUP_GUIDE.md for more details.       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features Highlighted

### ✅ Real-Time Monitoring
- Auto-refresh checkbox for live sensor updates
- Updates every 5 seconds when enabled
- Perfect for monitoring critical sensors

### ⚠️ Breach Detection
- Temperature breaches automatically highlighted in RED
- Delta indicators show breach status
- Required range displayed for context

### 📦 Shipment Association
- Sensors linked to shipments
- Documents linked to shipments
- Easy cross-reference between resources

### 🎨 Visual Indicators
- ✅ Green checkmarks for healthy status
- ❌ Red X for errors/offline
- 🟢 Green for normal sensor status
- 🟡 Yellow for warnings
- 🔴 Red for critical alerts

### 📄 Full Data Access
- Expandable sections for complete JSON data
- Metadata display for all resources
- Tags and timestamps for documents

---

## Navigation Flow

```
1. Open MCP Tab
   ↓
2. Check Server Status
   ↓
3. Select Resource Type
   ↓
4. Browse Available Resources
   ↓
5. View Detailed Information
   ↓
6. Take Action (if needed)
```

---

## Use Case Examples

### Monitor Temperature Breach
```
MCP Tab → Shipments → CHI-ATL-2025-089 → See 5.2°C breach
```

### Check Sensor Status
```
MCP Tab → Sensors → temperature → TEMP-002 → See critical status
```

### Read SOP
```
MCP Tab → Documents → sop → Temperature Breach Protocol → Read procedures
```

### Live Monitoring
```
MCP Tab → Sensors → temperature → TEMP-001 → ✓ Auto-refresh → Watch live
```

---

**The MCP UI provides a complete, user-friendly interface for accessing all external data sources through a standardized protocol!** 🚀
