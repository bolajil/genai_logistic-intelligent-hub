# MCP UI Guide

Quick guide to using the Model Context Protocol tab in the GLIH Streamlit interface.

---

## Accessing the MCP Tab

1. **Start the frontend**:
   ```powershell
   streamlit run glih-frontend/src/glih_frontend/app.py
   ```

2. **Open in browser**: http://localhost:8501

3. **Click the "MCP" tab** (rightmost tab)

---

## Features

### 1. Server Status Dashboard

Shows real-time status of all 3 MCP servers:
- ✅ **WMS Server** (port 8080) - Warehouse Management System
- ✅ **IoT Server** (port 8081) - IoT Sensor Data  
- ✅ **Docs Server** (port 8082) - Document Storage

**If servers show ❌**: They're not running. Start them with:
```powershell
cd mcp-servers
./start_all.ps1
```

---

### 2. Resource Browser

Browse and view data from each MCP server:

#### **Shipments (WMS)**
- View all available shipments
- Select a shipment to see details:
  - Origin and destination
  - Product type and status
  - **Temperature monitoring** with breach detection
  - ETA and carrier info
- Temperature breaches are highlighted in red

**Example**: Select `CHI-ATL-2025-089` to see a temperature breach scenario

#### **Sensors (IoT)**
- Browse sensors by type (temperature, GPS, door)
- View real-time sensor readings
- **Auto-refresh option** for live monitoring (updates every 5 seconds)
- Status indicators:
  - 🟢 NORMAL
  - 🟡 WARNING
  - 🔴 CRITICAL

**Example**: Select temperature sensor `TEMP-002` to see critical breach

#### **Documents (Docs)**
- Browse documents by type (SOP, invoice, BOL)
- View full document content
- See metadata (tags, creation date, associated shipments)
- Search through SOPs, invoices, and bills of lading

**Example**: View `SOP-TEMP-BREACH-001` for temperature breach protocols

---

## Usage Scenarios

### Scenario 1: Monitor Shipment Temperature

1. Go to MCP tab
2. Select "Shipments (WMS)"
3. Choose shipment `CHI-ATL-2025-089`
4. Click "Get Shipment Details"
5. See temperature breach: **5.2°C** (required: 0-4°C)

### Scenario 2: Real-Time Sensor Monitoring

1. Go to MCP tab
2. Select "Sensors (IoT)"
3. Choose sensor type: `temperature`
4. Select sensor: `TEMP-002`
5. **Check "Auto-refresh (5s)"** for live updates
6. Watch sensor readings update in real-time

### Scenario 3: View Response Procedures

1. Go to MCP tab
2. Select "Documents (Docs)"
3. Choose document type: `sop`
4. Select: "Temperature Breach Response Protocol"
5. Click "Get Document"
6. Read full SOP with step-by-step procedures

---

## Troubleshooting

### "WMS Server is not running"

**Fix**: Start the WMS server
```powershell
cd mcp-servers
python wms_server.py
```

### "Failed to load collections" error

**Fix**: Start the GLIH backend
```powershell
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

### Auto-refresh not working

**Issue**: Browser may block auto-refresh
**Fix**: Manually click "Get Sensor Reading" button to refresh

---

## Tips

1. **Keep MCP servers running** in separate terminals for best experience
2. **Use auto-refresh** for temperature sensors to catch breaches immediately
3. **Check shipment details first**, then view associated sensors
4. **Read SOPs** before responding to incidents
5. **Temperature breaches** are automatically highlighted in red

---

## Next Steps

- **Integrate with agents**: Use MCP data in AnomalyResponder
- **Add alerts**: Set up notifications for critical sensors
- **Export data**: Download reports from MCP resources
- **Custom dashboards**: Create facility-specific views

---

**For detailed MCP setup and API usage, see [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)**
