"use client";
import { useState, useEffect, useCallback } from "react";
import Header from "@/components/Header";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  History, Search, ChevronDown, ChevronRight, Clock, User,
  MessageSquare, Bot, Bell, RefreshCw, Filter, X, FileText,
  CheckCircle, AlertCircle, Zap, Route, Send, BarChart3
} from "lucide-react";

const BASE = "http://localhost:9001";

type Tab = "queries" | "agents" | "notifications";

const AGENT_ICONS: Record<string, React.ReactNode> = {
  AnomalyResponder: <AlertCircle size={14} />,
  RouteAdvisor:     <Route size={14} />,
  CustomerNotifier: <Send size={14} />,
  OpsSummarizer:    <BarChart3 size={14} />,
};

const AGENT_COLORS: Record<string, string> = {
  AnomalyResponder: "#ef4444",
  RouteAdvisor:     "#22d3ee",
  CustomerNotifier: "#a78bfa",
  OpsSummarizer:    "#10b981",
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#f59e0b",
  low:      "#10b981",
};

function formatDate(iso: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function DurationBadge({ ms }: { ms?: number }) {
  if (!ms) return null;
  const s = (ms / 1000).toFixed(1);
  const color = ms < 2000 ? "#10b981" : ms < 5000 ? "#f59e0b" : "#ef4444";
  return (
    <span style={{ fontSize: 11, color, background: color + "18", padding: "2px 7px", borderRadius: 6 }}>
      {s}s
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = status === "success" ? "#10b981" : status === "error" ? "#ef4444" : "#f59e0b";
  return (
    <span style={{ fontSize: 11, color, background: color + "20", padding: "2px 8px", borderRadius: 6, fontWeight: 600, textTransform: "capitalize" }}>
      {status}
    </span>
  );
}

// ── Query Row ──────────────────────────────────────────────────────────────────
function QueryRow({ rec, isAdmin }: { rec: any; isAdmin: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border)", transition: "background 0.15s" }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(34,211,238,0.04)")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "12px 16px", width: 28 }}>
          {open ? <ChevronDown size={14} color="var(--teal)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
        </td>
        <td style={{ padding: "12px 8px", maxWidth: 280 }}>
          <div style={{ fontSize: 13, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {rec.query}
          </div>
        </td>
        {isAdmin && (
          <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            {rec.user_email}
          </td>
        )}
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)" }}>{rec.collection || "—"}</td>
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)" }}>{rec.model || "—"}</td>
        <td style={{ padding: "12px 8px" }}><DurationBadge ms={rec.duration_ms} /></td>
        <td style={{ padding: "12px 16px", fontSize: 12, color: "var(--text-dim)", whiteSpace: "nowrap" }}>{formatDate(rec.timestamp)}</td>
      </tr>
      {open && (
        <tr style={{ background: "rgba(15,31,61,0.6)" }}>
          <td colSpan={isAdmin ? 7 : 6} style={{ padding: "0 16px 16px 44px" }}>
            <div style={{ display: "grid", gap: 12 }}>
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Answer</div>
                <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, background: "rgba(34,211,238,0.04)", padding: "10px 14px", borderRadius: 8, border: "1px solid var(--border)" }}>
                  {rec.answer}
                </div>
              </div>
              {rec.citations?.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>
                    Citations ({rec.citations.length})
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {rec.citations.map((c: any, i: number) => (
                      <div key={i} style={{ fontSize: 12, color: "var(--text-secondary)", background: "rgba(167,139,250,0.06)", padding: "8px 12px", borderRadius: 6, border: "1px solid rgba(167,139,250,0.15)" }}>
                        <span style={{ color: "var(--purple)", fontWeight: 600 }}>{c.source || c.doc_id || `Chunk ${i + 1}`}</span>
                        {c.distance != null && <span style={{ color: "var(--text-dim)", marginLeft: 8 }}>dist: {c.distance?.toFixed(3)}</span>}
                        {c.snippet && <div style={{ marginTop: 4, color: "var(--text-muted)", fontStyle: "italic" }}>{c.snippet.slice(0, 200)}{c.snippet.length > 200 ? "…" : ""}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Agent Run Row ──────────────────────────────────────────────────────────────
function AgentRunRow({ rec, isAdmin }: { rec: any; isAdmin: boolean }) {
  const [open, setOpen] = useState(false);
  const color = AGENT_COLORS[rec.agent_name] || "var(--teal)";
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border)", transition: "background 0.15s" }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(34,211,238,0.04)")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "12px 16px", width: 28 }}>
          {open ? <ChevronDown size={14} color="var(--teal)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
        </td>
        <td style={{ padding: "12px 8px" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color, background: color + "18", padding: "3px 9px", borderRadius: 6, fontWeight: 600 }}>
            {AGENT_ICONS[rec.agent_name]}{rec.agent_name}
          </span>
        </td>
        {isAdmin && (
          <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap" }}>{rec.user_email}</td>
        )}
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>
          {rec.run_id?.slice(0, 8)}…
        </td>
        <td style={{ padding: "12px 8px" }}><StatusBadge status={rec.status} /></td>
        <td style={{ padding: "12px 8px" }}><DurationBadge ms={rec.duration_ms} /></td>
        <td style={{ padding: "12px 16px", fontSize: 12, color: "var(--text-dim)", whiteSpace: "nowrap" }}>{formatDate(rec.timestamp)}</td>
      </tr>
      {open && (
        <tr style={{ background: "rgba(15,31,61,0.6)" }}>
          <td colSpan={isAdmin ? 7 : 6} style={{ padding: "0 16px 16px 44px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {/* Input */}
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Input</div>
                <pre style={{ fontSize: 11, color: "var(--text-secondary)", background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6, overflow: "auto", maxHeight: 160, border: "1px solid var(--border)" }}>
                  {JSON.stringify(rec.input, null, 2)}
                </pre>
              </div>
              {/* Progress Events */}
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Events ({rec.events?.length || 0})</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 160, overflow: "auto" }}>
                  {(rec.events || []).map((ev: any, i: number) => {
                    const stepColor =
                      ev.step === "complete" ? "#10b981" :
                      ev.step === "error" ? "#ef4444" :
                      ev.step === "llm_call" || ev.step === "llm_done" ? "#a78bfa" :
                      ev.step === "retrieval" || ev.step === "retrieval_done" ? "#f59e0b" : "var(--teal)";
                    return (
                      <div key={i} style={{ fontSize: 11, display: "flex", gap: 8, alignItems: "flex-start" }}>
                        <span style={{ color: stepColor, fontWeight: 700, minWidth: 90, flexShrink: 0 }}>{ev.step}</span>
                        <span style={{ color: "var(--text-muted)" }}>{ev.message}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* Result (full width) */}
              {rec.result && (
                <div style={{ gridColumn: "1 / -1" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Result</div>
                  <pre style={{ fontSize: 11, color: "var(--text-secondary)", background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6, overflow: "auto", maxHeight: 180, border: "1px solid var(--border)" }}>
                    {JSON.stringify(rec.result?.result || rec.result, null, 2)}
                  </pre>
                </div>
              )}
              {rec.error && (
                <div style={{ gridColumn: "1 / -1" }}>
                  <div style={{ fontSize: 11, color: "#ef4444", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Error</div>
                  <div style={{ fontSize: 12, color: "#ef4444", background: "rgba(239,68,68,0.08)", padding: "8px 12px", borderRadius: 6, border: "1px solid rgba(239,68,68,0.2)" }}>
                    {rec.error}
                  </div>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Notification Row ───────────────────────────────────────────────────────────
function NotifRow({ rec, isAdmin }: { rec: any; isAdmin: boolean }) {
  const [open, setOpen] = useState(false);
  const sevColor = SEVERITY_COLORS[rec.severity?.toLowerCase()] || "var(--text-muted)";
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border)", transition: "background 0.15s" }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(34,211,238,0.04)")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "12px 16px", width: 28 }}>
          {open ? <ChevronDown size={14} color="var(--teal)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
        </td>
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-primary)", fontWeight: 600 }}>{rec.shipment_id}</td>
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-secondary)" }}>{rec.customer_id}</td>
        <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--teal)" }}>{rec.notification_type}</td>
        <td style={{ padding: "12px 8px" }}>
          <span style={{ fontSize: 11, color: sevColor, background: sevColor + "18", padding: "2px 8px", borderRadius: 6, fontWeight: 600, textTransform: "capitalize" }}>
            {rec.severity}
          </span>
        </td>
        {isAdmin && (
          <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--text-muted)" }}>{rec.dispatcher_name}</td>
        )}
        <td style={{ padding: "12px 16px", fontSize: 12, color: "var(--text-dim)", whiteSpace: "nowrap" }}>{formatDate(rec.timestamp)}</td>
      </tr>
      {open && (
        <tr style={{ background: "rgba(15,31,61,0.6)" }}>
          <td colSpan={isAdmin ? 7 : 6} style={{ padding: "0 16px 16px 44px" }}>
            <div style={{ display: "grid", gap: 8 }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Message Sent to Customer</div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7, background: "rgba(167,139,250,0.06)", padding: "12px 16px", borderRadius: 8, border: "1px solid rgba(167,139,250,0.15)", whiteSpace: "pre-wrap" }}>
                {rec.message || "(no message content saved)"}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Sent by <strong style={{ color: "var(--text-secondary)" }}>{rec.dispatcher_name}</strong>
                {rec.dispatcher_title && <> · {rec.dispatcher_title}</>}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function HistoryPage() {
  const { user } = useAuth();
  const isAdmin = (user as any)?.role === "admin";

  const [tab, setTab] = useState<Tab>("queries");
  const [search, setSearch] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [shipmentFilter, setShipmentFilter] = useState("");
  const [queries, setQueries] = useState<any[]>([]);
  const [agentRuns, setAgentRuns] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authHeaders = () => {
    const token = localStorage.getItem("glih_access_token");
    return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = authHeaders();
      const [qRes, aRes, nRes] = await Promise.all([
        fetch(`${BASE}/history/queries?limit=100`, { headers }),
        fetch(`${BASE}/history/agents?limit=100${agentFilter ? `&agent_name=${agentFilter}` : ""}`, { headers }),
        fetch(`${BASE}/history/notifications?limit=100${shipmentFilter ? `&shipment_id=${shipmentFilter}` : ""}`, { headers }),
      ]);
      const [qData, aData, nData] = await Promise.all([qRes.json(), aRes.json(), nRes.json()]);
      setQueries(qData.queries || []);
      setAgentRuns(aData.agent_runs || []);
      setNotifications(nData.notifications || []);

      if (isAdmin) {
        const sRes = await fetch(`${BASE}/history/stats`, { headers });
        if (sRes.ok) setStats(await sRes.json());
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [agentFilter, shipmentFilter, isAdmin]);

  useEffect(() => { loadAll(); }, [loadAll]);

  // Client-side search filter
  const filteredQueries = queries.filter(r =>
    !search || r.query?.toLowerCase().includes(search.toLowerCase()) ||
    r.answer?.toLowerCase().includes(search.toLowerCase()) ||
    r.user_email?.toLowerCase().includes(search.toLowerCase())
  );
  const filteredAgents = agentRuns.filter(r =>
    !search || r.agent_name?.toLowerCase().includes(search.toLowerCase()) ||
    r.user_email?.toLowerCase().includes(search.toLowerCase()) ||
    r.run_id?.includes(search)
  );
  const filteredNotifs = notifications.filter(r =>
    !search || r.shipment_id?.toLowerCase().includes(search.toLowerCase()) ||
    r.customer_id?.toLowerCase().includes(search.toLowerCase()) ||
    r.notification_type?.toLowerCase().includes(search.toLowerCase())
  );

  const tabs: { id: Tab; label: string; icon: React.ReactNode; count: number }[] = [
    { id: "queries",       label: "Queries",       icon: <MessageSquare size={14} />, count: filteredQueries.length },
    { id: "agents",        label: "Agent Runs",    icon: <Bot size={14} />,           count: filteredAgents.length },
    { id: "notifications", label: "Notifications", icon: <Bell size={14} />,          count: filteredNotifs.length },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--bg-primary)" }}>
      <Header
        title={isAdmin ? "History — All Dispatchers" : "My History"}
        subtitle={isAdmin ? "Full audit trail across all users" : "Your queries, agent runs, and notifications"}
      />

      <div style={{ flex: 1, overflow: "auto", padding: "20px 24px" }}>

        {/* Stats cards — admin only */}
        {isAdmin && stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Total Queries",       value: stats.total_queries,       color: "var(--teal)",   icon: <MessageSquare size={16} /> },
              { label: "Agent Runs",          value: stats.total_agent_runs,    color: "#a78bfa",       icon: <Bot size={16} /> },
              { label: "Notifications Sent",  value: stats.total_notifications, color: "#f59e0b",       icon: <Bell size={16} /> },
              { label: "Anomaly Runs",        value: stats.agent_breakdown?.AnomalyResponder || 0, color: "#ef4444", icon: <AlertCircle size={16} /> },
            ].map(s => (
              <div key={s.label} className="card" style={{ padding: "14px 18px", display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ color: s.color, opacity: 0.8 }}>{s.icon}</div>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Controls bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          {/* Search */}
          <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
            <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={tab === "queries" ? "Search queries or answers…" : tab === "agents" ? "Search agent name or run ID…" : "Search shipment or customer…"}
              style={{ width: "100%", paddingLeft: 32, paddingRight: search ? 32 : 12, paddingTop: 8, paddingBottom: 8, background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-primary)", fontSize: 13, outline: "none" }}
            />
            {search && (
              <button onClick={() => setSearch("")} style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 2 }}>
                <X size={13} />
              </button>
            )}
          </div>

          {/* Agent filter (agents tab) */}
          {tab === "agents" && (
            <select
              value={agentFilter}
              onChange={e => setAgentFilter(e.target.value)}
              style={{ padding: "8px 12px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-primary)", fontSize: 13, cursor: "pointer" }}
            >
              <option value="">All Agents</option>
              <option value="AnomalyResponder">Anomaly Responder</option>
              <option value="RouteAdvisor">Route Advisor</option>
              <option value="CustomerNotifier">Customer Notifier</option>
              <option value="OpsSummarizer">Ops Summarizer</option>
            </select>
          )}

          {/* Shipment filter (notifications tab) */}
          {tab === "notifications" && (
            <div style={{ position: "relative" }}>
              <Filter size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                value={shipmentFilter}
                onChange={e => setShipmentFilter(e.target.value)}
                placeholder="Filter by shipment ID…"
                style={{ paddingLeft: 28, paddingRight: 10, paddingTop: 8, paddingBottom: 8, background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-primary)", fontSize: 13, outline: "none" }}
              />
            </div>
          )}

          {/* Refresh */}
          <button
            onClick={loadAll}
            disabled={loading}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 14px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-secondary)", fontSize: 13, cursor: "pointer" }}
          >
            <RefreshCw size={13} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 16, borderBottom: "1px solid var(--border)" }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "8px 16px", background: "none", border: "none",
                borderBottom: tab === t.id ? "2px solid var(--teal)" : "2px solid transparent",
                color: tab === t.id ? "var(--teal)" : "var(--text-muted)",
                fontWeight: tab === t.id ? 600 : 400, fontSize: 13, cursor: "pointer",
                marginBottom: -1, transition: "color 0.15s",
              }}
            >
              {t.icon}{t.label}
              <span style={{ fontSize: 11, background: tab === t.id ? "rgba(34,211,238,0.15)" : "rgba(148,163,184,0.1)", color: tab === t.id ? "var(--teal)" : "var(--text-dim)", padding: "1px 6px", borderRadius: 10, marginLeft: 2 }}>
                {t.count}
              </span>
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div style={{ padding: "12px 16px", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, color: "#ef4444", fontSize: 13, marginBottom: 16 }}>
            {error}
          </div>
        )}

        {/* Table */}
        <div className="card" style={{ overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>

            {/* ── QUERIES TABLE ── */}
            {tab === "queries" && (
              <>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", background: "rgba(15,31,61,0.6)" }}>
                    <th style={{ width: 28, padding: "10px 16px" }} />
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Query</th>
                    {isAdmin && <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Dispatcher</th>}
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Collection</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Model</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Duration</th>
                    <th style={{ padding: "10px 16px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQueries.length === 0 ? (
                    <tr><td colSpan={isAdmin ? 7 : 6} style={{ padding: 40, textAlign: "center", color: "var(--text-dim)", fontSize: 13 }}>
                      {loading ? "Loading…" : "No queries found"}
                    </td></tr>
                  ) : filteredQueries.map(r => <QueryRow key={r.id} rec={r} isAdmin={isAdmin} />)}
                </tbody>
              </>
            )}

            {/* ── AGENT RUNS TABLE ── */}
            {tab === "agents" && (
              <>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", background: "rgba(15,31,61,0.6)" }}>
                    <th style={{ width: 28, padding: "10px 16px" }} />
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Agent</th>
                    {isAdmin && <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Dispatcher</th>}
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Run ID</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Status</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Duration</th>
                    <th style={{ padding: "10px 16px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAgents.length === 0 ? (
                    <tr><td colSpan={isAdmin ? 7 : 6} style={{ padding: 40, textAlign: "center", color: "var(--text-dim)", fontSize: 13 }}>
                      {loading ? "Loading…" : "No agent runs found"}
                    </td></tr>
                  ) : filteredAgents.map(r => <AgentRunRow key={r.run_id} rec={r} isAdmin={isAdmin} />)}
                </tbody>
              </>
            )}

            {/* ── NOTIFICATIONS TABLE ── */}
            {tab === "notifications" && (
              <>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", background: "rgba(15,31,61,0.6)" }}>
                    <th style={{ width: 28, padding: "10px 16px" }} />
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Shipment</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Customer</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Type</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Severity</th>
                    {isAdmin && <th style={{ padding: "10px 8px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Dispatcher</th>}
                    <th style={{ padding: "10px 16px", textAlign: "left", fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredNotifs.length === 0 ? (
                    <tr><td colSpan={isAdmin ? 7 : 6} style={{ padding: 40, textAlign: "center", color: "var(--text-dim)", fontSize: 13 }}>
                      {loading ? "Loading…" : "No notifications found"}
                    </td></tr>
                  ) : filteredNotifs.map(r => <NotifRow key={r.id} rec={r} isAdmin={isAdmin} />)}
                </tbody>
              </>
            )}

          </table>
        </div>

      </div>

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
