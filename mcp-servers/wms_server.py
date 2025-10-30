"""
Example MCP Server for WMS/TMS data.

This is a mock implementation for demonstration purposes.
In production, this would connect to actual Lineage WMS/TMS systems.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

app = FastAPI(title="Lineage WMS MCP Server", version="1.0.0")


# Mock data storage
MOCK_SHIPMENTS = {
    "TX-CHI-2025-001": {
        "shipment_id": "TX-CHI-2025-001",
        "origin": "Dallas",
        "destination": "Chicago",
        "product_type": "Seafood",
        "status": "in_transit",
        "temperature_range": [-2, 2],
        "current_temperature": 0.5,
        "current_location": "41.8781,-87.6298",
        "eta": "2025-10-31T14:00:00Z",
        "carrier": "Swift Logistics",
        "driver": "John Smith",
        "metadata": {
            "weight_kg": 5000,
            "container_id": "CONT-8834",
            "priority": "high"
        }
    },
    "CHI-ATL-2025-089": {
        "shipment_id": "CHI-ATL-2025-089",
        "origin": "Chicago",
        "destination": "Atlanta",
        "product_type": "Dairy",
        "status": "in_transit",
        "temperature_range": [0, 4],
        "current_temperature": 5.2,  # Breach!
        "current_location": "33.7490,-84.3880",
        "eta": "2025-10-30T18:00:00Z",
        "carrier": "Cold Chain Express",
        "driver": "Jane Doe",
        "metadata": {
            "weight_kg": 3000,
            "container_id": "CONT-9921",
            "priority": "medium"
        }
    },
    "LA-SEA-2025-156": {
        "shipment_id": "LA-SEA-2025-156",
        "origin": "Los Angeles",
        "destination": "Seattle",
        "product_type": "Frozen Foods",
        "status": "delivered",
        "temperature_range": [-25, -18],
        "current_temperature": -20.0,
        "current_location": "47.6062,-122.3321",
        "eta": "2025-10-29T10:00:00Z",
        "carrier": "Arctic Transport",
        "driver": "Bob Johnson",
        "metadata": {
            "weight_kg": 8000,
            "container_id": "CONT-7712",
            "priority": "low"
        }
    }
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Lineage WMS MCP Server",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/resources")
async def list_resources():
    """List available WMS resources."""
    resources = []
    
    for shipment_id in MOCK_SHIPMENTS.keys():
        resources.append({
            "uri": f"wms://shipments/{shipment_id}",
            "name": f"Shipment {shipment_id}",
            "description": f"Shipment data for {shipment_id}",
            "mime_type": "application/json",
            "metadata": {"type": "shipment"}
        })
    
    return {"resources": resources}


@app.get("/resources/shipments/{shipment_id}")
async def get_shipment(shipment_id: str):
    """Get shipment by ID."""
    if shipment_id not in MOCK_SHIPMENTS:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")
    
    return MOCK_SHIPMENTS[shipment_id]


@app.get("/query")
async def query_shipments(
    pattern: str = Query(..., description="URI pattern to match"),
    status: Optional[str] = Query(None, description="Filter by status"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    origin: Optional[str] = Query(None, description="Filter by origin"),
    destination: Optional[str] = Query(None, description="Filter by destination")
):
    """Query shipments with filters."""
    results = []
    
    for shipment in MOCK_SHIPMENTS.values():
        # Apply filters
        if status and shipment["status"] != status:
            continue
        if product_type and shipment["product_type"] != product_type:
            continue
        if origin and shipment["origin"] != origin:
            continue
        if destination and shipment["destination"] != destination:
            continue
        
        results.append(shipment)
    
    return {"results": results}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "shipments_count": len(MOCK_SHIPMENTS)
    }


if __name__ == "__main__":
    print("Starting Lineage WMS MCP Server on http://localhost:8080")
    print("Available shipments:")
    for shipment_id in MOCK_SHIPMENTS.keys():
        print(f"  - {shipment_id}")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
