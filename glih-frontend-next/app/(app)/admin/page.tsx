"use client";
import { useState, useEffect } from "react";
import Header from "@/components/Header";
import { getHealthDetailed } from "@/lib/api";

const USERS = [
  { id: 1, name: "Lanre Bolaji",  email: "lanre@lineage.com",    role: "ops-manager", last: "Now" },
  { id: 2, name: "Sarah Chen",    email: "s.chen@lineage.com",   role: "admin",       last: "2h ago" },
  { id: 3, name: "Marcus Webb",   email: "m.webb@lineage.com",   role: "analyst",     last: "1d ago" },
  { id: 4, name: "Priya Sharma",  email: "p.sharma@lineage.com", role: "viewer",      last: "3d ago" },
  { id: 5, name: "locust-test",   email: "locust@glih.test",     role: "analyst",     last: "Load test" },
];

const AUDIT = [
  { user: "Lanre Bolaji", action: "rag_query",          resource: "lineage-sops",     time: "1m ago" },
  { user: "Lanre Bolaji", action: "anomaly_agent",       resource: "CHI-ATL-2025-089", time: "2m ago" },
  { user: "Lanre Bolaji", action: "connector_toggle",    resource: "iot → real",        time: "1h ago" },
  { user: "Sarah Chen",   action: "user_created",        resource: "locust@glih.test",  time: "2h ago" },
  { user: "Marcus Webb",  action: "rag_query",           resource: "lineage-sops",      time: "3h ago" },
  { user: "Sarah Chen",   action: "api_key_created",     resource: "iot:ingest scope",  time: "1d ago" },
];

const roleColor: Record<string, string> = {
  admin: "#f59e0b", "ops-manager": "#22d3ee", analyst: "#a78bfa", viewer: "#64748b",
};

export default function AdminPage() {
  const [tab, setTab] = useState<"users" | "audit" | "health">("users");
  const [health, setHealth] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  useEffect(() => {
    if (tab === "health") {
      setHealthLoading(true);
      getHealthDetailed()
        .then(setHealth)
        .catch(() => setHealth(null))
        .finally(() => setHealthLoading(false));
    }
  }, [tab]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Admin" subtitle="User management · Audit log · System health" />
      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        <div style={{ display: "flex", gap: 0, marginBottom: 16, borderBottom: "1px solid var(--border)" }}>
          {[["users", "👥 Users"], ["audit", "📋 Audit Log"], ["health", "💚 System Health"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as any)} style={{
              padding: "8px 18px", background: "transparent", border: "none",
              borderBottom: tab === id ? "2px solid var(--teal)" : "2px solid transparent",
              color: tab === id ? "var(--teal)" : "var(--text-muted)",
              fontSize: "0.8rem", fontWeight: tab === id ? 700 : 400, cursor: "pointer", marginBottom: -1,
            }}>{label}</button>
          ))}
        </div>

        {tab === "users" && (
          <div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
              <button className="btn-primary">+ Add User</button>
            </div>
            <div className="card" style={{ overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                <thead>
                  <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
                    {["Name", "Email", "Role", "Last Active", "Actions"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "var(--text-muted)", fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.06em" }}>{h.toUpperCase()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {USERS.map(u => (
                    <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 14px", color: "var(--text-primary)", fontWeight: 600 }}>{u.name}</td>
                      <td style={{ padding: "10px 14px", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "0.68rem" }}>{u.email}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{ color: roleColor[u.role] || "#64748b", fontSize: "0.68rem", fontWeight: 700 }}>{u.role}</span>
                      </td>
                      <td style={{ padding: "10px 14px", color: "var(--text-muted)" }}>{u.last}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <button className="btn-ghost" style={{ fontSize: "0.62rem", padding: "3px 8px" }}>Edit</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "audit" && (
          <div className="card" style={{ overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
              <thead>
                <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
                  {["User", "Action", "Resource", "Time"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "var(--text-muted)", fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.06em" }}>{h.toUpperCase()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {AUDIT.map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 14px", color: "var(--text-primary)" }}>{a.user}</td>
                    <td style={{ padding: "10px 14px", color: "var(--teal)", fontFamily: "monospace", fontSize: "0.68rem" }}>{a.action}</td>
                    <td style={{ padding: "10px 14px", color: "var(--text-secondary)" }}>{a.resource}</td>
                    <td style={{ padding: "10px 14px", color: "var(--text-muted)" }}>{a.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "health" && (
          <div>
            {healthLoading && <div style={{ color: "var(--text-muted)", padding: 20 }}>Loading health status...</div>}

            {health && (
              <>
                {/* Live provider status */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 16 }}>
                  {Object.entries(health.providers || {}).map(([key, val]: [string, any]) => (
                    <div key={key} className="card" style={{ padding: 14 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                        <span className={`pulse-dot ${val.available ? "green" : "red"}`} />
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "capitalize" }}>{key}</span>
                        <span style={{ fontSize: "0.62rem", marginLeft: "auto", color: val.available ? "#4ade80" : "#f87171" }}>
                          {val.available ? "LIVE" : "OFFLINE"}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        {val.provider}/{val.model || val.collection || ""}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Collections */}
                {health.collections?.length > 0 && (
                  <div className="card" style={{ padding: 16 }}>
                    <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.08em", marginBottom: 10 }}>
                      VECTOR STORE COLLECTIONS
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {health.collections.map((c: string) => (
                        <span key={c} style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 4, padding: "4px 10px", fontSize: "0.7rem", color: "var(--teal)", fontFamily: "monospace" }}>
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Static services */}
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.08em", marginBottom: 10 }}>
                ALL SERVICES
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                {[
                  { name: "Next.js Frontend", port: 9000, live: true },
                  { name: "FastAPI Backend",  port: 9001, live: !!health },
                  { name: "WMS MCP Server",   port: 9002, live: false },
                  { name: "IoT MCP Server",   port: 9003, live: false },
                  { name: "Docs MCP Server",  port: 9004, live: false },
                  { name: "MQTT Broker",      port: 9005, live: false },
                  { name: "PostgreSQL",       port: 9006, live: false },
                  { name: "Redis",            port: 9007, live: false },
                  { name: "Langfuse",         port: 9008, live: false },
                  { name: "Locust",           port: 9009, live: false },
                ].map(s => (
                  <div key={s.name} className="card" style={{ padding: 12, display: "flex", alignItems: "center", gap: 10 }}>
                    <span className={`pulse-dot ${s.live ? "green" : "amber"}`} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600 }}>{s.name}</div>
                      <div style={{ fontSize: "0.6rem", color: "var(--text-muted)", fontFamily: "monospace" }}>:{s.port}</div>
                    </div>
                    <span style={{ fontSize: "0.6rem", color: s.live ? "#4ade80" : "#f59e0b" }}>
                      {s.live ? "UP" : "DEMO"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
