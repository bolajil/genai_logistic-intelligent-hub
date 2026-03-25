"use client";
import { useState } from "react";
import Header from "@/components/Header";

const BASE = "http://localhost:9001";

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
    { label: "📧 Breach → Whole Foods",    payload: { shipment_id: "CHI-ATL-2025-089", customer_id: "CUST-001", notification_type: "temperature_breach", severity: "high" } },
    { label: "📧 Delay → Sysco",           payload: { shipment_id: "TX-CHI-2025-001",  customer_id: "CUST-002", notification_type: "delay",              severity: "medium" } },
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

  // CustomerNotifier / OpsSummarizer — show raw JSON nicely
  return (
    <div>
      {r.message && <div style={{ fontSize: "0.73rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6, marginBottom: 10 }}>{r.message}</div>}
      {r.executive_summary && (
        <div>
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 6 }}>EXECUTIVE SUMMARY</div>
          <div style={{ fontSize: "0.73rem", color: "var(--text-secondary)", lineHeight: 1.6, background: "var(--bg-secondary)", padding: 12, borderRadius: 6 }}>{r.executive_summary}</div>
        </div>
      )}
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
  const [selected, setSelected] = useState("anomaly");
  const [payload, setPayload] = useState(JSON.stringify(PRESETS["anomaly"][0].payload, null, 2));
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const agent = AGENTS.find(a => a.id === selected)!;

  async function runAgent() {
    setRunning(true);
    setResult(null);
    setError(null);
    const t0 = Date.now();
    try {
      const parsed = JSON.parse(payload);
      const res = await fetch(`${BASE}${agent.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || res.statusText);
      setElapsed(Date.now() - t0);
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
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
              setResult(null); setError(null);
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
              onClick={() => { setPayload(JSON.stringify(p.payload, null, 2)); setResult(null); setError(null); }}>
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
            <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
              <button className="btn-primary" onClick={runAgent} disabled={running}
                style={{ background: agent.color, minWidth: 160 }}>
                {running ? "⚡ Running..." : `⚡ Run ${agent.name}`}
              </button>
              <button className="btn-ghost" onClick={() => { setResult(null); setError(null); }}>Clear</button>
              {result && <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{elapsed}ms</span>}
            </div>
          </div>

          {running && (
            <div className="card" style={{ padding: 24, textAlign: "center" }}>
              <div style={{ fontSize: "1.6rem", marginBottom: 8 }}>⚡</div>
              <div style={{ fontSize: "0.82rem", color: "var(--teal)" }}>{agent.name} running</div>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: 6 }}>
                Retrieving SOPs from ChromaDB → calling GPT-4o → generating action plan...
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
