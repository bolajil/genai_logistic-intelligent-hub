"use client";
import { useState, useEffect } from "react";
import Header from "@/components/Header";

const BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9001";

type Tab = "connectors" | "api-keys" | "llm" | "advanced";

interface MCPConnector {
  id: string;
  name: string;
  enabled: boolean;
  configured: boolean;
  mode: "demo" | "real";
  description: string;
  endpoint: string;
}

interface ConnectorFields {
  [key: string]: { label: string; field: string; type: "text" | "password"; placeholder: string }[];
}

const CONNECTOR_FIELDS: ConnectorFields = {
  gps_trace: [
    { label: "API Token", field: "api_token", type: "password", placeholder: "Get from gps-trace.com or ruhavik.com" },
  ],
  openweathermap: [
    { label: "API Key", field: "api_key", type: "password", placeholder: "Get from openweathermap.org/api" },
  ],
  iot: [
    { label: "Mode", field: "mode", type: "text", placeholder: "demo | mqtt | api" },
    { label: "MQTT Broker", field: "mqtt_broker", type: "text", placeholder: "e.g., mqtt.lineage.local" },
    { label: "MQTT Port", field: "mqtt_port", type: "text", placeholder: "1883" },
    { label: "MQTT Username", field: "mqtt_username", type: "text", placeholder: "Optional" },
    { label: "MQTT Password", field: "mqtt_password", type: "password", placeholder: "Optional" },
    { label: "API Endpoint", field: "api_endpoint", type: "text", placeholder: "e.g., http://iot-gateway:8080" },
    { label: "API Key", field: "api_key", type: "password", placeholder: "Optional API key for gateway" },
  ],
  traffic: [
    { label: "Provider", field: "provider", type: "text", placeholder: "google | here | mapbox" },
    { label: "API Key", field: "api_key", type: "password", placeholder: "API key for selected provider" },
  ],
};

// Default connectors for fallback when backend unavailable
const DEFAULT_CONNECTORS: MCPConnector[] = [
  { id: "gps_trace", name: "GPS-Trace (Truck Tracking)", enabled: true, configured: false, mode: "demo", description: "Real-time truck tracking, mileage, engine hours, geofences", endpoint: "https://mcp.gps-trace.com/mcp" },
  { id: "openweathermap", name: "OpenWeatherMap (Weather)", enabled: true, configured: false, mode: "demo", description: "Weather forecasts for route planning and spoilage risk", endpoint: "" },
  { id: "iot", name: "Lineage IoT Sensors", enabled: true, configured: false, mode: "demo", description: "Temperature sensors, door status, humidity monitoring", endpoint: "" },
  { id: "traffic", name: "Traffic & Routing", enabled: false, configured: false, mode: "demo", description: "Real-time traffic for ETA optimization", endpoint: "" },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("connectors");
  const [connectors, setConnectors] = useState<MCPConnector[]>(DEFAULT_CONNECTORS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { status: string; message: string }>>({});
  const [formData, setFormData] = useState<Record<string, Record<string, string>>>({});
  const [llm, setLlm] = useState("openai/gpt-4o");
  const [saved, setSaved] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Fetch MCP settings on mount
  useEffect(() => {
    fetchMCPSettings();
  }, []);

  async function fetchMCPSettings() {
    try {
      const res = await fetch(`${BASE}/settings/mcp`);
      if (res.ok) {
        const data = await res.json();
        if (data.connectors && data.connectors.length > 0) {
          setConnectors(data.connectors);
        }
        // Initialize form data for each connector
        const initialForm: Record<string, Record<string, string>> = {};
        (data.connectors || DEFAULT_CONNECTORS).forEach((c: MCPConnector) => {
          initialForm[c.id] = {};
        });
        setFormData(initialForm);
        setFetchError(null);
      } else {
        setFetchError(`Backend returned ${res.status}`);
      }
    } catch (e) {
      console.error("Failed to fetch MCP settings:", e);
      setFetchError(String(e));
      // Initialize form data with defaults
      const initialForm: Record<string, Record<string, string>> = {};
      DEFAULT_CONNECTORS.forEach((c) => {
        initialForm[c.id] = {};
      });
      setFormData(initialForm);
    } finally {
      setLoading(false);
    }
  }

  async function saveConnector(connectorId: string) {
    setSaving(connectorId);
    try {
      const fields = formData[connectorId] || {};
      const res = await fetch(`${BASE}/settings/mcp/connector/${connectorId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: true, ...fields }),
      });
      if (res.ok) {
        await fetchMCPSettings();
        setFormData(prev => ({ ...prev, [connectorId]: {} }));
      }
    } catch (e) {
      console.error("Failed to save connector:", e);
    } finally {
      setSaving(null);
    }
  }

  async function testConnector(connectorId: string) {
    setTesting(connectorId);
    try {
      const res = await fetch(`${BASE}/settings/mcp/test/${connectorId}`, { method: "POST" });
      if (res.ok) {
        const result = await res.json();
        setTestResults(prev => ({ ...prev, [connectorId]: result }));
      }
    } catch (e) {
      setTestResults(prev => ({ ...prev, [connectorId]: { status: "error", message: String(e) } }));
    } finally {
      setTesting(null);
    }
  }

  function updateField(connectorId: string, field: string, value: string) {
    setFormData(prev => ({
      ...prev,
      [connectorId]: { ...prev[connectorId], [field]: value },
    }));
  }

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "connectors", label: "Connection Mode", icon: "🔌" },
    { id: "api-keys", label: "API Keys & IoT", icon: "🔑" },
    { id: "llm", label: "LLM Provider", icon: "🤖" },
    { id: "advanced", label: "Advanced", icon: "⚙️" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Settings" subtitle="Connector configuration, API keys, and system preferences" />
      
      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: 4, padding: "0 20px", borderBottom: "1px solid var(--border)" }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: "12px 16px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: "transparent",
              border: "none",
              borderBottom: tab === t.id ? "2px solid var(--teal)" : "2px solid transparent",
              color: tab === t.id ? "var(--teal)" : "var(--text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>Loading settings...</div>
        ) : (
          <>
            {/* Error banner */}
            {fetchError && (
              <div style={{ marginBottom: 16, padding: 12, background: "var(--yellow)" + "15", border: "1px solid var(--yellow)", borderRadius: 8 }}>
                <div style={{ fontSize: "0.75rem", color: "var(--yellow)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>⚠️ Using offline mode - backend connection failed. Settings will be saved locally.</span>
                  <button onClick={fetchMCPSettings} style={{ padding: "4px 12px", fontSize: "0.7rem", background: "var(--yellow)", color: "#000", border: "none", borderRadius: 4, cursor: "pointer" }}>Retry</button>
                </div>
              </div>
            )}

            {/* TAB: Connection Mode */}
            {tab === "connectors" && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, marginBottom: 4 }}>MCP Connector Status</div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: 18 }}>
                  Each connector can run in <b>DEMO</b> mode (simulated data) or <b>REAL</b> mode (live API connection).
                  Configure API keys in the "API Keys & IoT" tab to enable real mode.
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {connectors.map(c => (
                    <div key={c.id} style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      padding: "14px 16px", background: "var(--bg-secondary)", borderRadius: 8,
                      border: `1px solid ${c.configured ? "var(--teal)" : "var(--border)"}`,
                    }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 2 }}>
                          {c.name}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{c.description}</div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                        <span style={{
                          fontSize: "0.7rem", fontWeight: 700, padding: "4px 10px", borderRadius: 4,
                          background: c.configured ? "var(--teal)" + "20" : "var(--yellow)" + "20",
                          color: c.configured ? "var(--teal)" : "var(--yellow)",
                        }}>
                          {c.configured ? "✓ REAL" : "DEMO"}
                        </span>
                        <button
                          onClick={() => testConnector(c.id)}
                          disabled={testing === c.id}
                          style={{
                            padding: "6px 12px", fontSize: "0.7rem", borderRadius: 4,
                            background: "var(--bg-primary)", border: "1px solid var(--border)",
                            cursor: "pointer", color: "var(--text-secondary)",
                          }}
                        >
                          {testing === c.id ? "Testing..." : "Test"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                {Object.keys(testResults).length > 0 && (
                  <div style={{ marginTop: 16, padding: 12, background: "var(--bg-secondary)", borderRadius: 6 }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 700, marginBottom: 8 }}>Test Results</div>
                    {Object.entries(testResults).map(([id, result]) => (
                      <div key={id} style={{ fontSize: "0.72rem", marginBottom: 4, display: "flex", gap: 8 }}>
                        <span style={{ fontWeight: 600 }}>{id}:</span>
                        <span style={{
                          color: result.status === "connected" ? "var(--green)" :
                                 result.status === "demo" ? "var(--yellow)" : "var(--red)"
                        }}>
                          {result.status} - {result.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB: API Keys & IoT Configuration */}
            {tab === "api-keys" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {connectors.map(c => (
                  <div key={c.id} className="card" style={{ padding: 20 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <div>
                        <div style={{ fontSize: "0.85rem", fontWeight: 700 }}>{c.name}</div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{c.description}</div>
                      </div>
                      <span style={{
                        fontSize: "0.68rem", fontWeight: 700, padding: "4px 10px", borderRadius: 4,
                        background: c.configured ? "var(--green)" + "20" : "var(--border)",
                        color: c.configured ? "var(--green)" : "var(--text-muted)",
                      }}>
                        {c.configured ? "✓ Configured" : "Not Configured"}
                      </span>
                    </div>

                    {CONNECTOR_FIELDS[c.id] && (
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                        {CONNECTOR_FIELDS[c.id].map(field => (
                          <div key={field.field}>
                            <label style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
                              {field.label}
                            </label>
                            <input
                              type={field.type}
                              placeholder={field.placeholder}
                              value={formData[c.id]?.[field.field] || ""}
                              onChange={e => updateField(c.id, field.field, e.target.value)}
                              style={{
                                width: "100%", padding: "10px 12px", fontSize: "0.78rem",
                                background: "var(--bg-primary)", border: "1px solid var(--border)",
                                borderRadius: 6, color: "var(--text-primary)",
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    )}

                    <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                      <button
                        onClick={() => saveConnector(c.id)}
                        disabled={saving === c.id}
                        className="btn-primary"
                        style={{ fontSize: "0.75rem", padding: "8px 16px" }}
                      >
                        {saving === c.id ? "Saving..." : "Save Configuration"}
                      </button>
                      <button
                        onClick={() => testConnector(c.id)}
                        disabled={testing === c.id}
                        className="btn-ghost"
                        style={{ fontSize: "0.75rem", padding: "8px 16px" }}
                      >
                        {testing === c.id ? "Testing..." : "Test Connection"}
                      </button>
                    </div>

                    {testResults[c.id] && (
                      <div style={{
                        marginTop: 12, padding: 10, borderRadius: 6, fontSize: "0.72rem",
                        background: testResults[c.id].status === "connected" ? "var(--green)" + "15" :
                                   testResults[c.id].status === "demo" ? "var(--yellow)" + "15" : "var(--red)" + "15",
                        color: testResults[c.id].status === "connected" ? "var(--green)" :
                               testResults[c.id].status === "demo" ? "var(--yellow)" : "var(--red)",
                      }}>
                        <b>{testResults[c.id].status.toUpperCase()}</b>: {testResults[c.id].message}
                      </div>
                    )}
                  </div>
                ))}

                {/* Help section */}
                <div className="card" style={{ padding: 20, background: "var(--bg-secondary)" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, marginBottom: 8 }}>📖 How to Get API Keys</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    <p style={{ marginBottom: 8 }}><b>GPS-Trace:</b> Sign up at <a href="https://gps-trace.com" target="_blank" style={{ color: "var(--teal)" }}>gps-trace.com</a> or <a href="https://ruhavik.com" target="_blank" style={{ color: "var(--teal)" }}>ruhavik.com</a>, then get your MCP token from account settings.</p>
                    <p style={{ marginBottom: 8 }}><b>OpenWeatherMap:</b> Register at <a href="https://openweathermap.org/api" target="_blank" style={{ color: "var(--teal)" }}>openweathermap.org/api</a> (free tier: 1000 calls/day).</p>
                    <p style={{ marginBottom: 8 }}><b>IoT Sensors:</b> Configure your MQTT broker (e.g., Mosquitto) or HTTP API gateway for temperature/door sensors.</p>
                    <p><b>Traffic:</b> Get API key from Google Maps Platform, HERE Developer, or Mapbox.</p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: LLM Provider */}
            {tab === "llm" && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, marginBottom: 16 }}>LLM Provider</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-sonnet-4-6", "mistral/mistral-large"].map(m => (
                    <div key={m} onClick={() => setLlm(m)} style={{
                      display: "flex", alignItems: "center", gap: 10, padding: "12px 16px",
                      borderRadius: 6, cursor: "pointer",
                      background: llm === m ? "var(--teal)" + "18" : "var(--bg-secondary)",
                      border: `1px solid ${llm === m ? "var(--teal)" : "var(--border)"}`,
                    }}>
                      <div style={{
                        width: 16, height: 16, borderRadius: "50%",
                        border: `2px solid ${llm === m ? "var(--teal)" : "var(--border)"}`,
                        background: llm === m ? "var(--teal)" : "transparent",
                        flexShrink: 0,
                      }} />
                      <span style={{ fontSize: "0.82rem", color: llm === m ? "var(--teal)" : "var(--text-secondary)", fontFamily: "monospace" }}>{m}</span>
                    </div>
                  ))}
                </div>
                <button className="btn-primary" onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 2000); }} style={{ marginTop: 16 }}>
                  {saved ? "✓ Saved" : "Save LLM Selection"}
                </button>
              </div>
            )}

            {/* TAB: Advanced */}
            {tab === "advanced" && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, marginBottom: 16 }}>Advanced Settings</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{ padding: 14, background: "var(--bg-secondary)", borderRadius: 8 }}>
                    <div style={{ fontSize: "0.78rem", fontWeight: 600, marginBottom: 4 }}>MCP Timeout</div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 8 }}>Maximum time to wait for MCP server responses</div>
                    <input type="number" defaultValue={30} style={{
                      padding: "8px 12px", fontSize: "0.78rem", width: 100,
                      background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: 4,
                    }} /> <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>seconds</span>
                  </div>
                  <div style={{ padding: 14, background: "var(--bg-secondary)", borderRadius: 8 }}>
                    <div style={{ fontSize: "0.78rem", fontWeight: 600, marginBottom: 4 }}>Cache TTL</div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 8 }}>How long to cache MCP responses</div>
                    <input type="number" defaultValue={300} style={{
                      padding: "8px 12px", fontSize: "0.78rem", width: 100,
                      background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: 4,
                    }} /> <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>seconds</span>
                  </div>
                  <div style={{ padding: 14, background: "var(--bg-secondary)", borderRadius: 8 }}>
                    <div style={{ fontSize: "0.78rem", fontWeight: 600, marginBottom: 4 }}>Retry Attempts</div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 8 }}>Number of retry attempts for failed API calls</div>
                    <input type="number" defaultValue={3} style={{
                      padding: "8px 12px", fontSize: "0.78rem", width: 100,
                      background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: 4,
                    }} />
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
                  <button className="btn-primary">Save Advanced Settings</button>
                  <button className="btn-ghost">Reset to Defaults</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
