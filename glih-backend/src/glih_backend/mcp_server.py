"""
Custom Lineage IoT MCP Server
Exposes temperature sensors, GPS tracking, and cold chain data as MCP tools.

This server can be run standalone or embedded in the GLIH backend.
When API keys aren't configured, it returns simulated data for demo mode.
"""

import os
import json
import random
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TruckData:
    """Real-time truck tracking data"""
    truck_id: str
    driver_name: str
    lat: float
    lon: float
    speed_kmh: float
    heading: float
    reefer_temp_c: float
    reefer_setpoint_c: float
    door_open: bool
    fuel_level_pct: float
    engine_hours: float
    last_updated: str
    route_id: Optional[str] = None
    eta_minutes: Optional[int] = None
    status: str = "in_transit"  # in_transit, loading, unloading, idle, maintenance


@dataclass  
class SensorData:
    """IoT sensor reading"""
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    location: str
    device_id: str
    timestamp: str
    status: str = "normal"  # normal, warning, critical


@dataclass
class GeofenceEvent:
    """Geofence entry/exit event"""
    truck_id: str
    geofence_name: str
    event_type: str  # enter, exit
    timestamp: str
    lat: float
    lon: float


class LineageMCPServer:
    """
    MCP Server providing Lineage-specific IoT and logistics tools.
    Supports both real data (when connected) and demo simulation.
    """
    
    # Demo data for facilities
    FACILITIES = {
        "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago DC"},
        "dallas": {"lat": 32.7767, "lon": -96.7970, "name": "Dallas DC"},
        "atlanta": {"lat": 33.7490, "lon": -84.3880, "name": "Atlanta DC"},
        "los_angeles": {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles DC"},
        "seattle": {"lat": 47.6062, "lon": -122.3321, "name": "Seattle DC"},
    }
    
    PRODUCT_TEMP_RANGES = {
        "seafood": (-2, 2),
        "dairy": (0, 4),
        "frozen": (-25, -18),
        "produce": (0, 10),
        "meat": (-2, 4),
    }
    
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._trucks: Dict[str, TruckData] = {}
        self._sensors: Dict[str, SensorData] = {}
        self._geofence_events: List[GeofenceEvent] = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize the MCP server with demo data if in demo mode"""
        if self.demo_mode:
            self._generate_demo_data()
        self._initialized = True
        logger.info(f"Lineage MCP Server initialized (demo_mode={self.demo_mode})")
    
    def _generate_demo_data(self):
        """Generate realistic demo data for trucks and sensors"""
        # Generate demo trucks
        truck_routes = [
            ("TRK-001", "chicago", "dallas", "John Smith", "seafood"),
            ("TRK-002", "los_angeles", "seattle", "Maria Garcia", "dairy"),
            ("TRK-003", "atlanta", "chicago", "James Wilson", "frozen"),
            ("TRK-004", "dallas", "atlanta", "Sarah Johnson", "produce"),
            ("TRK-005", "seattle", "los_angeles", "Mike Brown", "meat"),
        ]
        
        for truck_id, origin_key, dest_key, driver, product in truck_routes:
            origin_loc = self.FACILITIES[origin_key]
            dest_loc = self.FACILITIES[dest_key]
            
            # Simulate position along route (random progress)
            progress = random.uniform(0.2, 0.8)
            lat = origin_loc["lat"] + (dest_loc["lat"] - origin_loc["lat"]) * progress
            lon = origin_loc["lon"] + (dest_loc["lon"] - origin_loc["lon"]) * progress
            
            # Get temp range for product
            temp_min, temp_max = self.PRODUCT_TEMP_RANGES[product]
            setpoint = (temp_min + temp_max) / 2
            
            self._trucks[truck_id] = TruckData(
                truck_id=truck_id,
                driver_name=driver,
                lat=lat,
                lon=lon,
                speed_kmh=random.uniform(60, 100),
                heading=random.uniform(0, 360),
                reefer_temp_c=setpoint + random.uniform(-0.5, 0.5),
                reefer_setpoint_c=setpoint,
                door_open=False,
                fuel_level_pct=random.uniform(40, 95),
                engine_hours=random.uniform(1000, 5000),
                last_updated=datetime.now().isoformat(),
                route_id=f"RTE-{truck_id[-3:]}",
                eta_minutes=int(random.uniform(60, 480)),
                status="in_transit"
            )
        
        # Generate demo sensors for each facility
        sensor_id = 1
        for facility_key, facility in self.FACILITIES.items():
            # Temperature sensors
            for zone in ["dock_1", "dock_2", "storage_a", "storage_b", "freezer"]:
                if "freezer" in zone:
                    temp = random.uniform(-22, -18)
                elif "storage" in zone:
                    temp = random.uniform(0, 4)
                else:
                    temp = random.uniform(2, 8)
                
                self._sensors[f"TEMP-{sensor_id:04d}"] = SensorData(
                    sensor_id=f"TEMP-{sensor_id:04d}",
                    sensor_type="temperature",
                    value=round(temp, 1),
                    unit="°C",
                    location=f"{facility['name']} - {zone}",
                    device_id=f"DEV-{facility_key.upper()}-{zone.upper()}",
                    timestamp=datetime.now().isoformat(),
                    status="normal" if -25 <= temp <= 10 else "warning"
                )
                sensor_id += 1
            
            # Door sensors
            for door in ["main_door", "loading_bay_1", "loading_bay_2"]:
                self._sensors[f"DOOR-{sensor_id:04d}"] = SensorData(
                    sensor_id=f"DOOR-{sensor_id:04d}",
                    sensor_type="door",
                    value=0,  # 0 = closed, 1 = open
                    unit="state",
                    location=f"{facility['name']} - {door}",
                    device_id=f"DEV-{facility_key.upper()}-{door.upper()}",
                    timestamp=datetime.now().isoformat(),
                    status="normal"
                )
                sensor_id += 1
    
    # ==================== MCP Tools ====================
    
    async def get_all_trucks(self) -> List[Dict[str, Any]]:
        """Get status of all tracked trucks"""
        if self.demo_mode:
            # Simulate real-time updates
            for truck in self._trucks.values():
                truck.lat += random.uniform(-0.01, 0.01)
                truck.lon += random.uniform(-0.01, 0.01)
                truck.speed_kmh = max(0, truck.speed_kmh + random.uniform(-5, 5))
                truck.reefer_temp_c += random.uniform(-0.1, 0.1)
                truck.last_updated = datetime.now().isoformat()
                if truck.eta_minutes:
                    truck.eta_minutes = max(0, truck.eta_minutes - 1)
        
        return [asdict(t) for t in self._trucks.values()]
    
    async def get_truck(self, truck_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific truck"""
        truck = self._trucks.get(truck_id)
        if truck and self.demo_mode:
            truck.last_updated = datetime.now().isoformat()
        return asdict(truck) if truck else None
    
    async def get_all_sensors(self, sensor_type: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all sensor readings, optionally filtered"""
        sensors = list(self._sensors.values())
        
        if sensor_type:
            sensors = [s for s in sensors if s.sensor_type == sensor_type]
        if location:
            sensors = [s for s in sensors if location.lower() in s.location.lower()]
        
        if self.demo_mode:
            for sensor in sensors:
                sensor.timestamp = datetime.now().isoformat()
                if sensor.sensor_type == "temperature":
                    sensor.value = round(sensor.value + random.uniform(-0.2, 0.2), 1)
        
        return [asdict(s) for s in sensors]
    
    async def get_sensor(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific sensor reading"""
        sensor = self._sensors.get(sensor_id)
        if sensor and self.demo_mode:
            sensor.timestamp = datetime.now().isoformat()
        return asdict(sensor) if sensor else None
    
    async def get_temperature_alerts(self, threshold_deviation: float = 2.0) -> List[Dict[str, Any]]:
        """Get sensors with temperature outside acceptable range"""
        alerts = []
        temp_sensors = [s for s in self._sensors.values() if s.sensor_type == "temperature"]
        
        for sensor in temp_sensors:
            # Determine expected range based on location
            if "freezer" in sensor.location.lower():
                expected_min, expected_max = -25, -18
            elif "storage" in sensor.location.lower():
                expected_min, expected_max = 0, 4
            else:
                expected_min, expected_max = 0, 10
            
            if sensor.value < expected_min - threshold_deviation or sensor.value > expected_max + threshold_deviation:
                alerts.append({
                    "sensor_id": sensor.sensor_id,
                    "location": sensor.location,
                    "current_temp": sensor.value,
                    "expected_range": f"{expected_min}°C to {expected_max}°C",
                    "deviation": round(max(sensor.value - expected_max, expected_min - sensor.value), 1),
                    "severity": "critical" if abs(sensor.value - (expected_min + expected_max) / 2) > threshold_deviation * 2 else "warning",
                    "timestamp": sensor.timestamp
                })
        
        return alerts
    
    async def get_facility_status(self, facility: str) -> Dict[str, Any]:
        """Get comprehensive status for a facility"""
        facility_key = facility.lower().replace(" dc", "").replace(" ", "_")
        
        if facility_key not in self.FACILITIES:
            return {"error": f"Unknown facility: {facility}"}
        
        facility_info = self.FACILITIES[facility_key]
        
        # Get sensors for this facility
        sensors = [s for s in self._sensors.values() if facility_info["name"] in s.location]
        temp_sensors = [s for s in sensors if s.sensor_type == "temperature"]
        door_sensors = [s for s in sensors if s.sensor_type == "door"]
        
        # Get trucks at or heading to this facility
        trucks_here = [t for t in self._trucks.values() 
                       if abs(t.lat - facility_info["lat"]) < 0.1 and abs(t.lon - facility_info["lon"]) < 0.1]
        
        return {
            "facility": facility_info["name"],
            "location": {"lat": facility_info["lat"], "lon": facility_info["lon"]},
            "sensors": {
                "total": len(sensors),
                "temperature": len(temp_sensors),
                "doors": len(door_sensors)
            },
            "avg_temperature": round(sum(s.value for s in temp_sensors) / len(temp_sensors), 1) if temp_sensors else None,
            "doors_open": sum(1 for s in door_sensors if s.value == 1),
            "trucks_present": len(trucks_here),
            "alerts": await self.get_temperature_alerts()
        }
    
    async def get_route_eta(self, truck_id: str) -> Dict[str, Any]:
        """Get ETA and route info for a truck"""
        truck = self._trucks.get(truck_id)
        if not truck:
            return {"error": f"Unknown truck: {truck_id}"}
        
        return {
            "truck_id": truck_id,
            "route_id": truck.route_id,
            "eta_minutes": truck.eta_minutes,
            "current_location": {"lat": truck.lat, "lon": truck.lon},
            "speed_kmh": truck.speed_kmh,
            "status": truck.status
        }
    
    async def simulate_breach(self, truck_id: Optional[str] = None) -> Dict[str, Any]:
        """Simulate a temperature breach for testing (demo mode only)"""
        if not self.demo_mode:
            return {"error": "Breach simulation only available in demo mode"}
        
        if truck_id:
            truck = self._trucks.get(truck_id)
            if truck:
                truck.reefer_temp_c = truck.reefer_setpoint_c + 5.0
                truck.last_updated = datetime.now().isoformat()
                return {"simulated": True, "truck_id": truck_id, "new_temp": truck.reefer_temp_c}
        else:
            # Pick random truck
            truck = random.choice(list(self._trucks.values()))
            truck.reefer_temp_c = truck.reefer_setpoint_c + 5.0
            truck.last_updated = datetime.now().isoformat()
            return {"simulated": True, "truck_id": truck.truck_id, "new_temp": truck.reefer_temp_c}
    
    # ==================== Tool Registry ====================
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions"""
        return [
            {
                "name": "get_all_trucks",
                "description": "Get real-time status of all tracked trucks including location, temperature, and ETA",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_truck",
                "description": "Get detailed status of a specific truck",
                "inputSchema": {
                    "type": "object",
                    "properties": {"truck_id": {"type": "string", "description": "Truck ID (e.g., TRK-001)"}},
                    "required": ["truck_id"]
                }
            },
            {
                "name": "get_all_sensors",
                "description": "Get all IoT sensor readings from facilities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sensor_type": {"type": "string", "enum": ["temperature", "door", "humidity"]},
                        "location": {"type": "string", "description": "Filter by facility or zone name"}
                    }
                }
            },
            {
                "name": "get_temperature_alerts",
                "description": "Get sensors with temperature outside acceptable range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "threshold_deviation": {"type": "number", "default": 2.0, "description": "Degrees of acceptable deviation"}
                    }
                }
            },
            {
                "name": "get_facility_status",
                "description": "Get comprehensive status for a distribution center",
                "inputSchema": {
                    "type": "object",
                    "properties": {"facility": {"type": "string", "description": "Facility name (e.g., Chicago DC)"}},
                    "required": ["facility"]
                }
            },
            {
                "name": "get_route_eta",
                "description": "Get ETA and route information for a truck",
                "inputSchema": {
                    "type": "object",
                    "properties": {"truck_id": {"type": "string"}},
                    "required": ["truck_id"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Any:
        """Execute an MCP tool by name"""
        arguments = arguments or {}
        
        tool_map = {
            "get_all_trucks": self.get_all_trucks,
            "get_truck": lambda: self.get_truck(arguments.get("truck_id", "")),
            "get_all_sensors": lambda: self.get_all_sensors(
                arguments.get("sensor_type"),
                arguments.get("location")
            ),
            "get_sensor": lambda: self.get_sensor(arguments.get("sensor_id", "")),
            "get_temperature_alerts": lambda: self.get_temperature_alerts(
                arguments.get("threshold_deviation", 2.0)
            ),
            "get_facility_status": lambda: self.get_facility_status(arguments.get("facility", "")),
            "get_route_eta": lambda: self.get_route_eta(arguments.get("truck_id", "")),
            "simulate_breach": lambda: self.simulate_breach(arguments.get("truck_id")),
        }
        
        if name not in tool_map:
            return {"error": f"Unknown tool: {name}"}
        
        result = tool_map[name]()
        if asyncio.iscoroutine(result):
            result = await result
        return result


# Global instance
_mcp_server: Optional[LineageMCPServer] = None


def get_mcp_server(demo_mode: bool = True) -> LineageMCPServer:
    """Get or create the global MCP server instance"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = LineageMCPServer(demo_mode=demo_mode)
    return _mcp_server


async def init_mcp_server(demo_mode: bool = True) -> LineageMCPServer:
    """Initialize the MCP server"""
    server = get_mcp_server(demo_mode)
    await server.initialize()
    return server
