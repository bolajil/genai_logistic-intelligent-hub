"use client";
import { useEffect, useState } from "react";
import Header from "@/components/Header";

// Demo shipments (shown in table + sensor feed)
const DEMO_SHIPMENTS = [
  { id: "CHI-ATL-2025-089", route: "Chicago → Atlanta",    product: "Dairy",       temp: 5.2,  status: "BREACH",    eta: "18:00 UTC" },
  { id: "TX-CHI-2025-001",  route: "Dallas → Chicago",     product: "Seafood",     temp: 0.5,  status: "IN TRANSIT", eta: "14:00 UTC" },
  { id: "BOS-CHI-2025-332", route: "Boston → Chicago",     product: "Produce",     temp: 3.1,  status: "DELAYED",   eta: "16:30 UTC" },
  { id: "LA-SEA-2025-156",  route: "Los Angeles → Seattle", product: "Frozen",     temp: -20,  status: "DELIVERED", eta: "—" },
  { id: "CHI-LA-2025-445",  route: "Chicago → Los Angeles", product: "Meat",       temp: -18.4, status: "IN TRANSIT", eta: "22:00 UTC" },
];

const DEMO_ALERTS = [
  { severity: "HIGH",   type: "TEMPERATURE BREACH",  msg: "CHI-ATL-2025-089 dairy at 5.2°C — exceeds 4°C threshold by 1.2°C for 22 min", agent: "AnomalyResponder · SOP-COLD-CHAIN-003 applied", time: "2m ago" },
  { severity: "MEDIUM", type: "DELAY RISK",           msg: "BOS-CHI-2025-332 approaching threshold — 45 min delay, temp rising to 3.1°C",  agent: "RouteAdvisor · Monitoring",                   time: "14m ago" },
  { severity: "INFO",   type: "DELIVERY CONFIRMED",   msg: "LA-SEA-2025-156 frozen foods delivered at −20°C — full compliance maintained",  agent: "CustomerNotifier · Amazon Fresh notified",      time: "1h ago" },
];

const AGENT_ACTIVITY = [
  { name: "AnomalyResponder", detail: "CHI-ATL-2025-089 · 5.2°C breach",  action: "Action plan generated", time: "3m ago",  color: "#ef4444" },
  { name: "CustomerNotifier", detail: "Whole Foods · email sent",           action: "Delivered",             time: "7m ago",  color: "#22d3ee" },
  { name: "RouteAdvisor",     detail: "TX-CHI-2025-001 · 68% risk",        action: "Via Hub recommended",   time: "18m ago", color: "#a78bfa" },
  { name: "OpsSummarizer",    detail: "08:00 shift handoff · 24h window",  action: "Report exported PDF",   time: "6h ago",  color: "#f59e0b" },
];

function statusBadge(status: string) {
  const map: Record<string, string> = {
    "BREACH":     "badge-breach",
    "IN TRANSIT": "badge-transit",
    "DELAYED":    "badge-delayed",
    "DELIVERED":  "badge-delivered",
  };
  return map[status] || "badge-ok";
}

function severityBadge(s: string) {
  return s === "HIGH" ? "badge-high" : s === "MEDIUM" ? "badge-medium" : "badge-info";
}

function TempBar({ temp }: { temp: number }) {
  // map -25 to +10 range to 0-100%
  const pct = Math.max(0, Math.min(100, ((temp + 25) / 35) * 100));
  const color = temp > 4 ? "#ef4444" : temp > 2 ? "#f59e0b" : "#10b981";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
      <div className="temp-bar" style={{ flex: 1 }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: "0.85rem", color, fontWeight: 700, minWidth: 54, textAlign: "right" }}>
        {temp > 0 ? "+" : ""}{temp}°C
      </span>
    </div>
  );
}

export default function DashboardPage() {
  const [tick, setTick] = useState(0);
  const [temps, setTemps] = useState(DEMO_SHIPMENTS.map(s => s.temp));

  // Simulate live temperature drift
  useEffect(() => {
    const interval = setInterval(() => {
      setTemps(prev => prev.map((t, i) => {
        const drift = (Math.random() - 0.5) * 0.3;
        const base = DEMO_SHIPMENTS[i].temp;
        return parseFloat((Math.max(base - 1, Math.min(base + 1, t + drift))).toFixed(1));
      }));
      setTick(t => t + 1);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header
        title="Operations Dashboard"
        subtitle={`Chicago Hub · ${new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })} · ${new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" })} UTC`}
        live
      />

      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        {/* KPI Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 20 }}>
          {[
            { label: "Active Shipments", value: "847", delta: "+12 from yesterday",   color: "var(--teal)",   icon: "🚚" },
            { label: "Active Alerts",    value: "3",   delta: "+2 in last hour",       color: "var(--amber)",  icon: "⚠" },
            { label: "Temp Compliance",  value: "99.1%", delta: "+0.4% vs last week", color: "var(--green)",  icon: "✓" },
            { label: "On-Time Delivery", value: "94.2%", delta: "−1.3% vs last week", color: "var(--purple)", icon: "⏱" },
          ].map(({ label, value, delta, color, icon }) => (
            <div key={label} className="card" style={{ padding: "16px 18px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 6, letterSpacing: "0.05em" }}>
                    {label.toUpperCase()}
                  </div>
                  <div style={{ fontSize: "1.8rem", fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 6 }}>{delta}</div>
                </div>
                <span style={{ fontSize: "1.4rem", opacity: 0.3 }}>{icon}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 380px", gap: 14, marginBottom: 14 }}>

          {/* Live Sensor Feed */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span className="pulse-dot teal" />
                <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--teal)", letterSpacing: "0.08em" }}>
                  LIVE SENSOR FEED
                </span>
              </div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>5s refresh</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {DEMO_SHIPMENTS.map((s, i) => {
                const t = temps[i];
                const chip = t > 4 ? { label: "BREACH", cls: "badge-breach" }
                           : t > 2 ? { label: "WATCH",  cls: "badge-watch"  }
                           :         { label: "OK",      cls: "badge-ok"     };
                return (
                  <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: "0.82rem", color: "var(--text-muted)", minWidth: 140, fontFamily: "monospace" }}>
                      {s.id}
                    </span>
                    <TempBar temp={t} />
                    <span className={`badge ${chip.cls}`}>{chip.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Agent Activity */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ color: "var(--teal)", fontSize: "0.7rem", fontWeight: 700, letterSpacing: "0.08em" }}>
                  ⚡ AGENT ACTIVITY
                </span>
              </div>
              <a href="/agents" style={{ fontSize: "0.65rem", color: "var(--text-muted)", textDecoration: "none" }}>History →</a>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {AGENT_ACTIVITY.map(a => (
                <div key={a.name} style={{ display: "flex", gap: 10 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%",
                    background: a.color + "22", border: `1px solid ${a.color}44`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                    fontSize: "0.65rem", color: a.color, fontWeight: 700,
                  }}>
                    {a.name[0]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", fontWeight: 600 }}>{a.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{a.detail}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--green)", marginTop: 2 }}>✓ {a.action}</div>
                  </div>
                  <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", whiteSpace: "nowrap" }}>{a.time}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.06em" }}>
                ● ACTIVE ALERTS
              </span>
              <a href="/alerts" style={{ fontSize: "0.65rem", color: "var(--text-muted)", textDecoration: "none" }}>View all →</a>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {DEMO_ALERTS.map((a, i) => (
                <div key={i} style={{
                  padding: "10px 12px",
                  borderRadius: 6,
                  background: a.severity === "HIGH" ? "#1a0505" : a.severity === "MEDIUM" ? "#1a0e05" : "#050f1a",
                  border: `1px solid ${a.severity === "HIGH" ? "#7f1d1d" : a.severity === "MEDIUM" ? "#7c2d12" : "#1e3a5f"}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <span className={`badge ${severityBadge(a.severity)}`}>{a.severity}</span>
                    <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", letterSpacing: "0.05em" }}>{a.type}</span>
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>{a.msg}</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: 4 }}>{a.agent} · {a.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Shipments + Compliance */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 14 }}>

          {/* Shipments table */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontSize: "0.7rem", fontWeight: 700, letterSpacing: "0.06em" }}>RECENT SHIPMENTS</span>
              <a href="/shipments" style={{ fontSize: "0.65rem", color: "var(--text-muted)", textDecoration: "none" }}>
                View all 847 →
              </a>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Shipment ID", "Route", "Product", "Temp", "Status", "ETA"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "6px 10px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.72rem", letterSpacing: "0.05em" }}>
                      {h.toUpperCase()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DEMO_SHIPMENTS.map((s, i) => (
                  <tr key={s.id} style={{ borderBottom: "1px solid var(--border)" }}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "var(--bg-card)"}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                  >
                    <td style={{ padding: "10px 10px", fontFamily: "monospace", color: "var(--teal)", fontSize: "0.82rem" }}>
                      {s.id}
                    </td>
                    <td style={{ padding: "8px 8px", color: "var(--text-secondary)" }}>{s.route}</td>
                    <td style={{ padding: "8px 8px" }}>
                      <span className="badge badge-transit" style={{ background: "#0c1a3a", color: "#93c5fd" }}>{s.product}</span>
                    </td>
                    <td style={{ padding: "8px 8px", color: temps[i] > 4 ? "#ef4444" : temps[i] > 2 ? "#f59e0b" : "#4ade80", fontWeight: 700 }}>
                      {temps[i] > 0 ? "+" : ""}{temps[i]}°C {temps[i] > 4 ? "▲" : ""}
                    </td>
                    <td style={{ padding: "8px 8px" }}>
                      <span className={`badge ${statusBadge(s.status)}`}>{s.status}</span>
                    </td>
                    <td style={{ padding: "8px 8px", color: "var(--text-muted)" }}>{s.eta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Compliance gauge */}
          <div className="card" style={{ padding: 16, display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, marginBottom: 16, letterSpacing: "0.06em" }}>
              COMPLIANCE SCORE — 7-day
            </div>
            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--green)" }}>99.1%</div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", letterSpacing: "0.08em" }}>TEMPERATURE COMPLIANCE</div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.6rem", color: "var(--text-dim)", marginBottom: 4 }}>
                <span>0%</span><span>Target 99%</span><span>100%</span>
              </div>
              <div className="temp-bar" style={{ height: 10 }}>
                <div style={{ height: "100%", width: "99.1%", background: "var(--green)", borderRadius: 5 }} />
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                { label: "Shipments",     value: "847",  color: "var(--teal)"  },
                { label: "Breaches",      value: "3",    color: "var(--red)"   },
                { label: "Avg Response",  value: "12m",  color: "var(--green)" },
                { label: "Waste Prevented", value: "$2.1M", color: "var(--purple)" },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: "var(--bg-secondary)", borderRadius: 6, padding: "10px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: "1.1rem", fontWeight: 800, color }}>{value}</div>
                  <div style={{ fontSize: "0.6rem", color: "var(--text-muted)", marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
