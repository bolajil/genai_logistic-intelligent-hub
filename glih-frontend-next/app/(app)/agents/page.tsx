"use client";
import { useState, useEffect, useRef } from "react";
import Header from "@/components/Header";
import { usePermissions } from "@/hooks/usePermissions";

const BASE = "http://localhost:9001";

interface Dispatcher {
  id: string;
  name: string;
  title: string;
  email: string;
  facility: string;
  active: boolean;
}

const AGENTS = [
  { id: "anomaly",     name: "AnomalyResponder",  desc: "Detect and respond to cold chain temperature breaches",       color: "#ef4444", endpoint: "/agents/anomaly" },
  { id: "route",       name: "RouteAdvisor",       desc: "Optimise routes based on spoilage risk and live conditions",  color: "#a78bfa", endpoint: "/agents/route" },
  { id: "notify",      name: "CustomerNotifier",   desc: "Draft and send customer alerts for shipment events",          color: "#22d3ee", endpoint: "/agents/notify" },
  { id: "ops-summary", name: "OpsSummarizer",      desc: "Generate shift handoff and operations summary reports",       color: "#f59e0b", endpoint: "/agents/ops-summary" },
];

const PRESETS: Record<string, { label: string; payload: Record<string, any> }[]> = {
  anomaly: [
    { label: "🌡 Dairy Breach — CHI-ATL",  payload: { shipment_id: "CHI-ATL-2025-089", temperature_c: 5.2, product_type: "Dairy",   threshold_max_c: 4.0, location: "Atlanta Cold Hub, GA", breach_duration_min: 22 } },
    { label: "🐟 Seafood Watch — TX-CHI",   payload: { shipment_id: "TX-CHI-2025-001",  temperature_c: 1.8, product_type: "Seafood", threshold_max_c: 2.0, location: "Chicago Hub, IL",       breach_duration_min: 8  } },
  ],
  route: [
    { label: "🐟 Seafood High Risk",  payload: { shipment_id: "TX-CHI-2025-001", origin: "Dallas, TX",  destination: "Chicago, IL", product_type: "Seafood" } },
    { label: "🥩 Meat — Long Haul",  payload: { shipment_id: "CHI-LA-2025-445", origin: "Chicago, IL", destination: "Los Angeles, CA", product_type: "Meat" } },
  ],
  notify: [
    { label: "📧 Breach → Whole Foods",    payload: { shipment_id: "CHI-ATL-2025-089", customer_id: "CUST-001", notification_type: "temperature_breach", severity: "high", dispatcher_name: "John Martinez", dispatcher_title: "Cold Chain Operations Dispatcher" } },
    { label: "📧 Delay → Sysco",           payload: { shipment_id: "TX-CHI-2025-001",  customer_id: "CUST-002", notification_type: "delay",              severity: "medium", dispatcher_name: "John Martinez", dispatcher_title: "Cold Chain Operations Dispatcher" } },
  ],
  "ops-summary": [
    { label: "📋 24h Chicago Report", payload: { time_window: "24h", facility: "Chicago" } },
    { label: "📋 8h Shift Report",    payload: { time_window: "8h",  facility: "all" } },
  ],
};

function renderResult(result: any) {
  if (!result) return null;
  const r = result.result || result;

  // AnomalyResponder
  if (r.actions || r.anomaly) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {r.anomaly && (
          <div style={{ background: "#1a0505", border: "1px solid #7f1d1d", borderRadius: 6, padding: 12 }}>
            <div style={{ color: "#f87171", fontWeight: 700, marginBottom: 6 }}>⚠ {r.anomaly.type?.toUpperCase()} — {r.anomaly.severity?.toUpperCase()}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Temp: {r.anomaly.details?.current_temp}°C · Range: {r.anomaly.details?.expected_range?.join(" to ")}°C · Deviation: {r.anomaly.details?.deviation?.toFixed(1)}°C
            </div>
          </div>
        )}
        {r.actions?.length > 0 && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>ACTION PLAN</div>
            {r.actions.map((a: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                <span style={{ background: "var(--teal)", color: "#020d1a", borderRadius: "50%", width: 18, height: 18, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.6rem", fontWeight: 800, flexShrink: 0, marginTop: 1 }}>{i + 1}</span>
                <div>
                  <span style={{ fontSize: "0.8rem", color: "var(--teal)", fontWeight: 700 }}>{a.action}</span>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}> — {a.description}</span>
                  <span style={{ fontSize: "0.75rem", color: a.priority === "urgent" ? "#f87171" : a.priority === "high" ? "#fdba74" : "var(--text-dim)", marginLeft: 8 }}>[{a.priority}]</span>
                </div>
              </div>
            ))}
          </div>
        )}
        {r.recommendation && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 6 }}>LLM RECOMMENDATION</div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6 }}>{r.recommendation}</div>
          </div>
        )}
      </div>
    );
  }

  // RouteAdvisor
  if (r.recommended_route || r.alternatives || r.spoilage_risk !== undefined) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {r.spoilage_risk !== undefined && (
          <div style={{ background: r.spoilage_risk > 0.6 ? "#1a0505" : "#052e16", border: `1px solid ${r.spoilage_risk > 0.6 ? "#7f1d1d" : "#14532d"}`, borderRadius: 6, padding: 12 }}>
            <span style={{ color: r.spoilage_risk > 0.6 ? "#f87171" : "#4ade80", fontWeight: 700 }}>
              Spoilage Risk: {(r.spoilage_risk * 100).toFixed(0)}%
            </span>
          </div>
        )}
        {r.recommendation && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 6 }}>ROUTE RECOMMENDATION</div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6 }}>{r.recommendation}</div>
          </div>
        )}
        {r.alternatives?.length > 0 && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>ALTERNATIVE ROUTES</div>
            {r.alternatives.map((alt: any, i: number) => (
              <div key={i} className="card" style={{ padding: 10, marginBottom: 6 }}>
                <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-primary)" }}>{alt.name || `Route ${i + 1}`}</div>
                <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                  {alt.distance_km}km · {alt.duration_hours}h · Cost: ${alt.cost_usd} · Risk: {(alt.spoilage_risk * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // CustomerNotifier — show email/notification details
  // Check for customer_name, customer_id, or status with reason (for skipped notifications)
  if (r.customer_name || r.customer_id || (r.status && r.reason) || (r.notification_type && r.shipment_id)) {
    // Handle skipped notifications
    if (r.status === "skipped") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ background: "#1a1a05", border: "1px solid #7f7f1d", borderRadius: 6, padding: 12 }}>
            <span style={{ color: "#fbbf24", fontWeight: 700 }}>⏭ NOTIFICATION SKIPPED</span>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: 6 }}>
              Reason: {r.reason === "customer_preference" ? "Customer prefers critical notifications only" : r.reason}
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 4 }}>
              Customer ID: {r.customer_id}
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {/* Delivery Status Banner */}
        <div style={{ 
          background: r.delivery_status === "sent" ? "#052e16" : "#1a0505", 
          border: `1px solid ${r.delivery_status === "sent" ? "#14532d" : "#7f1d1d"}`, 
          borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center" 
        }}>
          <div>
            <span style={{ color: r.delivery_status === "sent" ? "#4ade80" : "#f87171", fontWeight: 700 }}>
              {r.delivery_status === "sent" ? "✓ NOTIFICATION SENT" : "⚠ " + (r.delivery_status || "PENDING").toUpperCase()}
            </span>
            <span style={{ color: "var(--text-muted)", marginLeft: 12, fontSize: "0.75rem" }}>
              via {r.channel?.toUpperCase() || "EMAIL"}
            </span>
          </div>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{r.timestamp}</span>
        </div>

        {/* Recipient Info */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="card" style={{ padding: 12 }}>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, marginBottom: 4 }}>RECIPIENT</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", fontWeight: 600 }}>{r.customer_name || "Customer"}</div>
            <div style={{ fontSize: "0.72rem", color: "var(--teal)" }}>{r.customer_id}</div>
          </div>
          <div className="card" style={{ padding: 12 }}>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, marginBottom: 4 }}>SHIPMENT</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", fontWeight: 600 }}>{r.shipment_id}</div>
            <div style={{ fontSize: "0.72rem", color: r.notification_type === "temperature_breach" ? "#f87171" : "#a78bfa" }}>
              {r.notification_type?.replace(/_/g, " ").toUpperCase()}
            </div>
          </div>
        </div>

        {/* Email/Message Content */}
        {r.message && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>
              📧 {r.channel === "email" ? "EMAIL CONTENT" : r.channel === "sms" ? "SMS MESSAGE" : "NOTIFICATION"}
            </div>
            <div style={{ 
              fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.7, 
              background: "var(--bg-secondary)", padding: 16, borderRadius: 6,
              border: "1px solid var(--border)", whiteSpace: "pre-wrap"
            }}>
              {r.message}
            </div>
          </div>
        )}

        {/* Message ID for tracking */}
        {r.message_id && (
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", display: "flex", gap: 8 }}>
            <span>Message ID:</span>
            <code style={{ color: "var(--teal)" }}>{r.message_id}</code>
          </div>
        )}
      </div>
    );
  }

  // OpsSummarizer — show shift details and attention items
  if (r.summary || r.metrics || r.incidents) {
    const summary = r.summary || {};
    const metrics = r.metrics || {};
    const incidents = r.incidents || {};
    
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Time Window & Generation Info */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          <span>📋 Report Period: <strong style={{ color: "var(--teal)" }}>{r.time_window || "24h"}</strong></span>
          <span>Generated: {r.generated_at ? new Date(r.generated_at).toLocaleString() : "Just now"}</span>
        </div>

        {/* KPI Metrics Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
          <div className="card" style={{ padding: 12, textAlign: "center" }}>
            <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--teal)" }}>{metrics.total_shipments || 0}</div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>SHIPMENTS</div>
          </div>
          <div className="card" style={{ padding: 12, textAlign: "center" }}>
            <div style={{ fontSize: "1.4rem", fontWeight: 800, color: metrics.on_time_pct >= 95 ? "#4ade80" : "#f87171" }}>
              {metrics.on_time_pct || 0}%
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>ON-TIME</div>
          </div>
          <div className="card" style={{ padding: 12, textAlign: "center" }}>
            <div style={{ fontSize: "1.4rem", fontWeight: 800, color: metrics.temp_compliance_pct >= 99 ? "#4ade80" : "#fdba74" }}>
              {metrics.temp_compliance_pct || 0}%
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>TEMP COMPLIANCE</div>
          </div>
          <div className="card" style={{ padding: 12, textAlign: "center" }}>
            <div style={{ fontSize: "1.4rem", fontWeight: 800, color: incidents.total > 0 ? "#f87171" : "#4ade80" }}>
              {incidents.total || 0}
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>INCIDENTS</div>
          </div>
        </div>

        {/* Executive Summary */}
        {summary.executive && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 6 }}>EXECUTIVE SUMMARY</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6 }}>
              {summary.executive}
            </div>
          </div>
        )}

        {/* Key Highlights */}
        {summary.highlights?.length > 0 && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>KEY HIGHLIGHTS</div>
            {summary.highlights.map((h: string, i: number) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                <span style={{ color: "#4ade80", fontSize: "0.75rem" }}>✓</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>{h}</span>
              </div>
            ))}
          </div>
        )}

        {/* Issues Requiring Attention */}
        {summary.issues?.length > 0 && (
          <div style={{ background: "#1a0505", border: "1px solid #7f1d1d", borderRadius: 6, padding: 12 }}>
            <div style={{ fontSize: "0.65rem", color: "#f87171", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>
              ⚠ ISSUES REQUIRING ATTENTION
            </div>
            {summary.issues.map((issue: string, i: number) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                <span style={{ color: "#f87171", fontSize: "0.75rem" }}>•</span>
                <span style={{ fontSize: "0.78rem", color: "#fca5a5" }}>{issue}</span>
              </div>
            ))}
          </div>
        )}

        {/* Incident Details */}
        {incidents.details?.length > 0 && (
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>INCIDENT DETAILS</div>
            {incidents.details.map((inc: any, i: number) => (
              <div key={i} className="card" style={{ padding: 10, marginBottom: 6, borderLeft: `3px solid ${inc.severity === "high" ? "#f87171" : "#fdba74"}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    {inc.type?.replace(/_/g, " ").toUpperCase()}
                  </span>
                  <span style={{ 
                    fontSize: "0.6rem", fontWeight: 700, padding: "2px 6px", borderRadius: 4,
                    background: inc.resolved ? "#052e16" : "#1a0505",
                    color: inc.resolved ? "#4ade80" : "#f87171"
                  }}>
                    {inc.resolved ? "RESOLVED" : "OPEN"}
                  </span>
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 4 }}>{inc.description}</div>
                {inc.resolution && (
                  <div style={{ fontSize: "0.68rem", color: "var(--teal)", marginTop: 4 }}>
                    Resolution: {inc.resolution}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Recommendations for Next Shift */}
        {summary.recommendations?.length > 0 && (
          <div style={{ background: "#0a1628", border: "1px solid #1e3a5f", borderRadius: 6, padding: 12 }}>
            <div style={{ fontSize: "0.65rem", color: "var(--teal)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>
              📋 RECOMMENDATIONS FOR NEXT SHIFT
            </div>
            {summary.recommendations.map((rec: string, i: number) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                <span style={{ background: "var(--teal)", color: "#020d1a", borderRadius: "50%", width: 16, height: 16, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.55rem", fontWeight: 800, flexShrink: 0 }}>{i + 1}</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>{rec}</span>
              </div>
            ))}
          </div>
        )}

        {/* Export Info */}
        {r.export && (
          <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "flex", gap: 12, alignItems: "center" }}>
            <span>📄 Report exported: <code style={{ color: "var(--teal)" }}>{r.export.filename}</code></span>
            <span>({r.export.size_kb} KB)</span>
          </div>
        )}
      </div>
    );
  }

  // Fallback — show raw JSON nicely
  return (
    <div>
      {r.message && <div style={{ fontSize: "0.73rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6, marginBottom: 10 }}>{r.message}</div>}
      <details style={{ marginTop: 10 }}>
        <summary style={{ fontSize: "0.65rem", color: "var(--text-muted)", cursor: "pointer" }}>View full JSON response</summary>
        <pre style={{ fontSize: "0.65rem", color: "var(--text-secondary)", background: "var(--bg-secondary)", padding: 12, borderRadius: 6, overflow: "auto", marginTop: 6 }}>
          {JSON.stringify(r, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export default function AgentsPage() {
  const { can } = usePermissions();
  const [selected, setSelected] = useState("anomaly");
  const [payload, setPayload] = useState(JSON.stringify(PRESETS["anomaly"][0].payload, null, 2));
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [dispatchers, setDispatchers] = useState<Dispatcher[]>([]);
  const [selectedDispatcher, setSelectedDispatcher] = useState<string>("");
  const [events, setEvents] = useState<{ step: string; message: string; ts: string }[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  const authHeaders = () => {
    const token = localStorage.getItem("glih_access_token");
    return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  // Load dispatchers on mount
  useEffect(() => {
    async function loadDispatchers() {
      try {
        const res = await fetch(`${BASE}/dispatchers`, { headers: authHeaders() });
        const data = await res.json();
        setDispatchers(data.dispatchers || []);
        if (data.dispatchers?.length > 0) {
          setSelectedDispatcher(data.dispatchers[0].id);
        }
      } catch (e) {
        console.error("Failed to load dispatchers:", e);
      }
    }
    loadDispatchers();
  }, []);

  const agent = AGENTS.find(a => a.id === selected)!;

  // Auto-scroll events log to bottom
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  // Cleanup poll on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function runAgent() {
    if (pollRef.current) clearInterval(pollRef.current);
    setRunning(true);
    setResult(null);
    setError(null);
    setEvents([]);
    const t0 = Date.now();
    try {
      let parsed = JSON.parse(payload);
      if (selected === "notify" && selectedDispatcher) {
        const disp = dispatchers.find(d => d.id === selectedDispatcher);
        if (disp) parsed = { ...parsed, dispatcher_name: disp.name, dispatcher_title: disp.title };
      }
      // Fire agent — returns immediately with run_id
      const res = await fetch(`${BASE}${agent.endpoint}`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(parsed),
      });
      const init = await res.json();
      if (!res.ok) throw new Error(init.detail || res.statusText);
      const runId = init.run_id;

      // Poll progress every 600ms
      pollRef.current = setInterval(async () => {
        try {
          const pr = await fetch(`${BASE}/agents/progress/${runId}`, { headers: authHeaders() });
          const progress = await pr.json();
          setEvents(progress.events || []);
          if (progress.status === "complete") {
            clearInterval(pollRef.current!);
            setElapsed(Date.now() - t0);
            setResult(progress.result);
            setRunning(false);
          } else if (progress.status === "error") {
            clearInterval(pollRef.current!);
            setError(progress.error || "Agent failed");
            setRunning(false);
          }
        } catch {
          // ignore transient poll errors
        }
      }, 600);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="AI Agents" subtitle="All agents wired to GPT-4o + ChromaDB RAG" />
      <div style={{ flex: 1, overflow: "auto", padding: 20, display: "grid", gridTemplateColumns: "280px 1fr", gap: 16 }}>

        {/* Agent selector */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 6 }}>SELECT AGENT</div>
          {AGENTS.map(a => (
            <div key={a.id} className="card card-hover" style={{
              padding: 14, cursor: "pointer",
              borderColor: selected === a.id ? a.color : "var(--border)",
              background: selected === a.id ? a.color + "18" : "var(--bg-card)",
            }} onClick={() => {
              setSelected(a.id);
              setPayload(JSON.stringify(PRESETS[a.id]?.[0]?.payload || {}, null, 2));
              setResult(null); setError(null); setEvents([]);
            }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 700, color: selected === a.id ? a.color : "var(--text-primary)", marginBottom: 4 }}>{a.name}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{a.desc}</div>
              {selected === a.id && (
                <div style={{ fontSize: "0.72rem", color: "var(--teal)", marginTop: 5, fontFamily: "monospace" }}>
                  POST {a.endpoint}
                </div>
              )}
            </div>
          ))}

          <div style={{ marginTop: 10, fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em" }}>DEMO PRESETS</div>
          {(PRESETS[selected] || []).map((p, i) => (
            <button key={i} className="btn-ghost" style={{ textAlign: "left" }}
              onClick={() => { setPayload(JSON.stringify(p.payload, null, 2)); setResult(null); setError(null); setEvents([]); }}>
              {p.label}
            </button>
          ))}
        </div>

        {/* Input + result */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em" }}>INPUT PAYLOAD</div>
              <div style={{ fontSize: "0.75rem", color: "var(--teal)" }}>● LIVE — GPT-4o</div>
            </div>
            <textarea
              value={payload}
              onChange={e => setPayload(e.target.value)}
              style={{
                width: "100%", height: 180,
                background: "var(--bg-secondary)", border: "1px solid var(--border)",
                borderRadius: 6, padding: 12,
                color: "var(--text-primary)", fontFamily: "monospace", fontSize: "0.85rem",
                resize: "vertical",
              }}
            />
            {/* Dispatcher selector for CustomerNotifier */}
            {selected === "notify" && dispatchers.length > 0 && (
              <div style={{ marginTop: 12, marginBottom: 12 }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600, display: "block", marginBottom: 6 }}>
                  SEND AS DISPATCHER
                </label>
                <select
                  value={selectedDispatcher}
                  onChange={(e) => setSelectedDispatcher(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: "0.85rem",
                  }}
                >
                  {dispatchers.filter(d => d.active).map(d => (
                    <option key={d.id} value={d.id}>
                      {d.name} — {d.title} ({d.facility})
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
              <button className="btn-primary" onClick={runAgent} disabled={running || !can("agents:run")}
                style={{ background: agent.color, minWidth: 160, opacity: can("agents:run") ? 1 : 0.45, cursor: can("agents:run") ? "pointer" : "not-allowed" }}
                title={can("agents:run") ? undefined : "Requires analyst role or higher"}>
                {running ? "⚡ Running..." : `⚡ Run ${agent.name}`}
              </button>
              <button className="btn-ghost" onClick={() => { setResult(null); setError(null); setEvents([]); }}>Clear</button>
              {result && <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{elapsed}ms</span>}
            </div>
          </div>

          {(running || events.length > 0) && (
            <div className="card" style={{ padding: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                {running && <span className="pulse-dot green" />}
                <span style={{ fontSize: "0.72rem", fontWeight: 700, color: running ? "var(--teal)" : "var(--text-muted)", letterSpacing: "0.08em" }}>
                  {running ? "AGENT EXECUTING" : "EXECUTION LOG"}
                </span>
              </div>
              <div style={{
                background: "var(--bg-secondary)", borderRadius: 6, padding: 12,
                maxHeight: 200, overflowY: "auto", fontFamily: "monospace",
                display: "flex", flexDirection: "column", gap: 6,
              }}>
                {events.map((ev, i) => {
                  const isError = ev.step === "error";
                  const isDone = ev.step === "complete";
                  const isLlm = ev.step === "llm_call" || ev.step === "llm_done";
                  const isSearch = ev.step === "retrieval" || ev.step === "retrieval_done";
                  const color = isError ? "#f87171" : isDone ? "#4ade80" : isLlm ? "#a78bfa" : isSearch ? "#f59e0b" : "var(--text-secondary)";
                  const prefix = isError ? "✗" : isDone ? "✓" : isLlm ? "◈" : isSearch ? "⊛" : "›";
                  return (
                    <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                      <span style={{ color, fontSize: "0.7rem", minWidth: 10, marginTop: 1 }}>{prefix}</span>
                      <div style={{ flex: 1 }}>
                        <span style={{ fontSize: "0.7rem", color }}>{ev.message}</span>
                        <span style={{ fontSize: "0.6rem", color: "var(--text-dim)", marginLeft: 8 }}>
                          {new Date(ev.ts).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  );
                })}
                {running && (
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ color: "var(--teal)", fontSize: "0.7rem" }}>›</span>
                    <span style={{ fontSize: "0.7rem", color: "var(--teal)" }}>waiting…</span>
                  </div>
                )}
                <div ref={eventsEndRef} />
              </div>
            </div>
          )}

          {error && (
            <div style={{ background: "#1a0505", border: "1px solid #7f1d1d", borderRadius: 8, padding: 16, color: "#f87171", fontSize: "0.75rem" }}>
              ✗ {error}
            </div>
          )}

          {result && !error && (
            <div className="card" style={{ padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ background: "#052e16", color: "#4ade80", border: "1px solid #14532d", borderRadius: 4, padding: "2px 8px", fontSize: "0.65rem", fontWeight: 700 }}>✓ SUCCESS</span>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700 }}>{result.agent_name}</span>
                </div>
                <span style={{ fontSize: "0.62rem", color: "var(--text-muted)" }}>{result.duration_ms}ms · run {result.run_id?.slice(0, 8)}</span>
              </div>
              {renderResult(result)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
