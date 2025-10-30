# MCP Servers for GLIH

Mock Model Context Protocol servers for testing and development.

## Overview

This directory contains three MCP servers that simulate external data sources:

1. **WMS Server** (`wms_server.py`) - Warehouse Management System data
2. **IoT Server** (`iot_server.py`) - IoT sensor data (temperature, GPS, door)
3. **Docs Server** (`docs_server.py`) - Document storage (SOPs, invoices, BOLs)

## Installation

```powershell
# Install dependencies
pip install -r requirements.txt
```

## Running Servers

Each server runs on a different port:

```powershell
# Terminal 1: WMS Server (port 8080)
python wms_server.py

# Terminal 2: IoT Server (port 8081)
python iot_server.py

# Terminal 3: Docs Server (port 8082)
python docs_server.py
```

## API Endpoints

All servers implement the MCP specification:

- `GET /` - Server info
- `GET /resources` - List all resources
- `GET /resources/{type}/{id}` - Get specific resource
- `GET /query` - Query resources with filters
- `GET /health` - Health check

### WMS Server (port 8080)

Mock shipments:
- `TX-CHI-2025-001` - Dallas to Chicago (Seafood)
- `CHI-ATL-2025-089` - Chicago to Atlanta (Dairy, breach scenario)
- `LA-SEA-2025-156` - Los Angeles to Seattle (Frozen Foods)

Example:
```powershell
curl http://localhost:8080/resources/shipments/TX-CHI-2025-001
```

### IoT Server (port 8081)

Mock sensors:
- `TEMP-001`, `TEMP-002`, `TEMP-003` - Temperature sensors
- `GPS-001`, `GPS-002`, `GPS-003` - GPS sensors
- `DOOR-001`, `DOOR-002`, `DOOR-003` - Door sensors

Example:
```powershell
curl http://localhost:8081/resources/sensors/TEMP-001
```

### Docs Server (port 8082)

Mock documents:
- `SOP-TEMP-BREACH-001` - Temperature breach SOP
- `SOP-NOTIFICATION-001` - Customer notification SOP
- `INV-2025-8834` - Invoice for TX-CHI-2025-001
- `BOL-CHI-ATL-089` - Bill of lading for CHI-ATL-2025-089

Example:
```powershell
curl http://localhost:8082/resources/documents/SOP-TEMP-BREACH-001
```

## Testing

After starting all servers, test with:

```powershell
# From project root
python test_mcp_client.py
```

## Production Deployment

These are **mock servers for development only**. In production:

1. Replace with actual integrations to Lineage systems
2. Add authentication (API keys, OAuth)
3. Use HTTPS/TLS
4. Add rate limiting
5. Deploy in private VPC
6. Add monitoring and logging

## Architecture

```
GLIH Backend
    ↓
MCP Client
    ↓
┌───────────┬───────────┬───────────┐
│ WMS:8080  │ IoT:8081  │ Docs:8082 │
└───────────┴───────────┴───────────┘
    ↓           ↓           ↓
[Lineage]   [Sensors]   [Storage]
[Systems]   [Network]   [Systems]
```

## Troubleshooting

**Port already in use:**
```powershell
# Find process using port
netstat -ano | findstr "8080"
# Kill process
taskkill /PID <process_id> /F
```

**Import errors:**
```powershell
pip install -r requirements.txt
```

**Connection refused:**
- Ensure server is running
- Check firewall settings
- Verify port is correct

## Next Steps

1. Test with `test_mcp_client.py`
2. Integrate into GLIH agents
3. Replace with real system connections
4. Deploy to production environment
