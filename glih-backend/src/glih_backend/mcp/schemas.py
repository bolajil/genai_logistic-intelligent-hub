"""
MCP resource schemas for Lineage Logistics data.

Defines the data structures for resources accessed through MCP servers.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MCPResource(BaseModel):
    """Base class for all MCP resources."""
    
    uri: str = Field(..., description="Resource URI (e.g., wms://shipments/123)")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mime_type: Optional[str] = Field(None, description="MIME type of resource")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ShipmentResource(BaseModel):
    """Shipment data from WMS/TMS."""
    
    shipment_id: str = Field(..., description="Unique shipment identifier")
    origin: str = Field(..., description="Origin facility")
    destination: str = Field(..., description="Destination facility")
    product_type: str = Field(..., description="Product type (Seafood, Dairy, etc.)")
    status: str = Field(..., description="Current status (in_transit, delivered, etc.)")
    temperature_range: List[float] = Field(..., description="Required temperature range [min, max]")
    current_temperature: Optional[float] = Field(None, description="Current temperature reading")
    current_location: Optional[str] = Field(None, description="Current GPS location")
    eta: Optional[datetime] = Field(None, description="Estimated time of arrival")
    carrier: Optional[str] = Field(None, description="Carrier name")
    driver: Optional[str] = Field(None, description="Driver name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SensorResource(BaseModel):
    """IoT sensor data."""
    
    sensor_id: str = Field(..., description="Unique sensor identifier")
    sensor_type: str = Field(..., description="Sensor type (temperature, gps, door)")
    shipment_id: Optional[str] = Field(None, description="Associated shipment ID")
    facility: Optional[str] = Field(None, description="Facility location")
    timestamp: datetime = Field(..., description="Reading timestamp")
    value: Any = Field(..., description="Sensor reading value (float for numeric, string for GPS coordinates, etc.)")
    unit: str = Field(..., description="Unit of measurement")
    status: str = Field(default="normal", description="Sensor status (normal, warning, critical)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentResource(BaseModel):
    """Document metadata and content."""
    
    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="Document type (invoice, bol, sop, etc.)")
    title: str = Field(..., description="Document title")
    content: Optional[str] = Field(None, description="Document text content")
    url: Optional[str] = Field(None, description="Document URL")
    shipment_id: Optional[str] = Field(None, description="Associated shipment ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    
    name: str = Field(..., description="Server name")
    url: str = Field(..., description="Server URL")
    description: Optional[str] = Field(None, description="Server description")
    enabled: bool = Field(default=True, description="Whether server is enabled")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")


class MCPResponse(BaseModel):
    """Response from MCP server."""
    
    success: bool = Field(..., description="Whether request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
