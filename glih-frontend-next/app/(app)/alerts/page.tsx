"use client";
import { useState } from "react";
import Header from "@/components/Header";

const ALERTS = [
  { id: 1, severity: "HIGH",   type: "Temperature Breach",  shipment: "CHI-ATL-2025-089", msg: "Dairy at 5.2°C — exceeds 4°C threshold by 1.2°C for 22 min",        agent: "AnomalyResponder", sop: "SOP-COLD-CHAIN-003 §4.2", status: "ACTIVE",   time: "2m ago",  resolution: null },
  { id: 2, severity: "MEDIUM", type: "Delay Risk",          shipment: "BOS-CHI-2025-332", msg: "45 min delay — temp rising to 3.1°C, approaching threshold",          agent: "RouteAdvisor",     sop: "SOP-ROUTE-007 §2.1",     status: "ACTIVE",   time: "14m ago", resolution: null },
  { id: 3, severity: "HIGH",   type: "Temperature Breach",  shipment: "DAL-MIA-2025-210", msg: "Produce at 7.2°C — exceeds 10°C safe zone warning, driver alerted",   agent: "AnomalyResponder", sop: "SOP-COLD-CHAIN-001 §3.1", status: "ACTIVE",   time: "31m ago", resolution: null },
  { id: 4, severity: "INFO",   type: "Delivery Confirmed",  shipment: "LA-SEA-2025-156",  msg: "Frozen foods delivered at −20°C — full compliance maintained",         agent: "CustomerNotifier", sop: null,                     status: "RESOLVED", time: "1h ago",  resolution: "Delivered in compliance" },
  { id: 5, severity: "MEDIUM", type: "Sensor Offline",      shipment: "TX-CHI-2025-001",  msg: "IoT sensor dropped for 4 min — reconnected, no temperature anomaly",   agent: "AnomalyResponder", sop: "SOP-IOT-002 §1.3",        status: "RESOLVED", time: "2h ago",  resolution: "Sensor reconnected" },
  { id: 6, severity: "HIGH",   type: "Temperature Breach",  shipment: "CHI-SEA-2025-071", msg: "Seafood at 3.8°C — threshold 2°C exceeded for 45 min, rerouted",       agent: "RouteAdvisor",     sop: "SOP-COLD-CHAIN-003 §5.1", status: "RESOLVED", time: "4h ago",  resolution: "Rerouted via hub, temp recovered" },
];

const severityColor: Record<string, { bg: string; border: string; text: string }> = {
  HIGH:   { bg: "#1a0505", border: "#7f1d1d", text: "#f87171" },
  MEDIUM: { bg: "#1a0e05", border: "#7c2d12", text: "#fdba74" },
  INFO:   { bg: "#050f1a", border: "#1e3a5f", text: "#93c5fd" },
};

export default function AlertsPage() {
  const [filter, setFilter] = useState("ALL");

  const filtered = ALERTS.filter(a =>
    filter === "ALL" ? true :
    filter === "ACTIVE" ? a.status === "ACTIVE" :
    filter === "RESOLVED" ? a.status === "RESOLVED" :
    a.severity === filter
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Alerts" subtitle={`${ALERTS.filter(a => a.status === "ACTIVE").length} active · ${ALERTS.filter(a => a.status === "RESOLVED").length} resolved`} />
      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        {/* Filter bar */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {["ALL", "ACTIVE", "RESOLVED", "HIGH", "MEDIUM", "INFO"].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "6px 14px", borderRadius: 6, fontSize: "0.72rem", cursor: "pointer",
              background: filter === f ? "var(--teal)" : "var(--bg-card)",
              color: filter === f ? "#020d1a" : "var(--text-muted)",
              border: filter === f ? "none" : "1px solid var(--border)",
              fontWeight: filter === f ? 700 : 400,
            }}>{f}</button>
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filtered.map(alert => {
            const c = severityColor[alert.severity];
            return (
              <div key={alert.id} style={{
                background: c.bg, border: `1px solid ${c.border}`,
                borderRadius: 8, padding: 16,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className={`badge badge-${alert.severity.toLowerCase()}`}>{alert.severity}</span>
                    <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-primary)" }}>{alert.type}</span>
                    <span style={{ fontSize: "0.65rem", color: "var(--teal)", fontFamily: "monospace" }}>{alert.shipment}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{alert.time}</span>
                    <span style={{
                      padding: "3px 10px", borderRadius: 4, fontSize: "0.62rem", fontWeight: 700,
                      background: alert.status === "ACTIVE" ? "#450a0a" : "#052e16",
                      color: alert.status === "ACTIVE" ? "#f87171" : "#4ade80",
                      border: `1px solid ${alert.status === "ACTIVE" ? "#7f1d1d" : "#14532d"}`,
                    }}>{alert.status}</span>
                  </div>
                </div>

                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: 10 }}>{alert.msg}</div>

                <div style={{ display: "flex", gap: 20, fontSize: "0.65rem" }}>
                  <div>
                    <span style={{ color: "var(--text-dim)" }}>Agent: </span>
                    <span style={{ color: "var(--teal)" }}>{alert.agent}</span>
                  </div>
                  {alert.sop && (
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>SOP: </span>
                      <span style={{ color: "var(--amber)" }}>📄 {alert.sop}</span>
                    </div>
                  )}
                  {alert.resolution && (
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>Resolution: </span>
                      <span style={{ color: "#4ade80" }}>✓ {alert.resolution}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
