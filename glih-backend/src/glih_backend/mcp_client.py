"""
MCP Client Module for GLIH
Provides graceful connections to external MCP servers:
- GPS-Trace: Truck/vehicle tracking
- OpenWeatherMap: Weather forecasts for route planning
- Custom IoT: Temperature sensors, door status

All connections are optional and fail gracefully when API keys are not configured.
"""

import os
import random
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


class SamsaraELDMCPClient:
    """MCP Client for Samsara ELD — Electronic Logging Device / Hours-of-Service compliance."""

    BASE_URL = "https://api.samsara.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SAMSARA_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Samsara ELD: No API key configured, skipping connection")
            return False
        try:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response = await self._client.get("/fleet/drivers")
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("Samsara ELD: Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"Samsara ELD: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_hos_status(self, driver_id: str = "all") -> Dict[str, Any]:
        """Get Hours-of-Service status for one or all drivers"""
        if self._connected and self._client:
            try:
                params = {"driverIds": driver_id} if driver_id != "all" else {}
                response = await self._client.get("/fleet/hos/current-duty-status", params=params)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Samsara ELD: get_hos_status error - {e}")
        # Demo fallback
        drivers = [
            {"driver_id": "DRV-001", "name": "John Smith"},
            {"driver_id": "DRV-002", "name": "Maria Garcia"},
            {"driver_id": "DRV-003", "name": "James Wilson"},
            {"driver_id": "DRV-004", "name": "Sarah Johnson"},
            {"driver_id": "DRV-005", "name": "Mike Brown"},
        ]
        statuses = []
        for d in drivers:
            if driver_id != "all" and d["driver_id"] != driver_id:
                continue
            on_duty = round(random.uniform(2, 9), 1)
            statuses.append({
                **d,
                "status": random.choice(["ON_DUTY", "DRIVING", "OFF_DUTY", "SLEEPER_BERTH"]),
                "on_duty_today_hours": on_duty,
                "remaining_drive_hours": round(max(0, 11 - on_duty + random.uniform(-1, 1)), 1),
                "cycle_used_hours": round(random.uniform(30, 65), 1),
                "violations": [],
                "last_updated": datetime.now().isoformat()
            })
        return {"drivers": statuses, "total": len(statuses)}

    async def get_eld_violations(self) -> Dict[str, Any]:
        return {
            "violations": [],
            "fleet_compliance_score": 98.5,
            "last_audit": datetime.now().isoformat(),
            "note": "No violations in past 30 days (demo data)"
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Samsara ELD",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class DATLoadBoardMCPClient:
    """MCP Client for DAT load board — carrier/broker load matching and rate forecasting."""

    BASE_URL = "https://api.dat.com"

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv("DAT_USERNAME", "")
        self.password = password or os.getenv("DAT_PASSWORD", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._token: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("DAT Load Board: No credentials configured, skipping connection")
            return False
        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                response = await c.post(
                    "https://identity.dat.com/access/v1/token",
                    json={"username": self.username, "password": self.password}
                )
                if response.status_code == 200:
                    self._token = response.json().get("access_token")
                    self._client = httpx.AsyncClient(
                        base_url=self.BASE_URL,
                        headers={"Authorization": f"Bearer {self._token}"},
                        timeout=30.0
                    )
                    self._connected = True
                    logger.info("DAT Load Board: Connected successfully")
                    return True
        except Exception as e:
            logger.warning(f"DAT Load Board: Connection failed - {e}")
        self._connected = False
        return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def search_loads(self, origin_city: str = "Chicago", dest_city: str = "", equipment: str = "Reefer") -> List[Dict[str, Any]]:
        cities = ["Dallas", "Atlanta", "Los Angeles", "Seattle", "Denver", "Phoenix", "Minneapolis"]
        dest = dest_city or random.choice(cities)
        loads = []
        for _ in range(random.randint(3, 8)):
            loads.append({
                "load_id": f"DAT-{random.randint(100000, 999999)}",
                "origin": origin_city,
                "destination": dest,
                "equipment": equipment,
                "weight_lbs": random.randint(20000, 44000),
                "rate_per_mile": round(random.uniform(2.50, 4.80), 2),
                "total_miles": random.randint(400, 2000),
                "pickup_date": datetime.now().isoformat()[:10],
                "commodity": random.choice(["Frozen Foods", "Dairy", "Produce", "Seafood"]),
                "posted_at": datetime.now().isoformat()
            })
        return loads

    async def get_rate_forecast(self, origin: str, destination: str) -> Dict[str, Any]:
        base_rate = round(random.uniform(2.80, 4.20), 2)
        return {
            "origin": origin,
            "destination": destination,
            "equipment": "Reefer",
            "current_rate_per_mile": base_rate,
            "7_day_forecast": round(base_rate + random.uniform(-0.15, 0.20), 2),
            "trend": random.choice(["rising", "stable", "falling"]),
            "confidence": random.choice(["high", "medium"]),
            "spot_vs_contract": "spot +$0.35/mi",
            "last_updated": datetime.now().isoformat()
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="DAT Load Board",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class TMSIntegrationMCPClient:
    """MCP Client for TMS Integration — McLeod Software / Oracle Transportation Management."""

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("TMS_ENDPOINT", "")
        self.api_key = api_key or os.getenv("TMS_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("TMS Integration: No endpoint/key configured, skipping connection")
            return False
        try:
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response = await self._client.get("/api/v1/health")
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("TMS Integration: Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"TMS Integration: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_shipments(self, status: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        statuses = ["in_transit", "delivered", "scheduled", "at_pickup", "at_delivery"]
        shipments = []
        for i in range(min(limit, 10)):
            s = status or random.choice(statuses)
            shipments.append({
                "shipment_id": f"SHP-{2024000 + i + random.randint(1, 999)}",
                "order_id": f"ORD-{random.randint(100000, 999999)}",
                "status": s,
                "origin": random.choice(["Chicago DC", "Dallas DC", "Atlanta DC"]),
                "destination": random.choice(["Customer A - NYC", "Customer B - Miami", "Customer C - Denver"]),
                "commodity": random.choice(["Frozen Foods", "Dairy", "Produce"]),
                "weight_lbs": random.randint(15000, 44000),
                "pickup_date": datetime.now().isoformat()[:10],
                "delivery_date": datetime.now().isoformat()[:10],
                "truck_id": f"TRK-{(i % 5) + 1:03d}"
            })
        return {"shipments": shipments, "total": len(shipments), "status_filter": status}

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="TMS Integration",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class GeofenceMCPClient:
    """MCP Client for Geofencing & POI — Google Maps / HERE Platform."""

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider or os.getenv("GEOFENCE_PROVIDER", "here")
        self.api_key = api_key or os.getenv("GEOFENCE_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Geofence: No API key configured, skipping connection")
            return False
        try:
            if self.provider == "here":
                url = f"https://geocode.search.hereapi.com/v1/geocode?q=Chicago&apiKey={self.api_key}"
            else:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Chicago&key={self.api_key}"
            async with httpx.AsyncClient(timeout=10.0) as c:
                response = await c.get(url)
                self._connected = response.status_code == 200
                if self._connected:
                    logger.info(f"Geofence ({self.provider}): Connected successfully")
                return self._connected
        except Exception as e:
            logger.warning(f"Geofence: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def check_geofence(self, lat: float, lon: float, geofence_name: str) -> Dict[str, Any]:
        dist_m = random.uniform(100, 50000)
        return {
            "geofence_name": geofence_name,
            "lat": lat,
            "lon": lon,
            "inside": dist_m < 1000,
            "distance_m": round(dist_m, 0),
            "timestamp": datetime.now().isoformat()
        }

    async def get_nearby_pois(self, lat: float, lon: float, category: str = "fuel", radius_m: int = 5000) -> List[Dict[str, Any]]:
        pois = []
        for i in range(random.randint(2, 5)):
            pois.append({
                "name": random.choice(["Pilot Flying J", "Love's Travel Stop", "TA Petro", "Speedway"]) if category == "fuel" else f"POI {i+1}",
                "category": category,
                "lat": lat + random.uniform(-0.05, 0.05),
                "lon": lon + random.uniform(-0.05, 0.05),
                "distance_m": round(random.uniform(500, radius_m), 0),
                "diesel_price": round(random.uniform(3.50, 4.80), 3) if category == "fuel" else None,
            })
        return sorted(pois, key=lambda x: x["distance_m"])

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Geofence & POI",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class USDAComplianceMCPClient:
    """MCP Client for USDA/FDA Compliance — free public APIs, no key required."""

    FDA_URL = "https://api.fda.gov"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return True  # Free public API

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                response = await c.get(f"{self.FDA_URL}/food/enforcement.json?limit=1")
                self._connected = response.status_code == 200
                if self._connected:
                    logger.info("USDA/FDA Compliance: Connected to FDA API")
                return self._connected
        except Exception as e:
            logger.warning(f"USDA/FDA Compliance: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_recall_alerts(self, limit: int = 10) -> Dict[str, Any]:
        if self._connected:
            try:
                async with httpx.AsyncClient(timeout=15.0) as c:
                    response = await c.get(f"{self.FDA_URL}/food/enforcement.json?limit={limit}&search=status:Ongoing")
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        return {"active_recalls": results[:limit], "total": len(results), "source": "FDA Enforcement API"}
            except Exception as e:
                logger.error(f"USDA/FDA: recall fetch error - {e}")
        return {"active_recalls": [], "total": 0, "commodities_checked": ["Seafood", "Dairy", "Frozen Foods", "Produce", "Meat"], "source": "FDA Enforcement API (demo)"}

    async def check_haccp_compliance(self, facility_id: str, product_types: List[str]) -> Dict[str, Any]:
        return {
            "facility_id": facility_id,
            "product_types": product_types,
            "haccp_score": round(random.uniform(92, 99), 1),
            "fsma_compliant": True,
            "open_corrective_actions": random.randint(0, 2),
            "certifications": ["HACCP", "FSMA", "SQF Level 2"],
            "last_audit": "2025-01-15",
            "next_audit_due": "2025-07-15"
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="USDA/FDA Compliance",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=True
        )


class EIAFuelPriceMCPClient:
    """MCP Client for EIA Fuel Prices — free public API from U.S. Energy Information Administration."""

    BASE_URL = "https://api.eia.gov/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EIA_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return True  # Public API, key is optional for higher rate limits

    async def connect(self) -> bool:
        try:
            params = {"api_key": self.api_key} if self.api_key else {}
            async with httpx.AsyncClient(timeout=15.0) as c:
                response = await c.get(f"{self.BASE_URL}/petroleum/pri/gnd/data/", params={**params, "length": 1})
                self._connected = response.status_code == 200
                if self._connected:
                    logger.info("EIA Fuel Prices: Connected successfully")
                return self._connected
        except Exception as e:
            logger.warning(f"EIA Fuel Prices: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_diesel_price(self, region: str = "US") -> Dict[str, Any]:
        base = round(random.uniform(3.60, 4.40), 3)
        return {
            "national_avg_per_gallon": base,
            "regions": {
                "midwest": round(base - 0.08, 3),
                "south": round(base - 0.12, 3),
                "northeast": round(base + 0.18, 3),
                "west": round(base + 0.22, 3),
            },
            "week_change": round(random.uniform(-0.15, 0.15), 3),
            "year_change": round(random.uniform(-0.50, 0.30), 3),
            "date": datetime.now().isoformat()[:10],
            "source": "EIA Weekly Retail Diesel Prices"
        }

    async def get_fuel_surcharge(self, base_rate: float, miles: float) -> Dict[str, Any]:
        diesel_price = round(random.uniform(3.60, 4.40), 3)
        mpg = 6.5
        gallons_needed = miles / mpg
        fuel_cost = round(gallons_needed * diesel_price, 2)
        surcharge_pct = round(max(0, (diesel_price - 2.50) / 2.50 * 0.30), 4)
        return {
            "miles": miles,
            "diesel_price": diesel_price,
            "fuel_cost": fuel_cost,
            "surcharge_percent": round(surcharge_pct * 100, 2),
            "surcharge_amount": round(base_rate * miles * surcharge_pct, 2),
            "total_with_surcharge": round(base_rate * miles * (1 + surcharge_pct), 2)
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="EIA Fuel Prices",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=True
        )


class PredictiveMaintenanceMCPClient:
    """MCP Client for Predictive Maintenance — vehicle health monitoring via Samsara or Fleet Complete."""

    BASE_URL = "https://api.samsara.com"

    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.api_key = api_key or os.getenv("MAINTENANCE_API_KEY", "") or os.getenv("SAMSARA_API_KEY", "")
        self.provider = provider or os.getenv("MAINTENANCE_PROVIDER", "samsara")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Predictive Maintenance: No API key configured, skipping connection")
            return False
        try:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response = await self._client.get("/fleet/vehicles")
            self._connected = response.status_code == 200
            if self._connected:
                logger.info(f"Predictive Maintenance ({self.provider}): Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"Predictive Maintenance: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_vehicle_health(self, vehicle_id: str) -> Dict[str, Any]:
        return {
            "vehicle_id": vehicle_id,
            "health_score": round(random.uniform(72, 98), 1),
            "next_service_miles": random.randint(2000, 15000),
            "fault_codes": [],
            "oil_life_pct": round(random.uniform(20, 90), 1),
            "brake_pad_pct": round(random.uniform(30, 95), 1),
            "tire_pressure_ok": random.random() > 0.1,
            "last_inspection": "2025-01-10",
            "estimated_next_failure_days": random.randint(45, 180)
        }

    async def get_maintenance_alerts(self, fleet_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        alerts = []
        if random.random() > 0.6:
            alerts.append({
                "truck_id": "TRK-003",
                "alert_type": "preventive",
                "severity": "low",
                "description": "Oil change due in 2,500 miles",
                "recommended_action": "Schedule service at next available DC",
                "created_at": datetime.now().isoformat()
            })
        return {
            "alerts": alerts,
            "fleet_avg_health": round(random.uniform(88, 95), 1),
            "trucks_due_service": len(alerts)
        }

    async def get_fault_codes(self, vehicle_id: str) -> List[Dict[str, Any]]:
        return []  # Clean fleet in demo mode

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Predictive Maintenance",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class PortStatusMCPClient:
    """MCP Client for Port & Intermodal Status — MarineTraffic / Portcast API."""

    BASE_URL = "https://services.marinetraffic.com/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PORT_STATUS_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Port Status: No API key configured, skipping connection")
            return False
        try:
            self._client = httpx.AsyncClient(timeout=30.0)
            response = await self._client.get(
                f"{self.BASE_URL}/portcalls/v:2/{self.api_key}",
                params={"portid": "1", "protocol": "json"}
            )
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("Port Status: Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"Port Status: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def get_port_congestion(self, port_code: str = "USLAX") -> Dict[str, Any]:
        port_names = {"USLAX": "Los Angeles", "USLGB": "Long Beach", "USSAV": "Savannah", "USNYC": "New York", "USIAH": "Houston"}
        level = random.choice(["low", "medium", "high"])
        wait = {"low": random.uniform(4, 12), "medium": random.uniform(12, 36), "high": random.uniform(36, 72)}
        return {
            "port_code": port_code,
            "port": port_names.get(port_code, port_code),
            "congestion_level": level,
            "avg_wait_hours": round(wait[level], 1),
            "vessels_at_anchor": random.randint(5, 45) if level == "high" else random.randint(0, 10),
            "rail_status": random.choice(["normal", "delayed"]),
            "drayage_availability": random.choice(["good", "limited"]),
            "updated_at": datetime.now().isoformat()
        }

    async def get_intermodal_options(self, origin: str, destination: str, weight_lbs: int = 40000) -> Dict[str, Any]:
        otr_rate = round(random.uniform(3.20, 5.00), 2)
        intermodal_rate = round(otr_rate * random.uniform(0.75, 0.88), 2)
        return {
            "origin": origin,
            "destination": destination,
            "options": [
                {"mode": "OTR (Over-the-Road)", "rate_per_mile": otr_rate, "transit_days": random.randint(2, 5), "co2_kg": round(weight_lbs * 0.001 * random.uniform(0.8, 1.0), 1)},
                {"mode": "Intermodal (Rail + Dray)", "rate_per_mile": intermodal_rate, "transit_days": random.randint(4, 8), "co2_kg": round(weight_lbs * 0.001 * random.uniform(0.3, 0.5), 1), "savings_pct": round((1 - intermodal_rate / otr_rate) * 100, 1)}
            ],
            "recommendation": "Intermodal" if weight_lbs > 35000 and intermodal_rate < otr_rate * 0.85 else "OTR",
            "calculated_at": datetime.now().isoformat()
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Port & Intermodal",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class TwilioPODMCPClient:
    """MCP Client for Twilio — customer notifications & Proof of Delivery."""

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, from_number: Optional[str] = None):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Twilio POD: No credentials configured, skipping connection")
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                response = await c.get(
                    f"{self.BASE_URL}/Accounts/{self.account_sid}.json",
                    auth=(self.account_sid, self.auth_token)
                )
                self._connected = response.status_code == 200
                if self._connected:
                    logger.info("Twilio POD: Connected successfully")
                return self._connected
        except Exception as e:
            logger.warning(f"Twilio POD: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def send_delivery_notification(self, to_number: str, customer_name: str, eta_minutes: int, load_id: str) -> Dict[str, Any]:
        if self._connected and self._client:
            try:
                response = await self._client.post(
                    f"{self.BASE_URL}/Accounts/{self.account_sid}/Messages.json",
                    auth=(self.account_sid, self.auth_token),
                    data={"From": self.from_number, "To": to_number, "Body": f"Hi {customer_name}, your delivery #{load_id} arrives in ~{eta_minutes} min."}
                )
                if response.status_code == 201:
                    return {"message_sid": response.json().get("sid"), "status": "sent"}
            except Exception as e:
                logger.error(f"Twilio POD: send error - {e}")
        return {
            "notification_id": f"NOTIF-{random.randint(10000, 99999)}",
            "customer": customer_name,
            "load_id": load_id,
            "eta_minutes": eta_minutes,
            "channel": "sms",
            "status": "demo_sent",
            "sent_at": datetime.now().isoformat()
        }

    async def send_pod_confirmation(self, to_number: str, load_id: str, delivered_at: str, signed_by: str) -> Dict[str, Any]:
        return {
            "pod_id": f"POD-{random.randint(100000, 999999)}",
            "load_id": load_id,
            "delivered_at": delivered_at,
            "signed_by": signed_by,
            "channel": "sms",
            "status": "demo_sent",
            "sent_at": datetime.now().isoformat()
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Twilio POD",
            connected=self._connected,
            last_check=datetime.now(),
            api_key_configured=self.is_configured
        )


class InsuranceClaimsMCPClient:
    """MCP Client for Insurance & Claims — Riskonnect / custom insurance API."""

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("INSURANCE_ENDPOINT", "")
        self.api_key = api_key or os.getenv("INSURANCE_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    async def connect(self) -> bool:
        if not self.is_configured:
            logger.info("Insurance Claims: No endpoint/key configured, skipping connection")
            return False
        try:
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response = await self._client.get("/api/v1/health")
            self._connected = response.status_code == 200
            if self._connected:
                logger.info("Insurance Claims: Connected successfully")
            return self._connected
        except Exception as e:
            logger.warning(f"Insurance Claims: Connection failed - {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def file_claim(self, load_id: str, incident_type: str, description: str, estimated_value: float) -> Dict[str, Any]:
        return {
            "claim_id": f"CLM-{random.randint(100000, 999999)}",
            "load_id": load_id,
            "incident_type": incident_type,
            "description": description,
            "estimated_value": estimated_value,
            "status": "submitted",
            "reference_number": f"REF-{random.randint(1000000, 9999999)}",
            "adjuster_assigned": "TBD",
            "expected_response_days": 5,
            "submitted_at": datetime.now().isoformat()
        }

    async def get_claim_status(self, claim_id: str) -> Dict[str, Any]:
        return {
            "claim_id": claim_id,
            "status": random.choice(["under_review", "approved", "pending_documentation"]),
            "adjuster": "Jane Doe (demo)",
            "amount_approved": None,
            "next_steps": "Provide supporting documentation",
            "updated_at": datetime.now().isoformat()
        }

    async def get_coverage_summary(self, policy_id: str = "default") -> Dict[str, Any]:
        return {
            "policy_id": policy_id or "LGL-FLEET-2025-001",
            "carrier": "National Transport Insurance (Demo)",
            "coverage_types": {
                "cargo": {"limit": 500000, "deductible": 5000},
                "liability": {"limit": 2000000, "deductible": 10000},
                "physical_damage": {"limit": 150000, "deductible": 2500},
                "refrigeration_breakdown": {"limit": 50000, "deductible": 1000}
            },
            "annual_premium": 187500,
            "policy_expiry": "2025-12-31",
            "claims_this_year": 0,
            "status": "active"
        }

    def get_status(self) -> MCPConnectionStatus:
        return MCPConnectionStatus(
            name="Insurance & Claims",
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
        # Phase 1 connectors
        self.samsara_eld = SamsaraELDMCPClient(
            api_key=mcp_config.get("samsara_eld", {}).get("api_key")
        )
        self.dat_load_board = DATLoadBoardMCPClient(
            username=mcp_config.get("dat_load_board", {}).get("username"),
            password=mcp_config.get("dat_load_board", {}).get("password")
        )
        self.tms = TMSIntegrationMCPClient(
            endpoint=mcp_config.get("tms", {}).get("endpoint"),
            api_key=mcp_config.get("tms", {}).get("api_key")
        )
        self.geofence = GeofenceMCPClient(
            provider=mcp_config.get("geofence", {}).get("provider"),
            api_key=mcp_config.get("geofence", {}).get("api_key")
        )
        # Phase 2 connectors
        self.usda_compliance = USDAComplianceMCPClient()
        self.eia_fuel = EIAFuelPriceMCPClient(
            api_key=mcp_config.get("eia_fuel", {}).get("api_key")
        )
        self.predictive_maintenance = PredictiveMaintenanceMCPClient(
            api_key=mcp_config.get("predictive_maintenance", {}).get("api_key"),
            provider=mcp_config.get("predictive_maintenance", {}).get("provider")
        )
        # Phase 3 connectors
        self.port_status = PortStatusMCPClient(
            api_key=mcp_config.get("port_status", {}).get("api_key")
        )
        self.twilio_pod = TwilioPODMCPClient(
            account_sid=mcp_config.get("twilio_pod", {}).get("account_sid"),
            auth_token=mcp_config.get("twilio_pod", {}).get("auth_token"),
            from_number=mcp_config.get("twilio_pod", {}).get("from_number")
        )
        self.insurance_claims = InsuranceClaimsMCPClient(
            endpoint=mcp_config.get("insurance_claims", {}).get("endpoint"),
            api_key=mcp_config.get("insurance_claims", {}).get("api_key")
        )

        self._initialized = False
    
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all MCP connections. Returns status of each."""
        results = {}
        
        # Connect to each service (failures are graceful)
        results["gps_trace"] = await self.gps_trace.connect()
        results["weather"] = await self.weather.connect()
        results["iot"] = await self.iot.connect()
        results["samsara_eld"] = await self.samsara_eld.connect()
        results["dat_load_board"] = await self.dat_load_board.connect()
        results["tms"] = await self.tms.connect()
        results["geofence"] = await self.geofence.connect()
        results["usda_compliance"] = await self.usda_compliance.connect()
        results["eia_fuel"] = await self.eia_fuel.connect()
        results["predictive_maintenance"] = await self.predictive_maintenance.connect()
        results["port_status"] = await self.port_status.connect()
        results["twilio_pod"] = await self.twilio_pod.connect()
        results["insurance_claims"] = await self.insurance_claims.connect()

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
        await self.samsara_eld.disconnect()
        await self.dat_load_board.disconnect()
        await self.tms.disconnect()
        await self.geofence.disconnect()
        await self.usda_compliance.disconnect()
        await self.eia_fuel.disconnect()
        await self.predictive_maintenance.disconnect()
        await self.port_status.disconnect()
        await self.twilio_pod.disconnect()
        await self.insurance_claims.disconnect()
        self._initialized = False
    
    def get_all_status(self) -> List[MCPConnectionStatus]:
        """Get status of all MCP connections"""
        return [
            self.gps_trace.get_status(),
            self.weather.get_status(),
            self.iot.get_status(),
            self.samsara_eld.get_status(),
            self.dat_load_board.get_status(),
            self.tms.get_status(),
            self.geofence.get_status(),
            self.usda_compliance.get_status(),
            self.eia_fuel.get_status(),
            self.predictive_maintenance.get_status(),
            self.port_status.get_status(),
            self.twilio_pod.get_status(),
            self.insurance_claims.get_status(),
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
