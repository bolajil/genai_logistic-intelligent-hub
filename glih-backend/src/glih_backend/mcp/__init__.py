"""
Model Context Protocol (MCP) integration for GLIH.

This module provides the MCP client layer for connecting to external
data sources (WMS, IoT sensors, documents) through standardized MCP servers.
"""

from .client import MCPClient
from .schemas import (
    ShipmentResource,
    SensorResource,
    DocumentResource,
    MCPResource,
)

__all__ = [
    "MCPClient",
    "ShipmentResource",
    "SensorResource",
    "DocumentResource",
    "MCPResource",
]
