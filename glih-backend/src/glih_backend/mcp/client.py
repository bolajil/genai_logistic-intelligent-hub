"""
MCP Client implementation for GLIH.

Provides a client for connecting to MCP servers and accessing resources.
"""

import logging
from typing import Any, Dict, List, Optional, AsyncIterator
import httpx
from datetime import datetime, timedelta

from .schemas import (
    MCPResource,
    MCPServerConfig,
    MCPResponse,
    ShipmentResource,
    SensorResource,
    DocumentResource,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for interacting with Model Context Protocol servers.
    
    Provides methods to:
    - List available resources
    - Read resource data
    - Subscribe to resource updates
    - Query resources with filters
    """
    
    def __init__(
        self,
        servers: List[Dict[str, Any]],
        timeout: int = 30,
        retry_attempts: int = 3,
        cache_ttl: int = 300,
    ):
        """
        Initialize MCP client.
        
        Args:
            servers: List of MCP server configurations
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            cache_ttl: Cache time-to-live in seconds
        """
        self.servers = [MCPServerConfig(**s) for s in servers if s.get("enabled", True)]
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"Initialized MCP client with {len(self.servers)} servers")
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    def _get_server_by_name(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name."""
        for server in self.servers:
            if server.name == server_name:
                return server
        return None
    
    def _parse_uri(self, uri: str) -> tuple[str, str]:
        """
        Parse MCP URI into server name and resource path.
        
        Args:
            uri: Resource URI (e.g., "wms://shipments/123")
        
        Returns:
            Tuple of (server_name, resource_path)
        """
        if "://" not in uri:
            raise ValueError(f"Invalid MCP URI format: {uri}")
        
        protocol, path = uri.split("://", 1)
        
        # Map protocol to server name
        protocol_map = {
            "wms": "lineage-wms",
            "iot": "lineage-iot",
            "docs": "lineage-docs",
        }
        
        server_name = protocol_map.get(protocol, protocol)
        return server_name, path
    
    def _get_cache_key(self, uri: str) -> str:
        """Generate cache key for URI."""
        return f"mcp:{uri}"
    
    def _get_cached(self, uri: str) -> Optional[Any]:
        """Get cached resource if available and not expired."""
        cache_key = self._get_cache_key(uri)
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for {uri}")
                return data
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
        return None
    
    def _set_cached(self, uri: str, data: Any):
        """Cache resource data."""
        cache_key = self._get_cache_key(uri)
        self._cache[cache_key] = (data, datetime.now())
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """
        List available resources from MCP servers.
        
        Args:
            server_name: Optional server name to query (queries all if None)
        
        Returns:
            List of available resources
        """
        resources = []
        servers = [self._get_server_by_name(server_name)] if server_name else self.servers
        
        for server in servers:
            if not server:
                continue
            
            try:
                response = await self._client.get(f"{server.url}/resources")
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("resources", []):
                    resources.append(MCPResource(**item))
                
                logger.info(f"Listed {len(data.get('resources', []))} resources from {server.name}")
            
            except Exception as e:
                logger.error(f"Failed to list resources from {server.name}: {e}")
        
        return resources
    
    async def read_resource(self, uri: str, use_cache: bool = True) -> MCPResponse:
        """
        Read a resource from an MCP server.
        
        Args:
            uri: Resource URI (e.g., "wms://shipments/TX-CHI-2025-001")
            use_cache: Whether to use cached data if available
        
        Returns:
            MCPResponse with resource data
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached(uri)
            if cached:
                return MCPResponse(success=True, data=cached)
        
        # Parse URI and get server
        server_name, resource_path = self._parse_uri(uri)
        server = self._get_server_by_name(server_name)
        
        if not server:
            return MCPResponse(
                success=False,
                error=f"Server '{server_name}' not found or not enabled"
            )
        
        # Make request with retries
        for attempt in range(self.retry_attempts):
            try:
                response = await self._client.get(
                    f"{server.url}/resources/{resource_path}"
                )
                response.raise_for_status()
                data = response.json()
                
                # Cache the result
                self._set_cached(uri, data)
                
                logger.info(f"Read resource {uri} from {server.name}")
                return MCPResponse(success=True, data=data)
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return MCPResponse(
                        success=False,
                        error=f"Resource not found: {uri}"
                    )
                logger.warning(f"HTTP error reading {uri} (attempt {attempt + 1}): {e}")
            
            except Exception as e:
                logger.warning(f"Error reading {uri} (attempt {attempt + 1}): {e}")
        
        return MCPResponse(
            success=False,
            error=f"Failed to read resource after {self.retry_attempts} attempts"
        )
    
    async def query_resources(
        self,
        uri_pattern: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MCPResponse]:
        """
        Query resources matching a pattern.
        
        Args:
            uri_pattern: URI pattern with wildcards (e.g., "iot://sensors/temp/*")
            filters: Optional filters to apply
        
        Returns:
            List of matching resources
        """
        server_name, pattern = self._parse_uri(uri_pattern)
        server = self._get_server_by_name(server_name)
        
        if not server:
            logger.error(f"Server '{server_name}' not found")
            return []
        
        try:
            params = {"pattern": pattern}
            if filters:
                params.update(filters)
            
            response = await self._client.get(
                f"{server.url}/query",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(MCPResponse(success=True, data=item))
            
            logger.info(f"Query {uri_pattern} returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Failed to query {uri_pattern}: {e}")
            return []
    
    async def subscribe(
        self,
        uri_pattern: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[MCPResponse]:
        """
        Subscribe to resource updates (streaming).
        
        Args:
            uri_pattern: URI pattern to subscribe to
            filters: Optional filters
        
        Yields:
            MCPResponse objects as updates arrive
        """
        server_name, pattern = self._parse_uri(uri_pattern)
        server = self._get_server_by_name(server_name)
        
        if not server:
            logger.error(f"Server '{server_name}' not found")
            return
        
        try:
            params = {"pattern": pattern}
            if filters:
                params.update(filters)
            
            async with self._client.stream(
                "GET",
                f"{server.url}/subscribe",
                params=params
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            import json
                            data = json.loads(line)
                            yield MCPResponse(success=True, data=data)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in stream: {line}")
        
        except Exception as e:
            logger.error(f"Subscription error for {uri_pattern}: {e}")
    
    # Convenience methods for specific resource types
    
    async def get_shipment(self, shipment_id: str) -> Optional[ShipmentResource]:
        """Get shipment data by ID."""
        response = await self.read_resource(f"wms://shipments/{shipment_id}")
        if response.success and response.data:
            return ShipmentResource(**response.data)
        return None
    
    async def get_sensor_reading(self, sensor_id: str) -> Optional[SensorResource]:
        """Get latest sensor reading by ID."""
        response = await self.read_resource(f"iot://sensors/{sensor_id}")
        if response.success and response.data:
            return SensorResource(**response.data)
        return None
    
    async def get_document(self, document_id: str) -> Optional[DocumentResource]:
        """Get document by ID."""
        response = await self.read_resource(f"docs://documents/{document_id}")
        if response.success and response.data:
            return DocumentResource(**response.data)
        return None
    
    async def get_shipment_sensors(self, shipment_id: str) -> List[SensorResource]:
        """Get all sensors for a shipment."""
        results = await self.query_resources(
            f"iot://sensors/*",
            filters={"shipment_id": shipment_id}
        )
        
        sensors = []
        for result in results:
            if result.success and result.data:
                sensors.append(SensorResource(**result.data))
        
        return sensors


# Singleton instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client(config: Dict[str, Any]) -> Optional[MCPClient]:
    """
    Get or create MCP client singleton.
    
    Args:
        config: MCP configuration from glih.toml
    
    Returns:
        MCPClient instance or None if MCP is disabled
    """
    global _mcp_client
    
    if not config.get("enabled", False):
        logger.info("MCP is disabled in configuration")
        return None
    
    if _mcp_client is None:
        _mcp_client = MCPClient(
            servers=config.get("servers", []),
            timeout=config.get("timeout_seconds", 30),
            retry_attempts=config.get("retry_attempts", 3),
            cache_ttl=config.get("cache_ttl_seconds", 300),
        )
    
    return _mcp_client
