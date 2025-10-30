"""
Example MCP Server for document storage.

This is a mock implementation for demonstration purposes.
In production, this would connect to SharePoint, S3, or other document storage.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

app = FastAPI(title="Lineage Documents MCP Server", version="1.0.0")


# Mock document storage
MOCK_DOCUMENTS = {
    "SOP-TEMP-BREACH-001": {
        "document_id": "SOP-TEMP-BREACH-001",
        "document_type": "sop",
        "title": "Temperature Breach Response Protocol",
        "content": """
STANDARD OPERATING PROCEDURE: Temperature Breach Response

1. IMMEDIATE ACTIONS (Within 5 minutes)
   - Document breach time, duration, and temperature
   - Verify sensor accuracy with backup thermometer
   - Notify shift supervisor immediately

2. ASSESSMENT (Within 15 minutes)
   - Determine product type and temperature requirements
   - Calculate total exposure time above threshold
   - Assess product condition (visual inspection)

3. RESPONSE ACTIONS
   For Minor Breach (< 2°C over, < 30 min):
   - Continue monitoring every 15 minutes
   - Document in incident log
   
   For Major Breach (2-5°C over, or > 30 min):
   - Quarantine affected products
   - Notify quality assurance team
   - Conduct detailed product inspection
   
   For Critical Breach (> 5°C over, or > 60 min):
   - IMMEDIATE QUARANTINE - Do not release
   - Notify QA manager and operations director
   - Initiate product disposition process
   - Contact customer within 2 hours

4. DOCUMENTATION
   - Complete Incident Report Form IR-2025
   - Attach sensor data logs
   - Photograph affected products
   - Update shipment tracking system

5. FOLLOW-UP
   - Root cause analysis within 24 hours
   - Corrective action plan within 48 hours
   - Update customer within 24 hours
        """,
        "url": "https://docs.lineage.com/sops/temp-breach-001",
        "shipment_id": None,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2025-10-01T14:30:00Z",
        "tags": ["sop", "temperature", "breach", "response", "cold-chain"],
        "metadata": {
            "version": "2.1",
            "author": "Quality Assurance Team",
            "approval_date": "2025-10-01"
        }
    },
    "INV-2025-8834": {
        "document_id": "INV-2025-8834",
        "document_type": "invoice",
        "title": "Invoice #2025-8834 - Seafood Shipment",
        "content": """
INVOICE #2025-8834
Date: October 28, 2025

From: Dallas Distribution Center
To: Chicago Hub

Shipment ID: TX-CHI-2025-001
Product: Fresh Seafood (Salmon, Cod, Shrimp)
Weight: 5,000 kg
Temperature Range: -2°C to 2°C

Line Items:
1. Atlantic Salmon (2,000 kg) @ $12/kg = $24,000
2. Pacific Cod (1,500 kg) @ $8/kg = $12,000
3. Gulf Shrimp (1,500 kg) @ $15/kg = $22,500

Subtotal: $58,500
Transportation: $2,500
Cold Chain Premium: $1,000
Total: $62,000

Payment Terms: Net 30
Due Date: November 27, 2025
        """,
        "url": "https://docs.lineage.com/invoices/2025/INV-2025-8834.pdf",
        "shipment_id": "TX-CHI-2025-001",
        "created_at": "2025-10-28T09:00:00Z",
        "updated_at": None,
        "tags": ["invoice", "seafood", "dallas", "chicago"],
        "metadata": {
            "amount": 62000,
            "currency": "USD",
            "status": "pending"
        }
    },
    "BOL-CHI-ATL-089": {
        "document_id": "BOL-CHI-ATL-089",
        "document_type": "bol",
        "title": "Bill of Lading - CHI to ATL",
        "content": """
BILL OF LADING
BOL Number: CHI-ATL-089
Date: October 29, 2025

Shipper: Lineage Logistics - Chicago Hub
Consignee: Lineage Logistics - Atlanta Hub

Shipment Details:
- Shipment ID: CHI-ATL-2025-089
- Product: Dairy Products (Milk, Cheese, Yogurt)
- Weight: 3,000 kg
- Container: CONT-9921
- Temperature: 0°C to 4°C

Carrier: Cold Chain Express
Driver: Jane Doe
License Plate: IL-COLD-123

Special Instructions:
- Maintain temperature between 0-4°C at all times
- Monitor temperature every 2 hours
- No stops except for fuel
- Direct route required

Signatures:
Shipper: [Signed] John Manager - Oct 29, 2025 08:00
Driver: [Signed] Jane Doe - Oct 29, 2025 08:15
        """,
        "url": "https://docs.lineage.com/bol/2025/BOL-CHI-ATL-089.pdf",
        "shipment_id": "CHI-ATL-2025-089",
        "created_at": "2025-10-29T08:00:00Z",
        "updated_at": None,
        "tags": ["bol", "dairy", "chicago", "atlanta"],
        "metadata": {
            "carrier": "Cold Chain Express",
            "driver": "Jane Doe",
            "status": "in_transit"
        }
    },
    "SOP-NOTIFICATION-001": {
        "document_id": "SOP-NOTIFICATION-001",
        "document_type": "sop",
        "title": "Customer Notification Escalation Protocol",
        "content": """
STANDARD OPERATING PROCEDURE: Customer Notification Escalation

NOTIFICATION LEVELS:

Level 1 - Informational (No action required)
- Routine status updates
- Delivery confirmations
- Scheduled maintenance notices
Timing: Within 24 hours
Channel: Email

Level 2 - Advisory (Awareness needed)
- Minor delays (< 2 hours)
- Route changes
- Temperature fluctuations (within acceptable range)
Timing: Within 4 hours
Channel: Email + Portal notification

Level 3 - Alert (Action may be needed)
- Moderate delays (2-6 hours)
- Temperature breaches (minor)
- Equipment issues (resolved)
Timing: Within 2 hours
Channel: Email + SMS + Phone call

Level 4 - Critical (Immediate action required)
- Major delays (> 6 hours)
- Temperature breaches (major/critical)
- Product quality concerns
- Shipment damage
Timing: Within 30 minutes
Channel: Phone call + Email + SMS + Portal alert

ESCALATION CONTACTS:
- Operations Manager: (555) 123-4567
- Quality Assurance: (555) 123-4568
- Customer Service Director: (555) 123-4569
- Emergency Hotline: (555) 911-COLD
        """,
        "url": "https://docs.lineage.com/sops/notification-001",
        "shipment_id": None,
        "created_at": "2024-03-20T10:00:00Z",
        "updated_at": "2025-09-15T11:00:00Z",
        "tags": ["sop", "notification", "escalation", "customer-service"],
        "metadata": {
            "version": "1.5",
            "author": "Customer Service Team"
        }
    }
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Lineage Documents MCP Server",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/resources")
async def list_resources():
    """List available document resources."""
    resources = []
    
    for doc_id, doc in MOCK_DOCUMENTS.items():
        resources.append({
            "uri": f"docs://documents/{doc_id}",
            "name": doc["title"],
            "description": f"{doc['document_type'].upper()}: {doc['title']}",
            "mime_type": "application/json",
            "metadata": {
                "type": doc["document_type"],
                "tags": doc["tags"]
            }
        })
    
    return {"resources": resources}


@app.get("/resources/documents/{document_id}")
async def get_document(document_id: str):
    """Get document by ID."""
    if document_id not in MOCK_DOCUMENTS:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    return MOCK_DOCUMENTS[document_id]


@app.get("/resources/sops/{sop_name}")
async def get_sop(sop_name: str):
    """Get SOP by name (convenience endpoint)."""
    # Map common names to document IDs
    sop_map = {
        "temperature-breach": "SOP-TEMP-BREACH-001",
        "notification": "SOP-NOTIFICATION-001",
    }
    
    doc_id = sop_map.get(sop_name)
    if not doc_id or doc_id not in MOCK_DOCUMENTS:
        raise HTTPException(status_code=404, detail=f"SOP '{sop_name}' not found")
    
    return MOCK_DOCUMENTS[doc_id]


@app.get("/query")
async def query_documents(
    pattern: str = Query(..., description="URI pattern to match"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    shipment_id: Optional[str] = Query(None, description="Filter by shipment ID"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")
):
    """Query documents with filters."""
    results = []
    
    tag_list = tags.split(",") if tags else []
    
    for doc in MOCK_DOCUMENTS.values():
        # Apply filters
        if document_type and doc["document_type"] != document_type:
            continue
        if shipment_id and doc.get("shipment_id") != shipment_id:
            continue
        if tag_list and not any(tag in doc["tags"] for tag in tag_list):
            continue
        
        results.append(doc)
    
    return {"results": results}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "documents_count": len(MOCK_DOCUMENTS)
    }


if __name__ == "__main__":
    print("Starting Lineage Documents MCP Server on http://localhost:8082")
    print("Available documents:")
    for doc_id, doc in MOCK_DOCUMENTS.items():
        print(f"  - {doc_id}: {doc['title']} ({doc['document_type']})")
    
    uvicorn.run(app, host="0.0.0.0", port=8082)
