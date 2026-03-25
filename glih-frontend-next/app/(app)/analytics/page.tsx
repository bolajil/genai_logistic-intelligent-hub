"use client";
import Header from "@/components/Header";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const complianceData = [
  { day: "Mon", compliance: 98.2, breaches: 3 },
  { day: "Tue", compliance: 99.1, breaches: 1 },
  { day: "Wed", compliance: 97.8, breaches: 5 },
  { day: "Thu", compliance: 99.4, breaches: 1 },
  { day: "Fri", compliance: 98.9, breaches: 2 },
  { day: "Sat", compliance: 99.6, breaches: 0 },
  { day: "Sun", compliance: 99.1, breaches: 1 },
];

const onTimeData = [
  { day: "Mon", onTime: 92.1 },
  { day: "Tue", onTime: 94.8 },
  { day: "Wed", onTime: 91.3 },
  { day: "Thu", onTime: 95.2 },
  { day: "Fri", onTime: 93.7 },
  { day: "Sat", onTime: 96.1 },
  { day: "Sun", onTime: 94.2 },
];

const agentRunData = [
  { agent: "AnomalyResponder", runs: 42, avgMs: 2840 },
  { agent: "RouteAdvisor",     runs: 28, avgMs: 3120 },
  { agent: "CustomerNotifier", runs: 19, avgMs: 1950 },
  { agent: "OpsSummarizer",    runs: 14, avgMs: 4200 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 12px", fontSize: "0.72rem" }}>
        <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>{label}</div>
        {payload.map((p: any) => (
          <div key={p.name} style={{ color: p.color }}>{p.name}: {p.value}{p.name.includes("compliance") || p.name.includes("onTime") ? "%" : ""}</div>
        ))}
      </div>
    );
  }
  return null;
};

export default function AnalyticsPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Analytics" subtitle="7-day performance overview" />
      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        {/* KPI summary row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 12, marginBottom: 20 }}>
          {[
            { label: "Avg Compliance", value: "98.9%",  color: "var(--green)" },
            { label: "Avg On-Time",    value: "93.9%",  color: "var(--purple)" },
            { label: "Total Breaches", value: "13",     color: "var(--red)" },
            { label: "Waste Prevented", value: "$2.1M", color: "var(--teal)" },
            { label: "Agent Runs",     value: "103",    color: "var(--amber)" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card" style={{ padding: "14px 16px", textAlign: "center" }}>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color }}>{value}</div>
              <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginTop: 4, letterSpacing: "0.06em" }}>{label.toUpperCase()}</div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>

          {/* Compliance chart */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, marginBottom: 14, letterSpacing: "0.06em" }}>TEMPERATURE COMPLIANCE %</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={complianceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                <XAxis dataKey="day" stroke="#475569" fontSize={11} />
                <YAxis domain={[96, 100]} stroke="#475569" fontSize={11} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="compliance" stroke="#10b981" strokeWidth={2} dot={{ fill: "#10b981", r: 3 }} name="compliance" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* On-time chart */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, marginBottom: 14, letterSpacing: "0.06em" }}>ON-TIME DELIVERY %</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={onTimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                <XAxis dataKey="day" stroke="#475569" fontSize={11} />
                <YAxis domain={[88, 98]} stroke="#475569" fontSize={11} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="onTime" stroke="#a78bfa" strokeWidth={2} dot={{ fill: "#a78bfa", r: 3 }} name="onTime" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

          {/* Breaches bar */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, marginBottom: 14, letterSpacing: "0.06em" }}>DAILY TEMPERATURE BREACHES</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={complianceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                <XAxis dataKey="day" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="breaches" fill="#ef4444" radius={[4,4,0,0]} name="breaches" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Agent runs table */}
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontSize: "0.7rem", fontWeight: 700, letterSpacing: "0.06em" }}>AGENT RUN HISTORY</span>
              <button className="btn-ghost" style={{ fontSize: "0.65rem" }}>Export CSV</button>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.72rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Agent", "Runs (7d)", "Avg Latency"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "4px 8px", color: "var(--text-muted)", fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.05em" }}>{h.toUpperCase()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {agentRunData.map(a => (
                  <tr key={a.agent} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 8px", color: "var(--teal)", fontWeight: 600 }}>{a.agent}</td>
                    <td style={{ padding: "10px 8px", color: "var(--text-primary)" }}>{a.runs}</td>
                    <td style={{ padding: "10px 8px", color: a.avgMs > 4000 ? "var(--amber)" : "var(--green)" }}>{a.avgMs}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
