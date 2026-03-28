"""
MCP Client Module for GLIH
Provides graceful connections to external MCP servers:
- GPS-Trace: Truck/vehicle tracking
- OpenWeatherMap: Weather forecasts for route planning
- Custom IoT: Temperature sensors, door status

All connections are optional and fail gracefully when API keys are not configured.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


@dataclass
class MCPConnectionStatus:
    """Status of an MCP connection"""
    name: str
    connected: bool = False
    last_check: Optional[datetime] = None
    error: Optional[str] = None
    api_key_configured: bool = False


@dataclass
class VehicleLocation:
    """GPS location data for a vehicle/truck"""
    vehicle_id: str
    lat: float
    lon: float
    speed_kmh: float = 0.0
    heading: float = 0.0
    timestamp: Optional[datetime] = None
    engine_hours: float = 0.0
    mileage_km: float = 0.0
    geofence: Optional[str] = None


@dataclass
class WeatherData:
    """Weather data for a location"""
    lat: float
    lon: float
    temp_c: float
    feels_like_c: float
    humidity: int
    description: str
    wind_speed_kmh: float
    timestamp: Optional[datetime] = None
    forecast_hours: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IoTSensorReading:
    """IoT sensor reading (temperature, door, etc.)"""
    sensor_id: str
    sensor_type: str  # temperature, door, humidity, gps
    value: Any
    unit: str
    timestamp: Optional[datetime] = None
    device_id: Optional[str] = None
    location: Optional[str] = None


class GPSTraceMCPClient:
    """
    MCP Client for GPS-Trace vehicle tracking.
    Connects to https://mcp.gps-trace.com/mcp
    """
    
    BASE_URL = "https://mcp.gps-trace.com"
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("GPS_TRACE_API_TOKEN", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_token)
    
    async def connect(self) -> bool:
        """Attempt to connect to GPS-Trace MCP server"""
        if not self.is_configured:
            logger.info("GPS-Trace: No API token configured, skipping connection")
            return False
        
        try:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=30.0
            )
            # Test connection
            response = await self._client.get("/health")
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("GPS-Trace: Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"GPS-Trace: Connection failed - {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
            self._connected = False
    
    async def get_vehicles(self) -> List[VehicleLocation]:
        """Get all tracked vehicles"""
        if not self._connected or not self._client:
            return []
        
        try:
            response = await self._client.post("/mcp", json={
                "method": "tools/call",
                "params": {"name": "get_units", "arguments": {}}
            })
            if response.status_code == 200:
                data = response.json()
                return self._parse_vehicles(data)
        except Exception as e:
            logger.error(f"GPS-Trace: Failed to get vehicles - {e}")
        return []
    
    async def get_vehicle_location(self, vehicle_id: str) -> Optional[VehicleLocation]:
        """Get location for a specific vehicle"""
        if not self._connected or not self._client:
            return None
        
        try:
            response = await self._client.post("/mcp", json={
                "method": "tools/call",
                "params": {"name": "get_unit_info", "arguments": {"unit_id": vehicle_id}}
            })
            if response.status_code == 200:
                data = response.json()
                vehicles = self._parse_vehicles(data)
                return vehicles[0] if vehicles else None
        except Exception as e:
            logger.error(f"GPS-Trace: Failed to get vehicle {vehicle_id} - {e}")
        return None
    
    def _parse_vehicles(self, data: Dict) -> List[VehicleLocation]:
        """Parse GPS-Trace response into VehicleLocation objects"""
        vehicles = []
        try:
            units = data.get("result", {}).get("units", [])
            for unit in units:
                vehicles.append(VehicleLocation(
                    vehicle_id=str(unit.get("id", "")),
                    lat=float(unit.get("lat", 0)),
                    lon=float(unit.get("lon", 0)),
                    speed_kmh=float(unit.get("speed", 0)),
                    heading=float(unit.get("heading", 0)),
                    timestamp=datetime.now(),
                    engine_hours=float(unit.get("engine_hours", 0)),
                    mileage_km=float(unit.get("mileage", 0)),
                ))
        except Exception as e:
            logger.error(f"GPS-Trace: Parse error - {e}")
        return vehicles
    
    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="GPS-Trace",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class OpenWeatherMCPClient:
    """
    MCP Client for OpenWeatherMap.
    Provides weather data for route planning and spoilage risk assessment.
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def connect(self) -> bool:
        """Test OpenWeatherMap API connection"""
        if not self.is_configured:
            logger.info("OpenWeatherMap: No API key configured, skipping connection")
            return False
        
        try:
            self._client = httpx.AsyncClient(timeout=30.0)
            # Test with a simple weather request
            response = await self._client.get(
                f"{self.BASE_URL}/weather",
                params={"q": "London", "appid": self.api_key}
            )
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("OpenWeatherMap: Connected successfully")
            else:
                logger.warning(f"OpenWeatherMap: API returned {response.status_code}")
            return self._connected
        except Exception as e:
            logger.warning(f"OpenWeatherMap: Connection failed - {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
            self._connected = False
    
    async def get_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get current weather for coordinates"""
        if not self._connected or not self._client:
            return None
        
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/weather",
                params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
            )
            if response.status_code == 200:
                data = response.json()
                return WeatherData(
                    lat=lat,
                    lon=lon,
                    temp_c=data["main"]["temp"],
                    feels_like_c=data["main"]["feels_like"],
                    humidity=data["main"]["humidity"],
                    description=data["weather"][0]["description"],
                    wind_speed_kmh=data["wind"]["speed"] * 3.6,
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"OpenWeatherMap: Failed to get weather - {e}")
        return None
    
    async def get_forecast(self, lat: float, lon: float, hours: int = 24) -> Optional[WeatherData]:
        """Get weather forecast for coordinates"""
        if not self._connected or not self._client:
            return None
        
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/forecast",
                params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
            )
            if response.status_code == 200:
                data = response.json()
                current = data["list"][0]
                forecast_hours = []
                for item in data["list"][:hours // 3]:  # 3-hour intervals
                    forecast_hours.append({
                        "time": item["dt_txt"],
                        "temp_c": item["main"]["temp"],
                        "description": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"]
                    })
                return WeatherData(
                    lat=lat,
                    lon=lon,
                    temp_c=current["main"]["temp"],
                    feels_like_c=current["main"]["feels_like"],
                    humidity=current["main"]["humidity"],
                    description=current["weather"][0]["description"],
                    wind_speed_kmh=current["wind"]["speed"] * 3.6,
                    timestamp=datetime.now(),
                    forecast_hours=forecast_hours
                )
        except Exception as e:
            logger.error(f"OpenWeatherMap: Failed to get forecast - {e}")
        return None
    
    async def get_route_weather_risk(self, waypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Assess weather risk along a route.
        Returns risk score and warnings for each waypoint.
        """
        if not self._connected:
            return {"risk_score": 0, "warnings": [], "available": False}
        
        warnings = []
        max_risk = 0
        
        for i, wp in enumerate(waypoints):
            weather = await self.get_weather(wp["lat"], wp["lon"])
            if weather:
                # Check for conditions that affect cold chain
                if weather.temp_c > 30:
                    warnings.append(f"Waypoint {i+1}: High ambient temp ({weather.temp_c}°C)")
                    max_risk = max(max_risk, 0.6)
                if weather.temp_c > 35:
                    max_risk = max(max_risk, 0.8)
                if "rain" in weather.description.lower() or "storm" in weather.description.lower():
                    warnings.append(f"Waypoint {i+1}: {weather.description}")
                    max_risk = max(max_risk, 0.4)
        
        return {
            "risk_score": max_risk,
            "warnings": warnings,
            "available": True,
            "waypoints_checked": len(waypoints)
        }
    
    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="OpenWeatherMap",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class LineageIoTMCPClient:
    """
    Custom MCP Client for Lineage IoT sensors.
    Connects to MQTT broker or custom IoT gateway for:
    - Temperature sensors in trucks/warehouses
    - Door open/close sensors
    - Humidity sensors
    """
    
    def __init__(
        self,
        mqtt_broker: Optional[str] = None,
        mqtt_port: int = 1883,
        mqtt_username: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.mqtt_broker = mqtt_broker or os.getenv("IOT_MQTT_BROKER", "")
        self.mqtt_port = mqtt_port or int(os.getenv("IOT_MQTT_PORT", "1883"))
        self.mqtt_username = mqtt_username or os.getenv("IOT_MQTT_USERNAME", "")
        self.mqtt_password = mqtt_password or os.getenv("IOT_MQTT_PASSWORD", "")
        self.api_endpoint = api_endpoint or os.getenv("IOT_API_ENDPOINT", "")
        self.api_key = api_key or os.getenv("IOT_API_KEY", "")
        
        self._connected = False
        self._client: Optional[httpx.AsyncClient] = None
        self._sensor_cache: Dict[str, IoTSensorReading] = {}
    
    @property
    def is_configured(self) -> bool:
        return bool(self.mqtt_broker) or bool(self.api_endpoint)
    
    async def connect(self) -> bool:
        """Connect to IoT gateway"""
        if not self.is_configured:
            logger.info("Lineage IoT: No broker/endpoint configured, skipping connection")
            return False
        
        # Try HTTP API first (easier than MQTT in async context)
        if self.api_endpoint:
            try:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                self._client = httpx.AsyncClient(
                    base_url=self.api_endpoint,
                    headers=headers,
                    timeout=30.0
                )
                response = await self._client.get("/health")
                self._connected = response.status_code in [200, 204]
                if self._connected:
                    logger.info("Lineage IoT: Connected to API endpoint")
                return self._connected
            except Exception as e:
                logger.warning(f"Lineage IoT: API connection failed - {e}")
        
        # MQTT connection would go here (requires paho-mqtt or aiomqtt)
        if self.mqtt_broker:
            logger.info(f"Lineage IoT: MQTT broker configured ({self.mqtt_broker}), but MQTT client not implemented yet")
            # TODO: Implement MQTT connection when ready
        
        return False
    
    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
    
    async def get_sensor_reading(self, sensor_id: str) -> Optional[IoTSensorReading]:
        """Get latest reading from a specific sensor"""
        if not self._connected or not self._client:
            return self._sensor_cache.get(sensor_id)
        
        try:
            response = await self._client.get(f"/sensors/{sensor_id}/latest")
            if response.status_code == 200:
                data = response.json()
                reading = IoTSensorReading(
                    sensor_id=sensor_id,
                    sensor_type=data.get("type", "unknown"),
                    value=data.get("value"),
                    unit=data.get("unit", ""),
                    timestamp=datetime.now(),
                    device_id=data.get("device_id"),
                    location=data.get("location")
                )
                self._sensor_cache[sensor_id] = reading
                return reading
        except Exception as e:
            logger.error(f"Lineage IoT: Failed to get sensor {sensor_id} - {e}")
        return None
    
    async def get_all_sensors(self, device_id: Optional[str] = None) -> List[IoTSensorReading]:
        """Get all sensor readings, optionally filtered by device"""
        if not self._connected or not self._client:
            return list(self._sensor_cache.values())
        
        try:
            params = {}
            if device_id:
                params["device_id"] = device_id
            response = await self._client.get("/sensors", params=params)
            if response.status_code == 200:
                data = response.json()
                readings = []
                for item in data.get("sensors", []):
                    reading = IoTSensorReading(
                        sensor_id=item["id"],
                        sensor_type=item.get("type", "unknown"),
                        value=item.get("value"),
                        unit=item.get("unit", ""),
                        timestamp=datetime.now(),
                        device_id=item.get("device_id"),
                        location=item.get("location")
                    )
                    readings.append(reading)
                    self._sensor_cache[reading.sensor_id] = reading
                return readings
        except Exception as e:
            logger.error(f"Lineage IoT: Failed to get sensors - {e}")
        return []
    
    async def get_temperature_sensors(self, location: Optional[str] = None) -> List[IoTSensorReading]:
        """Get all temperature sensor readings"""
        all_sensors = await self.get_all_sensors()
        return [s for s in all_sensors if s.sensor_type == "temperature" 
                and (location is None or s.location == location)]
    
    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Lineage IoT",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class MCPClientManager:
    """
    Central manager for all MCP client connections.
    Handles initialization, connection status, and graceful fallback to demo mode.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize clients with config or env vars
        mcp_config = self.config.get("mcp", {}).get("connectors", {})
        
        self.gps_trace = GPSTraceMCPClient(
            api_token=mcp_config.get("gps_trace", {}).get("api_token")
        )
        self.weather = OpenWeatherMCPClient(
            api_key=mcp_config.get("openweathermap", {}).get("api_key")
        )
        self.iot = LineageIoTMCPClient(
            mqtt_broker=mcp_config.get("iot", {}).get("mqtt_broker"),
            mqtt_port=mcp_config.get("iot", {}).get("mqtt_port", 1883),
            api_endpoint=mcp_config.get("iot", {}).get("api_endpoint"),
            api_key=mcp_config.get("iot", {}).get("api_key")
        )
        
        self._initialized = False
    
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all MCP connections. Returns status of each."""
        results = {}
        
        # Connect to each service (failures are graceful)
        results["gps_trace"] = await self.gps_trace.connect()
        results["weather"] = await self.weather.connect()
        results["iot"] = await self.iot.connect()
        
        self._initialized = True
        
        # Log summary
        configured = sum(1 for v in results.values() if v)
        logger.info(f"MCP Manager: {configured}/{len(results)} connections active")
        
        return results
    
    async def shutdown(self):
        """Disconnect all MCP clients"""
        await self.gps_trace.disconnect()
        await self.weather.disconnect()
        await self.iot.disconnect()
        self._initialized = False
    
    def get_all_status(self) -> List[MCPConnectionStatus]:
        """Get status of all MCP connections"""
        return [
            self.gps_trace.get_status(),
            self.weather.get_status(),
            self.iot.get_status()
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize status for API response"""
        return {
            "initialized": self._initialized,
            "connections": [
                {
                    "name": s.name,
                    "connected": s.connected,
                    "configured": s.api_key_configured,
                    "last_check": s.last_check.isoformat() if s.last_check else None,
                    "error": s.error
                }
                for s in self.get_all_status()
            ]
        }


# Global instance (lazy initialized)
_mcp_manager: Optional[MCPClientManager] = None


def get_mcp_manager(config: Optional[Dict[str, Any]] = None) -> MCPClientManager:
    """Get or create the global MCP manager instance"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager(config)
    return _mcp_manager


async def init_mcp_clients(config: Optional[Dict[str, Any]] = None) -> MCPClientManager:
    """Initialize and connect MCP clients"""
    manager = get_mcp_manager(config)
    await manager.initialize()
    return manager
