"""
GLIH Load Test — Locust
=======================
Run: locust -f tests/load_test.py --host http://localhost:9001

Open browser at http://localhost:8089 to start the test.
Set users=100, spawn_rate=10 for a 1,000-user simulation.
"""
from locust import HttpUser, task, between


class DispatcherUser(HttpUser):
    """Simulates a dispatcher using the GLIH platform."""
    wait_time = between(1, 3)   # realistic think time between requests

    def on_start(self):
        """Login before running tasks."""
        resp = self.client.post("/auth/login", json={
            "username": "admin@glih.ops",
            "password": "glih-admin-2025",
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
