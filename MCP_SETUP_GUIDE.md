# MCP Setup and Testing Guide

**Model Context Protocol Integration for GLIH**

---

## Overview

This guide walks you through setting up and testing the Model Context Protocol (MCP) integration in GLIH. MCP enables standardized access to external data sources (WMS, IoT sensors, documents) through a unified interface.

---

## Prerequisites

- Python 3.10+
- GLIH backend installed
- Virtual environment activated

---

## Installation

### Step 1: Install MCP Dependencies

```powershell
# From project root
pip install -e glih-backend

# Verify MCP package is installed
python -c "import mcp; print('MCP installed successfully')"
```

### Step 2: Configure MCP Servers

Edit `config/glih.toml` to enable MCP:

```toml
[mcp]
enabled = true  # Change from false to true
timeout_seconds = 30
retry_attempts = 3
cache_ttl_seconds = 300

[[mcp.servers]]
name = "lineage-wms"
url = "http://localhost:8080"
description = "WMS/TMS data access for shipments and inventory"
enabled = true  # Change from false to true

[[mcp.servers]]
name = "lineage-iot"
url = "http://localhost:8081"
description = "IoT sensor data streaming (temperature, GPS, door status)"
enabled = true  # Change from false to true

[[mcp.servers]]
name = "lineage-docs"
url = "http://localhost:8082"
description = "Document storage access (invoices, BOLs, SOPs)"
enabled = true  # Change from false to true
```

---

## Running MCP Servers

You'll need **4 terminals** to run everything:

### Terminal 1: WMS MCP Server

```powershell
cd mcp-servers
python wms_server.py
```

Expected output:
```
Starting Lineage WMS MCP Server on http://localhost:8080
Available shipments:
  - TX-CHI-2025-001
  - CHI-ATL-2025-089
  - LA-SEA-2025-156
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Terminal 2: IoT MCP Server

```powershell
cd mcp-servers
python iot_server.py
```

Expected output:
```
Starting Lineage IoT MCP Server on http://localhost:8081
Available sensors:
  - TEMP-001: temperature (TX-CHI-2025-001)
  - GPS-001: gps (TX-CHI-2025-001)
  ...
INFO:     Uvicorn running on http://0.0.0.0:8081
```

### Terminal 3: Documents MCP Server

```powershell
cd mcp-servers
python docs_server.py
```

Expected output:
```
Starting Lineage Documents MCP Server on http://localhost:8082
Available documents:
  - SOP-TEMP-BREACH-001: Temperature Breach Response Protocol (sop)
  - INV-2025-8834: Invoice #2025-8834 - Seafood Shipment (invoice)
  ...
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### Terminal 4: GLIH Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

---

## Testing MCP Integration

### Test 1: Verify MCP Servers are Running

```powershell
# Test WMS server
curl http://localhost:8080/health

# Test IoT server
curl http://localhost:8081/health

# Test Documents server
curl http://localhost:8082/health
```

All should return `{"status": "healthy", ...}`

### Test 2: List Available Resources

```powershell
# List WMS resources
curl http://localhost:8080/resources

# List IoT sensors
curl http://localhost:8081/resources

# List documents
curl http://localhost:8082/resources
```

### Test 3: Read Specific Resources

```powershell
# Get shipment data
curl http://localhost:8080/resources/shipments/TX-CHI-2025-001

# Get sensor reading
curl http://localhost:8081/resources/sensors/TEMP-001

# Get document
curl http://localhost:8082/resources/documents/SOP-TEMP-BREACH-001
```

### Test 4: Query with Filters

```powershell
# Query in-transit shipments
curl "http://localhost:8080/query?pattern=shipments/*&status=in_transit"

# Query temperature sensors
curl "http://localhost:8081/query?pattern=sensors/*&sensor_type=temperature"

# Query SOPs
curl "http://localhost:8082/query?pattern=documents/*&document_type=sop"
```

---

## Using MCP Client in Python

### Basic Usage

```python
import asyncio
from glih_backend.config import load_config
from glih_backend.mcp import get_mcp_client

async def main():
    # Load configuration
    config = load_config()
    
    # Get MCP client
    mcp_client = get_mcp_client(config.get("mcp", {}))
    
    if not mcp_client:
        print("MCP is not enabled")
        return
    
    try:
        # List all resources
        resources = await mcp_client.list_resources()
        print(f"Found {len(resources)} resources")
        
        # Get shipment data
        shipment = await mcp_client.get_shipment("TX-CHI-2025-001")
        if shipment:
            print(f"Shipment: {shipment.shipment_id}")
            print(f"Status: {shipment.status}")
            print(f"Temperature: {shipment.current_temperature}°C")
        
        # Get sensor reading
        sensor = await mcp_client.get_sensor_reading("TEMP-001")
        if sensor:
            print(f"Sensor: {sensor.sensor_id}")
            print(f"Value: {sensor.value} {sensor.unit}")
            print(f"Status: {sensor.status}")
        
        # Get document
        doc = await mcp_client.get_document("SOP-TEMP-BREACH-001")
        if doc:
            print(f"Document: {doc.title}")
            print(f"Type: {doc.document_type}")
        
    finally:
        await mcp_client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Save as `test_mcp_client.py` and run:

```powershell
python test_mcp_client.py
```

### Advanced Usage: Agent Integration

```python
import asyncio
from glih_backend.config import load_config
from glih_backend.mcp import get_mcp_client

async def anomaly_response_with_mcp(shipment_id: str):
    """
    Example: AnomalyResponder using MCP to gather context.
    """
    config = load_config()
    mcp_client = get_mcp_client(config.get("mcp", {}))
    
    if not mcp_client:
        print("MCP not available, using fallback")
        return
    
    try:
        # 1. Get shipment details from WMS
        shipment = await mcp_client.get_shipment(shipment_id)
        if not shipment:
            print(f"Shipment {shipment_id} not found")
            return
        
        print(f"\n=== Shipment Details ===")
        print(f"ID: {shipment.shipment_id}")
        print(f"Product: {shipment.product_type}")
        print(f"Status: {shipment.status}")
        print(f"Temperature: {shipment.current_temperature}°C")
        print(f"Required Range: {shipment.temperature_range}")
        
        # 2. Get all sensors for this shipment
        sensors = await mcp_client.get_shipment_sensors(shipment_id)
        print(f"\n=== Sensor Readings ({len(sensors)} sensors) ===")
        for sensor in sensors:
            print(f"- {sensor.sensor_type}: {sensor.value} {sensor.unit} ({sensor.status})")
        
        # 3. Check for temperature breach
        temp_min, temp_max = shipment.temperature_range
        if shipment.current_temperature:
            if shipment.current_temperature < temp_min or shipment.current_temperature > temp_max:
                print(f"\n⚠️  TEMPERATURE BREACH DETECTED!")
                
                # 4. Retrieve relevant SOP
                sop_response = await mcp_client.read_resource("docs://sops/temperature-breach")
                if sop_response.success:
                    sop = sop_response.data
                    print(f"\n=== Relevant SOP ===")
                    print(f"Title: {sop['title']}")
                    print(f"First 200 chars: {sop['content'][:200]}...")
                
                # 5. Generate response actions
                print(f"\n=== Recommended Actions ===")
                if abs(shipment.current_temperature - temp_max) > 5:
                    print("1. CRITICAL: Immediate quarantine required")
                    print("2. Notify QA manager and operations director")
                    print("3. Contact customer within 2 hours")
                elif abs(shipment.current_temperature - temp_max) > 2:
                    print("1. MAJOR: Quarantine affected products")
                    print("2. Notify quality assurance team")
                    print("3. Conduct detailed product inspection")
                else:
                    print("1. MINOR: Continue monitoring every 15 minutes")
                    print("2. Document in incident log")
            else:
                print(f"\n✅ Temperature within acceptable range")
    
    finally:
        await mcp_client.close()

if __name__ == "__main__":
    # Test with breach scenario
    asyncio.run(anomaly_response_with_mcp("CHI-ATL-2025-089"))
```

Save as `test_mcp_agent.py` and run:

```powershell
python test_mcp_agent.py
```

---

## Troubleshooting

### Issue: "Connection refused" errors

**Cause**: MCP servers not running

**Fix**:
1. Ensure all 3 MCP servers are running in separate terminals
2. Check ports 8080, 8081, 8082 are not in use by other applications
3. Verify firewall allows local connections

### Issue: "MCP is not enabled"

**Cause**: MCP not enabled in configuration

**Fix**:
1. Edit `config/glih.toml`
2. Set `[mcp] enabled = true`
3. Set each server's `enabled = true`
4. Restart GLIH backend

### Issue: "Module 'mcp' not found"

**Cause**: MCP package not installed

**Fix**:
```powershell
pip install mcp httpx
# Or reinstall backend
pip install -e glih-backend
```

### Issue: Slow response times

**Cause**: Network latency or server overload

**Fix**:
1. Increase timeout in config: `timeout_seconds = 60`
2. Enable caching: `cache_ttl_seconds = 600`
3. Check MCP server logs for errors

---

## Production Deployment

### Security Considerations

1. **Authentication**: Add API keys to MCP servers
   ```python
   # In MCP server
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("MCP_API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

2. **TLS/HTTPS**: Use HTTPS for all MCP servers in production
   ```toml
   [[mcp.servers]]
   url = "https://mcp-wms.lineage.com"  # Not http://
   ```

3. **Network Isolation**: Deploy MCP servers in private VPC
   - Only GLIH backend can access MCP servers
   - No public internet access

4. **Rate Limiting**: Add rate limiting to prevent abuse
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

### Monitoring

1. **Health Checks**: Monitor all MCP servers
   ```powershell
   # Add to monitoring system
   curl http://mcp-wms.lineage.local:8080/health
   ```

2. **Metrics**: Track request latency and error rates
   - Average response time
   - Cache hit rate
   - Error rate by server

3. **Logging**: Centralize logs from all MCP servers
   - Use ELK stack or CloudWatch
   - Alert on errors and slow requests

### Scaling

1. **Horizontal Scaling**: Run multiple instances of each MCP server
   ```
   Load Balancer
   ├── MCP-WMS-1 (8080)
   ├── MCP-WMS-2 (8080)
   └── MCP-WMS-3 (8080)
   ```

2. **Caching**: Use Redis for shared cache across GLIH instances
   ```python
   import redis
   cache = redis.Redis(host='localhost', port=6379)
   ```

3. **Database Connection Pooling**: Optimize database connections in MCP servers

---

## Next Steps

1. ✅ **Test basic MCP functionality** (this guide)
2. ⬜ **Integrate MCP into agents** (AnomalyResponder, RouteAdvisor, etc.)
3. ⬜ **Add API endpoints** for MCP queries in GLIH backend
4. ⬜ **Connect to real systems** (replace mock servers with actual WMS/IoT/docs)
5. ⬜ **Deploy to production** (cloud infrastructure, security hardening)

---

## Resources

- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **GLIH MCP Client**: `glih-backend/src/glih_backend/mcp/client.py`
- **MCP Schemas**: `glih-backend/src/glih_backend/mcp/schemas.py`
- **Example Servers**: `mcp-servers/` directory

---

**Questions?** Contact the GLIH team or refer to README_LINEAGE.md for more details.
