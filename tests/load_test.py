"""
GLIH Load Test — Locust
=======================
Run: locust -f tests/load_test.py --host http://localhost:9001

Open browser at http://localhost:8089 to start the test.
Set users=50, spawn_rate=10 and run for 5 minutes for the standard profile.

Credentials are read from environment variables:
  GLIH_ADMIN_EMAIL      (default: admin@glih.ops)
  GLIH_ADMIN_PASSWORD   — required, no default
  GLIH_DISPATCHER_EMAIL (default: sarah.chen@glih.ops)
  GLIH_DISPATCHER_PASSWORD — required, no default
"""
import os
from locust import HttpUser, task, between

_ADMIN_EMAIL      = os.getenv("GLIH_ADMIN_EMAIL",      "admin@glih.ops")
_ADMIN_PASSWORD   = os.getenv("GLIH_ADMIN_PASSWORD",   "")
_DISP_EMAIL       = os.getenv("GLIH_DISPATCHER_EMAIL",  "sarah.chen@glih.ops")
_DISP_PASSWORD    = os.getenv("GLIH_DISPATCHER_PASSWORD", "")


class DispatcherUser(HttpUser):
    """Simulates a dispatcher using the GLIH platform (analyst role)."""
    wait_time = between(1, 3)   # realistic think time between requests

    def on_start(self):
        """Login before running tasks."""
        resp = self.client.post("/auth/login", json={
            "username": _DISP_EMAIL,
            "password": _DISP_PASSWORD,
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")
        else:
            self.token = ""

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def query_sops(self):
        """Most common action — query SOPs. Weight 5 = 5x more frequent."""
        self.client.get(
            "/query",
            params={"q": "temperature breach procedure dairy", "k": 4, "collection": "lineage-sops"},
            headers=self._headers(),
            name="/query [sop]",
        )

    @task(3)
    def health_check(self):
        """Health checks — simulate load balancer probes."""
        self.client.get("/health", name="/health")

    @task(2)
    def run_anomaly_agent(self):
        """Anomaly agent — heavier workload."""
        self.client.post(
            "/agents/anomaly",
            json={
                "shipment_id": "TEST-001",
                "temperature_c": 6.5,
                "product_type": "Dairy",
                "threshold_max_c": 4.0,
                "location": "Chicago Hub",
                "breach_duration_min": 15,
            },
            headers=self._headers(),
            name="/agents/anomaly",
        )

    @task(1)
    def list_collections(self):
        """Index operations."""
        self.client.get("/index/collections", headers=self._headers(), name="/index/collections")

    @task(2)
    def fleet_view(self):
        """Dispatcher frequently checks fleet status."""
        self.client.get("/fleet/trucks", headers=self._headers(), name="/fleet/trucks")


class AdminUser(HttpUser):
    """Simulates an admin managing users and checking system health (weight: 1 admin per 10 dispatchers)."""
    wait_time = between(3, 8)
    weight = 1   # spawn 1 admin for every ~10 dispatchers

    def on_start(self):
        resp = self.client.post("/auth/login", json={
            "username": _ADMIN_EMAIL,
            "password": _ADMIN_PASSWORD,
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")
        else:
            self.token = ""

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def health_detailed(self):
        self.client.get("/health/detailed", headers=self._headers(), name="/health/detailed")

    @task(2)
    def list_users(self):
        self.client.get("/auth/users", headers=self._headers(), name="/auth/users")

    @task(1)
    def list_collections(self):
        self.client.get("/index/collections", headers=self._headers(), name="/index/collections")
