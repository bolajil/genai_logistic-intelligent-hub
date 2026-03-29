"""
Custom Lineage IoT MCP Server
Exposes temperature sensors, GPS tracking, and cold chain data as MCP tools.

This server can be run standalone or embedded in the GLIH backend.
When API keys aren't configured, it returns simulated data for demo mode.
"""

import random
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
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
    
    # ==================== Phase 1-3 Tools ====================

    async def get_driver_hos_status(self, driver_id: str = "all") -> Dict[str, Any]:
        """Get ELD Hours-of-Service status for one or all drivers"""
        drivers = [
            {"driver_id": "DRV-001", "name": "John Smith", "truck": "TRK-001"},
            {"driver_id": "DRV-002", "name": "Maria Garcia", "truck": "TRK-002"},
            {"driver_id": "DRV-003", "name": "James Wilson", "truck": "TRK-003"},
            {"driver_id": "DRV-004", "name": "Sarah Johnson", "truck": "TRK-004"},
            {"driver_id": "DRV-005", "name": "Mike Brown", "truck": "TRK-005"},
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
        """Get recent ELD violations across the fleet"""
        return {
            "violations": [],
            "fleet_compliance_score": 98.5,
            "last_audit": datetime.now().isoformat(),
            "note": "No violations in past 30 days (demo data)"
        }

    async def search_available_loads(self, origin_city: str = "Chicago", destination_city: str = "", equipment: str = "Reefer") -> List[Dict[str, Any]]:
        """Search DAT load board for available loads"""
        cities = ["Dallas", "Atlanta", "Los Angeles", "Seattle", "Denver", "Phoenix", "Minneapolis"]
        dest = destination_city or random.choice(cities)
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

    async def get_lane_rate_forecast(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get DAT rate forecast for a lane"""
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

    async def get_tms_shipments(self, status: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Get active shipments from TMS"""
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

    async def check_truck_geofences(self) -> List[Dict[str, Any]]:
        """Check which trucks are inside/outside their assigned geofences"""
        events = []
        for truck_id, truck in self._trucks.items():
            for fac_key, fac in self.FACILITIES.items():
                dist = ((truck.lat - fac["lat"])**2 + (truck.lon - fac["lon"])**2)**0.5 * 111
                if dist < 5:
                    events.append({
                        "truck_id": truck_id,
                        "facility": fac["name"],
                        "event": "inside_geofence",
                        "distance_km": round(dist, 2),
                        "timestamp": datetime.now().isoformat()
                    })
        return events if events else [{"message": "All trucks between geofences (in transit)", "timestamp": datetime.now().isoformat()}]

    async def get_nearby_fuel_stops(self, truck_id: str) -> List[Dict[str, Any]]:
        """Get nearby fuel stops for a truck"""
        truck = self._trucks.get(truck_id)
        if not truck:
            return []
        stops = []
        for _ in range(3):
            stops.append({
                "station_id": f"FS-{random.randint(1000, 9999)}",
                "name": random.choice(["Pilot Flying J", "Love's Travel Stop", "TA Petro", "Speedway"]),
                "lat": truck.lat + random.uniform(-0.5, 0.5),
                "lon": truck.lon + random.uniform(-0.5, 0.5),
                "distance_miles": round(random.uniform(0.5, 15), 1),
                "diesel_price": round(random.uniform(3.50, 4.80), 3),
                "has_reefer_parking": random.choice([True, False]),
                "amenities": ["showers", "restaurant"] if random.random() > 0.5 else ["restaurant"]
            })
        return sorted(stops, key=lambda x: x["distance_miles"])

    async def get_compliance_status(self) -> Dict[str, Any]:
        """Get HACCP/FSMA compliance status for all facilities"""
        facilities_status = {}
        for fac_key, fac in self.FACILITIES.items():
            facilities_status[fac["name"]] = {
                "haccp_score": round(random.uniform(92, 99), 1),
                "fsma_compliant": True,
                "last_audit": "2025-01-15",
                "next_audit_due": "2025-07-15",
                "open_corrective_actions": random.randint(0, 2),
                "certifications": ["HACCP", "FSMA", "SQF Level 2"],
                "temperature_log_compliance": "100%"
            }
        return {
            "overall_score": 96.8,
            "facilities": facilities_status,
            "active_recalls": [],
            "last_fda_check": datetime.now().isoformat()[:10]
        }

    async def get_recall_alerts(self) -> Dict[str, Any]:
        """Check for active FDA food recalls affecting transported commodities"""
        return {
            "active_recalls": [],
            "commodities_checked": ["Seafood", "Dairy", "Frozen Foods", "Produce", "Meat"],
            "last_checked": datetime.now().isoformat(),
            "source": "FDA Enforcement Reports (demo)"
        }

    async def get_current_fuel_prices(self) -> Dict[str, Any]:
        """Get current EIA national and regional diesel prices"""
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

    async def calculate_fuel_surcharge(self, base_rate: float, miles: float) -> Dict[str, Any]:
        """Calculate fuel surcharge for a load"""
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

    async def get_fleet_health(self) -> List[Dict[str, Any]]:
        """Get predictive maintenance health scores for all trucks"""
        health_data = []
        for truck_id in self._trucks:
            health_data.append({
                "truck_id": truck_id,
                "health_score": round(random.uniform(72, 98), 1),
                "next_service_miles": random.randint(2000, 15000),
                "fault_codes": [],
                "alerts": ["Oil change due in 3,000 miles"] if random.random() > 0.7 else [],
                "oil_life_pct": round(random.uniform(20, 90), 1),
                "brake_pad_pct": round(random.uniform(30, 95), 1),
                "tire_pressure_ok": random.random() > 0.1,
                "last_inspection": "2025-01-10",
                "estimated_next_failure_days": random.randint(45, 180)
            })
        return health_data

    async def get_maintenance_alerts(self) -> Dict[str, Any]:
        """Get active maintenance alerts requiring attention"""
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

    async def get_port_status(self, port: str = "Los Angeles") -> Dict[str, Any]:
        """Get port congestion and wait times"""
        level = random.choice(["low", "medium", "high"])
        wait = {"low": random.uniform(4, 12), "medium": random.uniform(12, 36), "high": random.uniform(36, 72)}
        return {
            "port": port,
            "congestion_level": level,
            "avg_wait_hours": round(wait[level], 1),
            "vessels_at_anchor": random.randint(5, 45) if level == "high" else random.randint(0, 10),
            "rail_status": random.choice(["normal", "delayed"]),
            "drayage_availability": random.choice(["good", "limited"]),
            "updated_at": datetime.now().isoformat()
        }

    async def get_intermodal_options(self, origin: str, destination: str, weight_lbs: int = 40000) -> Dict[str, Any]:
        """Get intermodal routing options vs OTR"""
        otr_rate = round(random.uniform(3.20, 5.00), 2)
        intermodal_rate = round(otr_rate * random.uniform(0.75, 0.88), 2)
        return {
            "origin": origin,
            "destination": destination,
            "options": [
                {"mode": "OTR (Over-the-Road)", "rate_per_mile": otr_rate, "transit_days": random.randint(2, 5)},
                {"mode": "Intermodal (Rail + Dray)", "rate_per_mile": intermodal_rate, "transit_days": random.randint(4, 8), "savings_pct": round((1 - intermodal_rate / otr_rate) * 100, 1)}
            ],
            "recommendation": "Intermodal" if weight_lbs > 35000 and intermodal_rate < otr_rate * 0.85 else "OTR",
            "calculated_at": datetime.now().isoformat()
        }

    async def send_delivery_alert(self, customer_name: str, load_id: str, truck_id: str, eta_minutes: int) -> Dict[str, Any]:
        """Send delivery ETA notification to customer"""
        return {
            "notification_id": f"NOTIF-{random.randint(10000, 99999)}",
            "customer": customer_name,
            "load_id": load_id,
            "truck_id": truck_id,
            "eta_minutes": eta_minutes,
            "message": f"Your delivery for order {load_id} is approximately {eta_minutes} minutes away.",
            "channel": "sms",
            "status": "demo_sent",
            "sent_at": datetime.now().isoformat()
        }

    async def generate_pod_document(self, load_id: str, truck_id: str, delivered_by: str) -> Dict[str, Any]:
        """Generate Proof of Delivery document"""
        truck = self._trucks.get(truck_id)
        return {
            "pod_id": f"POD-{random.randint(100000, 999999)}",
            "load_id": load_id,
            "truck_id": truck_id,
            "delivered_by": delivered_by,
            "delivery_lat": truck.lat if truck else 0,
            "delivery_lon": truck.lon if truck else 0,
            "temperature_at_delivery_c": truck.reefer_temp_c if truck else 0,
            "door_seal_intact": not (truck.door_open if truck else False),
            "delivered_at": datetime.now().isoformat(),
            "signature_captured": True,
            "photo_count": random.randint(2, 5),
            "status": "complete"
        }

    async def get_insurance_summary(self) -> Dict[str, Any]:
        """Get fleet insurance coverage summary"""
        return {
            "policy_id": "LGL-FLEET-2025-001",
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

    async def file_cargo_claim(self, load_id: str, incident_type: str, description: str, estimated_value: float) -> Dict[str, Any]:
        """File a cargo insurance claim"""
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
            },
            # Phase 1-3 tools
            {"name": "get_driver_hos_status", "description": "Get ELD Hours-of-Service status for drivers (compliant fleet check)", "inputSchema": {"type": "object", "properties": {"driver_id": {"type": "string", "description": "Driver ID or 'all' for fleet-wide", "default": "all"}}}},
            {"name": "get_eld_violations", "description": "Get recent ELD violations across the fleet", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "search_available_loads", "description": "Search DAT load board for available Reefer loads matching fleet equipment", "inputSchema": {"type": "object", "properties": {"origin_city": {"type": "string"}, "destination_city": {"type": "string"}, "equipment": {"type": "string", "default": "Reefer"}}}},
            {"name": "get_lane_rate_forecast", "description": "Get DAT rate forecast for a lane (pricing intelligence)", "inputSchema": {"type": "object", "properties": {"origin": {"type": "string"}, "destination": {"type": "string"}}, "required": ["origin", "destination"]}},
            {"name": "get_tms_shipments", "description": "Get active shipments from TMS (McLeod/Oracle)", "inputSchema": {"type": "object", "properties": {"status": {"type": "string", "enum": ["in_transit", "delivered", "scheduled", "at_pickup", "at_delivery"]}, "limit": {"type": "integer", "default": 20}}}},
            {"name": "check_truck_geofences", "description": "Check which trucks are inside/outside their assigned facility geofences", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_nearby_fuel_stops", "description": "Get nearby fuel stops for a truck with diesel price and amenities", "inputSchema": {"type": "object", "properties": {"truck_id": {"type": "string"}}, "required": ["truck_id"]}},
            {"name": "get_compliance_status", "description": "Get HACCP/FSMA compliance status for all facilities", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_recall_alerts", "description": "Check for active FDA food recalls affecting transported commodities", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_current_fuel_prices", "description": "Get current EIA national and regional diesel fuel prices", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "calculate_fuel_surcharge", "description": "Calculate fuel surcharge for a load based on current diesel price", "inputSchema": {"type": "object", "properties": {"base_rate": {"type": "number", "description": "Rate per mile USD"}, "miles": {"type": "number"}}, "required": ["base_rate", "miles"]}},
            {"name": "get_fleet_health", "description": "Get predictive maintenance health scores for all trucks", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_maintenance_alerts", "description": "Get active maintenance alerts requiring attention", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_port_status", "description": "Get port congestion and estimated wait times", "inputSchema": {"type": "object", "properties": {"port": {"type": "string", "default": "Los Angeles"}}}},
            {"name": "get_intermodal_options", "description": "Compare intermodal (rail+dray) vs OTR routing for a lane", "inputSchema": {"type": "object", "properties": {"origin": {"type": "string"}, "destination": {"type": "string"}, "weight_lbs": {"type": "integer", "default": 40000}}, "required": ["origin", "destination"]}},
            {"name": "send_delivery_alert", "description": "Send delivery ETA notification to customer via SMS", "inputSchema": {"type": "object", "properties": {"customer_name": {"type": "string"}, "load_id": {"type": "string"}, "truck_id": {"type": "string"}, "eta_minutes": {"type": "integer"}}, "required": ["customer_name", "load_id", "truck_id", "eta_minutes"]}},
            {"name": "generate_pod_document", "description": "Generate Proof of Delivery document with temperature and signature", "inputSchema": {"type": "object", "properties": {"load_id": {"type": "string"}, "truck_id": {"type": "string"}, "delivered_by": {"type": "string"}}, "required": ["load_id", "truck_id", "delivered_by"]}},
            {"name": "get_insurance_summary", "description": "Get fleet cargo insurance coverage summary and policy details", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "file_cargo_claim", "description": "File a cargo insurance claim for a damaged or lost shipment", "inputSchema": {"type": "object", "properties": {"load_id": {"type": "string"}, "incident_type": {"type": "string"}, "description": {"type": "string"}, "estimated_value": {"type": "number"}}, "required": ["load_id", "incident_type", "description", "estimated_value"]}},
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
            # Phase 1-3 tools
            "get_driver_hos_status": lambda: self.get_driver_hos_status(arguments.get("driver_id", "all")),
            "get_eld_violations": self.get_eld_violations,
            "search_available_loads": lambda: self.search_available_loads(arguments.get("origin_city", "Chicago"), arguments.get("destination_city", ""), arguments.get("equipment", "Reefer")),
            "get_lane_rate_forecast": lambda: self.get_lane_rate_forecast(arguments.get("origin", ""), arguments.get("destination", "")),
            "get_tms_shipments": lambda: self.get_tms_shipments(arguments.get("status"), arguments.get("limit", 20)),
            "check_truck_geofences": self.check_truck_geofences,
            "get_nearby_fuel_stops": lambda: self.get_nearby_fuel_stops(arguments.get("truck_id", "")),
            "get_compliance_status": self.get_compliance_status,
            "get_recall_alerts": self.get_recall_alerts,
            "get_current_fuel_prices": self.get_current_fuel_prices,
            "calculate_fuel_surcharge": lambda: self.calculate_fuel_surcharge(arguments.get("base_rate", 3.0), arguments.get("miles", 0)),
            "get_fleet_health": self.get_fleet_health,
            "get_maintenance_alerts": self.get_maintenance_alerts,
            "get_port_status": lambda: self.get_port_status(arguments.get("port", "Los Angeles")),
            "get_intermodal_options": lambda: self.get_intermodal_options(arguments.get("origin", ""), arguments.get("destination", ""), arguments.get("weight_lbs", 40000)),
            "send_delivery_alert": lambda: self.send_delivery_alert(arguments.get("customer_name", ""), arguments.get("load_id", ""), arguments.get("truck_id", ""), arguments.get("eta_minutes", 0)),
            "generate_pod_document": lambda: self.generate_pod_document(arguments.get("load_id", ""), arguments.get("truck_id", ""), arguments.get("delivered_by", "")),
            "get_insurance_summary": self.get_insurance_summary,
            "file_cargo_claim": lambda: self.file_cargo_claim(arguments.get("load_id", ""), arguments.get("incident_type", ""), arguments.get("description", ""), arguments.get("estimated_value", 0)),
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
