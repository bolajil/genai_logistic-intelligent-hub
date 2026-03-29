"use client";
import { useState, useEffect } from "react";
import Header from "@/components/Header";
import { getHealthDetailed, BASE, authHeaders } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import { useAuth } from "@/app/contexts/AuthContext";

const AUDIT = [
  { user: "Lanre Bolaji", action: "rag_query",          resource: "lineage-sops",     time: "1m ago" },
  { user: "Lanre Bolaji", action: "anomaly_agent",       resource: "CHI-ATL-2025-089", time: "2m ago" },
  { user: "Lanre Bolaji", action: "connector_toggle",    resource: "iot → real",        time: "1h ago" },
  { user: "Sarah Chen",   action: "user_created",        resource: "locust@glih.test",  time: "2h ago" },
  { user: "Marcus Webb",  action: "rag_query",           resource: "lineage-sops",      time: "3h ago" },
  { user: "Sarah Chen",   action: "api_key_created",     resource: "iot:ingest scope",  time: "1d ago" },
];

const roleColor: Record<string, string> = {
  admin: "#f59e0b", analyst: "#a78bfa", viewer: "#64748b",
};

interface LiveUser {
  id: string; name: string; email: string; role: string;
  created_at: string; force_password_change: boolean;
}

export default function AdminPage() {
  const { can, role } = usePermissions();
  const { user: me } = useAuth();
  const [tab, setTab] = useState<"users" | "audit" | "health">("users");

  if (!can("admin:users")) {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        <Header title="Admin" subtitle="System administration" />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ textAlign: "center", padding: 40 }}>
            <div style={{ fontSize: "2rem", marginBottom: 12 }}>🔒</div>
            <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>Access Restricted</div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              Admin panel requires <strong>admin</strong> role. Your current role is <strong>{role}</strong>.
            </div>
          </div>
        </div>
      </div>
    );
  }
  const [health, setHealth] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [users, setUsers] = useState<LiveUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [resetTarget, setResetTarget] = useState<LiveUser | null>(null);
  const [resetPwd, setResetPwd] = useState("");
  const [resetMsg, setResetMsg] = useState<string | null>(null);
  const [resetErr, setResetErr] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  async function fetchUsers() {
    setUsersLoading(true);
    try {
      const res = await fetch(`${BASE}/auth/users`, { headers: authHeaders() });
      if (res.ok) { const d = await res.json(); setUsers(d.users || []); }
    } finally { setUsersLoading(false); }
  }

  async function handleReset() {
    if (!resetTarget || resetPwd.length < 8) return;
    setResetting(true); setResetMsg(null); setResetErr(null);
    try {
      const res = await fetch(`${BASE}/auth/admin/reset-password`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ user_id: resetTarget.id, new_password: resetPwd }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Reset failed");
      setResetMsg(d.message); setResetPwd(""); setResetTarget(null);
      fetchUsers();
    } catch (e: any) { setResetErr(e.message); } finally { setResetting(false); }
  }

  async function handleDelete(u: LiveUser) {
    if (!confirm(`Delete ${u.name} (${u.email})? This cannot be undone.`)) return;
    const res = await fetch(`${BASE}/auth/users/${u.id}`, { method: "DELETE", headers: authHeaders() });
    if (res.ok || res.status === 204) fetchUsers();
  }

  useEffect(() => { if (tab === "users") fetchUsers(); }, [tab]);

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
            {resetMsg && <div style={{ background: "#052e16", border: "1px solid #14532d", borderRadius: 6, padding: "10px 14px", color: "#4ade80", fontSize: "0.75rem", marginBottom: 12 }}>✓ {resetMsg}</div>}
            {usersLoading
              ? <div style={{ color: "var(--text-muted)", padding: 20, fontSize: "0.8rem" }}>Loading users...</div>
              : (
              <div className="card" style={{ overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                  <thead>
                    <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
                      {["Name", "Email", "Role", "Status", "Actions"].map(h => (
                        <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "var(--text-muted)", fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.06em" }}>{h.toUpperCase()}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "10px 14px", color: "var(--text-primary)", fontWeight: 600 }}>
                          {u.name} {u.id === (me as any)?.id && <span style={{ fontSize: "0.58rem", color: "var(--teal)" }}>YOU</span>}
                        </td>
                        <td style={{ padding: "10px 14px", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "0.68rem" }}>{u.email}</td>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{ color: roleColor[u.role] || "#64748b", fontSize: "0.68rem", fontWeight: 700 }}>{u.role}</span>
                        </td>
                        <td style={{ padding: "10px 14px" }}>
                          {u.force_password_change
                            ? <span style={{ color: "#f59e0b", fontSize: "0.65rem" }}>⚠ Must change pwd</span>
                            : <span style={{ color: "#4ade80", fontSize: "0.65rem" }}>● Active</span>}
                        </td>
                        <td style={{ padding: "10px 14px", display: "flex", gap: 6 }}>
                          <button className="btn-ghost" style={{ fontSize: "0.62rem", padding: "3px 8px" }}
                            onClick={() => { setResetTarget(u); setResetPwd(""); setResetErr(null); }}>
                            Reset Pwd
                          </button>
                          {u.id !== (me as any)?.id && (
                            <button className="btn-ghost" style={{ fontSize: "0.62rem", padding: "3px 8px", color: "#f87171" }}
                              onClick={() => handleDelete(u)}>
                              Delete
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Reset Password Modal */}
            {resetTarget && (
              <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
                onClick={e => { if (e.target === e.currentTarget) setResetTarget(null); }}>
                <div className="card" style={{ width: 400, padding: 24 }}>
                  <div style={{ fontWeight: 700, marginBottom: 4 }}>Reset Password</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 16 }}>{resetTarget.name} · {resetTarget.email}</div>
                  <input type="password" value={resetPwd} onChange={e => setResetPwd(e.target.value)}
                    placeholder="New password (min 8 chars)"
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, padding: "9px 12px", color: "var(--text-primary)", fontSize: "0.8rem", marginBottom: 10 }} />
                  {resetErr && <div style={{ color: "#f87171", fontSize: "0.72rem", marginBottom: 8 }}>✗ {resetErr}</div>}
                  <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                    <button className="btn-ghost" onClick={() => setResetTarget(null)}>Cancel</button>
                    <button className="btn-primary" onClick={handleReset} disabled={resetting || resetPwd.length < 8}>
                      {resetting ? "Resetting..." : "Reset & Force Change"}
                    </button>
                  </div>
                </div>
              </div>
            )}
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
