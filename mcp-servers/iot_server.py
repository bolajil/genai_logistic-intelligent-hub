"""
Example MCP Server for IoT sensor data.

This is a mock implementation for demonstration purposes.
In production, this would connect to actual IoT sensor networks.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uvicorn
import random

app = FastAPI(title="Lineage IoT MCP Server", version="1.0.0")


# Mock sensor data
def generate_sensor_reading(sensor_id: str, sensor_type: str, shipment_id: str) -> Dict[str, Any]:
    """Generate mock sensor reading."""
    now = datetime.now()
    
    if sensor_type == "temperature":
        # Simulate temperature readings
        if "CHI-ATL" in shipment_id:
            value = 5.2  # Breach scenario
            status = "critical"
        else:
            value = random.uniform(-2, 2)
            status = "normal"
        
        return {
            "sensor_id": sensor_id,
            "sensor_type": "temperature",
            "shipment_id": shipment_id,
            "facility": None,
            "timestamp": now.isoformat(),
            "value": value,
            "unit": "celsius",
            "status": status,
            "metadata": {"accuracy": 0.1}
        }
    
    elif sensor_type == "gps":
        # Simulate GPS readings
        locations = {
            "TX-CHI-2025-001": (41.8781, -87.6298),  # Chicago
            "CHI-ATL-2025-089": (33.7490, -84.3880),  # Atlanta
            "LA-SEA-2025-156": (47.6062, -122.3321),  # Seattle
        }
        lat, lon = locations.get(shipment_id, (0.0, 0.0))
        
        return {
            "sensor_id": sensor_id,
            "sensor_type": "gps",
            "shipment_id": shipment_id,
            "facility": None,
            "timestamp": now.isoformat(),
            "value": f"{lat},{lon}",
            "unit": "coordinates",
            "status": "normal",
            "metadata": {"accuracy_meters": 5}
        }
    
    elif sensor_type == "door":
        # Simulate door sensor
        return {
            "sensor_id": sensor_id,
            "sensor_type": "door",
            "shipment_id": shipment_id,
            "facility": None,
            "timestamp": now.isoformat(),
            "value": 0,  # 0 = closed, 1 = open
            "unit": "boolean",
            "status": "normal",
            "metadata": {}
        }
    
    return {}


MOCK_SENSORS = {
    "TEMP-001": {"type": "temperature", "shipment": "TX-CHI-2025-001"},
    "TEMP-002": {"type": "temperature", "shipment": "CHI-ATL-2025-089"},
    "TEMP-003": {"type": "temperature", "shipment": "LA-SEA-2025-156"},
    "GPS-001": {"type": "gps", "shipment": "TX-CHI-2025-001"},
    "GPS-002": {"type": "gps", "shipment": "CHI-ATL-2025-089"},
    "GPS-003": {"type": "gps", "shipment": "LA-SEA-2025-156"},
    "DOOR-001": {"type": "door", "shipment": "TX-CHI-2025-001"},
    "DOOR-002": {"type": "door", "shipment": "CHI-ATL-2025-089"},
    "DOOR-003": {"type": "door", "shipment": "LA-SEA-2025-156"},
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Lineage IoT MCP Server",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/resources")
async def list_resources():
    """List available IoT sensor resources."""
    resources = []
    
    for sensor_id, info in MOCK_SENSORS.items():
        resources.append({
            "uri": f"iot://sensors/{sensor_id}",
            "name": f"Sensor {sensor_id}",
            "description": f"{info['type']} sensor for {info['shipment']}",
            "mime_type": "application/json",
            "metadata": {"type": info["type"], "shipment": info["shipment"]}
        })
    
    return {"resources": resources}


@app.get("/resources/sensors/{sensor_id}")
async def get_sensor(sensor_id: str):
    """Get sensor reading by ID."""
    if sensor_id not in MOCK_SENSORS:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    
    info = MOCK_SENSORS[sensor_id]
    return generate_sensor_reading(sensor_id, info["type"], info["shipment"])


@app.get("/query")
async def query_sensors(
    pattern: str = Query(..., description="URI pattern to match"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    shipment_id: Optional[str] = Query(None, description="Filter by shipment ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Query sensors with filters."""
    results = []
    
    for sensor_id, info in MOCK_SENSORS.items():
        # Apply filters
        if sensor_type and info["type"] != sensor_type:
            continue
        if shipment_id and info["shipment"] != shipment_id:
            continue
        
        reading = generate_sensor_reading(sensor_id, info["type"], info["shipment"])
        
        if status and reading.get("status") != status:
            continue
        
        results.append(reading)
    
    return {"results": results}


@app.get("/subscribe")
async def subscribe(
    pattern: str = Query(..., description="URI pattern to subscribe to"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    shipment_id: Optional[str] = Query(None, description="Filter by shipment ID")
):
    """
    Subscribe to sensor updates (streaming endpoint).
    
    Note: This is a simplified mock. In production, this would use
    Server-Sent Events (SSE) or WebSockets for real-time streaming.
    """
    import json
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        """Generate sensor readings every 5 seconds."""
        while True:
            for sensor_id, info in MOCK_SENSORS.items():
                # Apply filters
                if sensor_type and info["type"] != sensor_type:
                    continue
                if shipment_id and info["shipment"] != shipment_id:
                    continue
                
                reading = generate_sensor_reading(sensor_id, info["type"], info["shipment"])
                yield f"{json.dumps(reading)}\n"
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sensors_count": len(MOCK_SENSORS)
    }


if __name__ == "__main__":
    print("Starting Lineage IoT MCP Server on http://localhost:8081")
    print("Available sensors:")
    for sensor_id, info in MOCK_SENSORS.items():
        print(f"  - {sensor_id}: {info['type']} ({info['shipment']})")
    
    uvicorn.run(app, host="0.0.0.0", port=8081)
