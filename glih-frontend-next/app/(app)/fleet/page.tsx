"use client";
import { useState, useEffect, useRef } from "react";
import Header from "@/components/Header";
import { usePermissions } from "@/hooks/usePermissions";

const BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9001";

interface Truck {
  truck_id: string;
  driver_name: string;
  device_id?: string;
  license_plate?: string;
  reefer_equipped: boolean;
  home_facility?: string;
  notes?: string;
  active: boolean;
  source?: string;
  created_at?: string;
  live_data?: {
    lat?: number;
    lon?: number;
    speed_kmh?: number;
    reefer_temp_c?: number;
    status?: string;
    last_updated?: string;
  };
}

interface FleetStats {
  total: number;
  active: number;
  inactive: number;
  in_transit: number;
  idle: number;
  offline: number;
  by_facility: Record<string, number>;
  reefer_equipped: number;
}

const FACILITIES = [
  "Chicago DC",
  "Dallas DC",
  "Atlanta DC",
  "Los Angeles DC",
  "Seattle DC",
];

export default function FleetPage() {
  const { can } = usePermissions();
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [stats, setStats] = useState<FleetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterFacility, setFilterFacility] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [form, setForm] = useState({
    truck_id: "",
    driver_name: "",
    device_id: "",
    license_plate: "",
    reefer_equipped: true,
    home_facility: "",
    notes: "",
  });

  // Bulk import state
  const [bulkData, setBulkData] = useState<Truck[]>([]);
  const [importResult, setImportResult] = useState<any>(null);

  useEffect(() => {
    fetchTrucks();
    fetchStats();
  }, []);

  async function fetchTrucks() {
    try {
      const res = await fetch(`${BASE}/fleet/trucks?active_only=false`);
      if (res.ok) {
        const data = await res.json();
        setTrucks(data.trucks || []);
      }
    } catch (e) {
      console.error("Failed to fetch trucks:", e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      const res = await fetch(`${BASE}/fleet/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    }
  }

  async function createTruck() {
    if (!form.truck_id || !form.driver_name) {
      alert("Truck ID and Driver Name are required");
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${BASE}/fleet/trucks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setShowForm(false);
        setForm({ truck_id: "", driver_name: "", device_id: "", license_plate: "", reefer_equipped: true, home_facility: "", notes: "" });
        fetchTrucks();
        fetchStats();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to create truck");
      }
    } catch (e) {
      alert("Failed to create truck");
    } finally {
      setSaving(false);
    }
  }

  async function deleteTruck(truckId: string) {
    if (!confirm(`Deactivate truck ${truckId}?`)) return;
    try {
      await fetch(`${BASE}/fleet/trucks/${truckId}`, { method: "DELETE" });
      fetchTrucks();
      fetchStats();
    } catch (e) {
      alert("Failed to delete truck");
    }
  }

  async function syncGPSTrace() {
    setSyncing(true);
    try {
      const res = await fetch(`${BASE}/fleet/sync/gps-trace`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        alert(`Sync complete: ${data.added} added, ${data.synced} updated`);
        fetchTrucks();
        fetchStats();
      } else {
        alert(data.message || "Sync failed");
      }
    } catch (e) {
      alert("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  function handleCSVUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const lines = text.split("\n").filter(l => l.trim());
      const headers = lines[0].split(",").map(h => h.trim().toLowerCase().replace(/\s+/g, "_"));

      const trucks: Truck[] = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(",").map(v => v.trim());
        const truck: any = {};
        headers.forEach((h, idx) => {
          if (h === "truck_id" || h === "id") truck.truck_id = values[idx];
          else if (h === "driver_name" || h === "driver") truck.driver_name = values[idx];
          else if (h === "device_id") truck.device_id = values[idx];
          else if (h === "license_plate" || h === "plate") truck.license_plate = values[idx];
          else if (h === "facility" || h === "home_facility") truck.home_facility = values[idx];
          else if (h === "reefer" || h === "reefer_equipped") truck.reefer_equipped = values[idx]?.toLowerCase() !== "false";
        });
        if (truck.truck_id && truck.driver_name) {
          truck.reefer_equipped = truck.reefer_equipped ?? true;
          trucks.push(truck);
        }
      }
      setBulkData(trucks);
    };
    reader.readAsText(file);
  }

  async function importBulkTrucks() {
    if (bulkData.length === 0) return;
    setSaving(true);
    try {
      const res = await fetch(`${BASE}/fleet/trucks/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trucks: bulkData }),
      });
      const result = await res.json();
      setImportResult(result);
      if (result.created > 0) {
        fetchTrucks();
        fetchStats();
      }
    } catch (e) {
      alert("Import failed");
    } finally {
      setSaving(false);
    }
  }

  // Filter trucks
  const filteredTrucks = trucks.filter(t => {
    const matchSearch = !searchTerm || 
      t.truck_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.driver_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.license_plate?.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchFacility = !filterFacility || t.home_facility === filterFacility;
    return matchSearch && matchFacility;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Fleet Management" subtitle="Manage trucks, drivers, and GPS trackers" />

      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
        {/* Stats Cards */}
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
            <div className="card" style={{ padding: 16, textAlign: "center" }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--teal)" }}>{stats.total}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Total Trucks</div>
            </div>
            <div className="card" style={{ padding: 16, textAlign: "center" }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--green)" }}>{stats.active}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Active</div>
            </div>
            <div className="card" style={{ padding: 16, textAlign: "center" }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--blue)" }}>{stats.in_transit}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>In Transit</div>
            </div>
            <div className="card" style={{ padding: 16, textAlign: "center" }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--yellow)" }}>{stats.idle}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Idle</div>
            </div>
            <div className="card" style={{ padding: 16, textAlign: "center" }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--red)" }}>{stats.offline}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Offline</div>
            </div>
          </div>
        )}

        {/* Action Bar */}
        <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
          {can("fleet:manage") && (
            <button className="btn-primary" onClick={() => setShowForm(true)}>
              + Add Truck
            </button>
          )}
          {can("fleet:manage") && (
            <button className="btn-ghost" onClick={() => setShowBulkImport(true)}>
              📥 Bulk Import (CSV)
            </button>
          )}
          {can("fleet:manage") && (
            <button className="btn-ghost" onClick={syncGPSTrace} disabled={syncing}>
              {syncing ? "Syncing..." : "🔄 Sync GPS-Trace"}
            </button>
          )}
          <div style={{ flex: 1 }} />
          <input
            type="text"
            placeholder="Search trucks..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ padding: "8px 12px", fontSize: "0.78rem", width: 200, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6 }}
          />
          <select
            value={filterFacility}
            onChange={e => setFilterFacility(e.target.value)}
            style={{ padding: "8px 12px", fontSize: "0.78rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6 }}
          >
            <option value="">All Facilities</option>
            {FACILITIES.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>

        {/* Add Truck Form Modal */}
        {showForm && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div className="card" style={{ padding: 24, width: 500, maxWidth: "90vw" }}>
              <div style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16 }}>Register New Truck</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>Truck ID *</label>
                  <input type="text" value={form.truck_id} onChange={e => setForm({ ...form, truck_id: e.target.value })} placeholder="TRK-001" style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4 }} />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>Driver Name *</label>
                  <input type="text" value={form.driver_name} onChange={e => setForm({ ...form, driver_name: e.target.value })} placeholder="John Smith" style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4 }} />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>GPS Device ID</label>
                  <input type="text" value={form.device_id} onChange={e => setForm({ ...form, device_id: e.target.value })} placeholder="DEV-12345" style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4 }} />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>License Plate</label>
                  <input type="text" value={form.license_plate} onChange={e => setForm({ ...form, license_plate: e.target.value })} placeholder="ABC-1234" style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4 }} />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>Home Facility</label>
                  <select value={form.home_facility} onChange={e => setForm({ ...form, home_facility: e.target.value })} style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4 }}>
                    <option value="">Select...</option>
                    {FACILITIES.map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 20 }}>
                  <input type="checkbox" checked={form.reefer_equipped} onChange={e => setForm({ ...form, reefer_equipped: e.target.checked })} id="reefer" />
                  <label htmlFor="reefer" style={{ fontSize: "0.78rem" }}>Reefer Equipped</label>
                </div>
                <div style={{ gridColumn: "1 / -1" }}>
                  <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>Notes</label>
                  <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Optional notes..." rows={2} style={{ width: "100%", padding: "10px", fontSize: "0.8rem", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, marginTop: 4, resize: "vertical" }} />
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, marginTop: 20, justifyContent: "flex-end" }}>
                <button className="btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
                <button className="btn-primary" onClick={createTruck} disabled={saving}>{saving ? "Saving..." : "Register Truck"}</button>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Import Modal */}
        {showBulkImport && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div className="card" style={{ padding: 24, width: 600, maxWidth: "90vw", maxHeight: "80vh", overflow: "auto" }}>
              <div style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16 }}>Bulk Import Trucks</div>
              
              <div style={{ marginBottom: 16, padding: 12, background: "var(--bg-secondary)", borderRadius: 8, fontSize: "0.75rem" }}>
                <b>CSV Format:</b> truck_id, driver_name, device_id, license_plate, facility, reefer<br/>
                <b>Example:</b> TRK-001, John Smith, DEV-123, ABC-1234, Chicago DC, true
              </div>

              <input type="file" accept=".csv" ref={fileInputRef} onChange={handleCSVUpload} style={{ marginBottom: 16 }} />

              {bulkData.length > 0 && (
                <>
                  <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: 8 }}>Preview ({bulkData.length} trucks)</div>
                  <div style={{ maxHeight: 200, overflow: "auto", marginBottom: 16, border: "1px solid var(--border)", borderRadius: 6 }}>
                    <table style={{ width: "100%", fontSize: "0.72rem", borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ background: "var(--bg-secondary)" }}>
                          <th style={{ padding: 8, textAlign: "left" }}>Truck ID</th>
                          <th style={{ padding: 8, textAlign: "left" }}>Driver</th>
                          <th style={{ padding: 8, textAlign: "left" }}>Device</th>
                          <th style={{ padding: 8, textAlign: "left" }}>Facility</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bulkData.slice(0, 10).map((t, i) => (
                          <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                            <td style={{ padding: 8 }}>{t.truck_id}</td>
                            <td style={{ padding: 8 }}>{t.driver_name}</td>
                            <td style={{ padding: 8 }}>{t.device_id || "-"}</td>
                            <td style={{ padding: 8 }}>{t.home_facility || "-"}</td>
                          </tr>
                        ))}
                        {bulkData.length > 10 && (
                          <tr><td colSpan={4} style={{ padding: 8, textAlign: "center", color: "var(--text-muted)" }}>...and {bulkData.length - 10} more</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {importResult && (
                <div style={{ marginBottom: 16, padding: 12, background: importResult.created > 0 ? "var(--green)" + "15" : "var(--yellow)" + "15", borderRadius: 8, fontSize: "0.75rem" }}>
                  <b>Import Result:</b> {importResult.created} created, {importResult.skipped} skipped (duplicates)
                </div>
              )}

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button className="btn-ghost" onClick={() => { setShowBulkImport(false); setBulkData([]); setImportResult(null); }}>Close</button>
                <button className="btn-primary" onClick={importBulkTrucks} disabled={saving || bulkData.length === 0}>{saving ? "Importing..." : `Import ${bulkData.length} Trucks`}</button>
              </div>
            </div>
          </div>
        )}

        {/* Trucks Table */}
        <div className="card" style={{ overflow: "hidden" }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>Loading fleet...</div>
          ) : filteredTrucks.length === 0 ? (
            <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              No trucks found. Add trucks manually or sync from GPS-Trace.
            </div>
          ) : (
            <table style={{ width: "100%", fontSize: "0.78rem", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--bg-secondary)" }}>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Truck ID</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Driver</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Device ID</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Plate</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Facility</th>
                  <th style={{ padding: "12px 16px", textAlign: "center", fontWeight: 600 }}>Status</th>
                  <th style={{ padding: "12px 16px", textAlign: "center", fontWeight: 600 }}>Temp</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Source</th>
                  <th style={{ padding: "12px 16px", textAlign: "center", fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrucks.map((truck) => (
                  <tr key={truck.truck_id} style={{ borderTop: "1px solid var(--border)", opacity: truck.active ? 1 : 0.5 }}>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{truck.truck_id}</td>
                    <td style={{ padding: "12px 16px" }}>{truck.driver_name}</td>
                    <td style={{ padding: "12px 16px", fontFamily: "monospace", fontSize: "0.7rem" }}>{truck.device_id || "-"}</td>
                    <td style={{ padding: "12px 16px" }}>{truck.license_plate || "-"}</td>
                    <td style={{ padding: "12px 16px" }}>{truck.home_facility || "-"}</td>
                    <td style={{ padding: "12px 16px", textAlign: "center" }}>
                      {truck.live_data?.status ? (
                        <span style={{
                          padding: "4px 8px", borderRadius: 4, fontSize: "0.68rem", fontWeight: 600,
                          background: truck.live_data.status === "in_transit" ? "var(--green)" + "20" : "var(--yellow)" + "20",
                          color: truck.live_data.status === "in_transit" ? "var(--green)" : "var(--yellow)",
                        }}>
                          {truck.live_data.status}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>-</span>
                      )}
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "center" }}>
                      {truck.live_data?.reefer_temp_c !== undefined ? (
                        <span style={{ fontFamily: "monospace" }}>{truck.live_data.reefer_temp_c.toFixed(1)}°C</span>
                      ) : "-"}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span style={{
                        padding: "2px 6px", borderRadius: 3, fontSize: "0.65rem",
                        background: truck.source === "gps_trace" ? "var(--teal)" + "20" : "var(--border)",
                        color: truck.source === "gps_trace" ? "var(--teal)" : "var(--text-muted)",
                      }}>
                        {truck.source || "manual"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "center" }}>
                      <button onClick={() => deleteTruck(truck.truck_id)} style={{ padding: "4px 8px", fontSize: "0.7rem", background: "var(--red)" + "15", color: "var(--red)", border: "none", borderRadius: 4, cursor: "pointer" }}>
                        {truck.active ? "Deactivate" : "Deleted"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
