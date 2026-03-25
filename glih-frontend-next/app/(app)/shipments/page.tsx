"use client";
import { useState } from "react";
import Header from "@/components/Header";

const SHIPMENTS = [
  { id: "CHI-ATL-2025-089", route: "Chicago → Atlanta",     product: "Dairy",        temp: 5.2,  status: "BREACH",     eta: "18:00 UTC", customer: "Whole Foods",    compliance: false },
  { id: "TX-CHI-2025-001",  route: "Dallas → Chicago",      product: "Seafood",      temp: 0.5,  status: "IN TRANSIT", eta: "14:00 UTC", customer: "Sysco",          compliance: true  },
  { id: "BOS-CHI-2025-332", route: "Boston → Chicago",      product: "Produce",      temp: 3.1,  status: "DELAYED",    eta: "16:30 UTC", customer: "US Foods",       compliance: true  },
  { id: "LA-SEA-2025-156",  route: "Los Angeles → Seattle", product: "Frozen Foods", temp: -20,  status: "DELIVERED",  eta: "—",         customer: "Amazon Fresh",   compliance: true  },
  { id: "CHI-LA-2025-445",  route: "Chicago → L.A.",        product: "Meat",         temp: -18.4, status: "IN TRANSIT", eta: "22:00 UTC", customer: "Kroger",        compliance: true  },
  { id: "DAL-MIA-2025-210", route: "Dallas → Miami",        product: "Produce",      temp: 7.2,  status: "BREACH",     eta: "20:00 UTC", customer: "Publix",         compliance: false },
  { id: "CHI-NYC-2025-098", route: "Chicago → New York",    product: "Dairy",        temp: 1.2,  status: "IN TRANSIT", eta: "10:00 UTC", customer: "Whole Foods",    compliance: true  },
  { id: "SEA-POR-2025-044", route: "Seattle → Portland",    product: "Seafood",      temp: -1.8, status: "IN TRANSIT", eta: "09:00 UTC", customer: "New Seasons",    compliance: true  },
];

const statusBadge: Record<string, string> = {
  "BREACH":     "badge-breach",
  "IN TRANSIT": "badge-transit",
  "DELAYED":    "badge-delayed",
  "DELIVERED":  "badge-delivered",
};

export default function ShipmentsPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");

  const filtered = SHIPMENTS.filter(s => {
    const matchSearch = s.id.toLowerCase().includes(search.toLowerCase()) ||
      s.route.toLowerCase().includes(search.toLowerCase()) ||
      s.customer.toLowerCase().includes(search.toLowerCase()) ||
      s.product.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === "ALL" || s.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Shipments" subtitle={`${SHIPMENTS.length} active shipments`} />
      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        {/* Filters */}
        <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
          <input
            placeholder="Search shipment ID, route, customer..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              flex: 1, background: "var(--bg-card)", border: "1px solid var(--border)",
              borderRadius: 6, padding: "8px 14px", color: "var(--text-primary)", fontSize: "0.8rem",
            }}
          />
          {["ALL", "IN TRANSIT", "BREACH", "DELAYED", "DELIVERED"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{
                padding: "7px 14px", borderRadius: 6, fontSize: "0.72rem", cursor: "pointer",
                background: filter === f ? "var(--teal)" : "var(--bg-card)",
                color: filter === f ? "#020d1a" : "var(--text-muted)",
                border: filter === f ? "none" : "1px solid var(--border)",
                fontWeight: filter === f ? 700 : 400,
              }}>
              {f}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="card" style={{ overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
            <thead>
              <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
                {["Shipment ID", "Route", "Product", "Customer", "Temp", "Status", "ETA", "Compliance"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6rem", letterSpacing: "0.06em" }}>
                    {h.toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <tr key={s.id}
                  style={{ borderBottom: "1px solid var(--border)", cursor: "pointer" }}
                  onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "var(--bg-card)"}
                  onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                >
                  <td style={{ padding: "11px 14px", fontFamily: "monospace", color: "var(--teal)", fontSize: "0.7rem" }}>{s.id}</td>
                  <td style={{ padding: "11px 14px", color: "var(--text-secondary)" }}>{s.route}</td>
                  <td style={{ padding: "11px 14px" }}>
                    <span className="badge badge-transit">{s.product}</span>
                  </td>
                  <td style={{ padding: "11px 14px", color: "var(--text-secondary)" }}>{s.customer}</td>
                  <td style={{ padding: "11px 14px", color: s.temp > 4 ? "#ef4444" : s.temp > 2 ? "#f59e0b" : "#4ade80", fontWeight: 700 }}>
                    {s.temp > 0 ? "+" : ""}{s.temp}°C
                  </td>
                  <td style={{ padding: "11px 14px" }}>
                    <span className={`badge ${statusBadge[s.status] || "badge-ok"}`}>{s.status}</span>
                  </td>
                  <td style={{ padding: "11px 14px", color: "var(--text-muted)" }}>{s.eta}</td>
                  <td style={{ padding: "11px 14px" }}>
                    {s.compliance
                      ? <span style={{ color: "#4ade80", fontSize: "0.72rem" }}>✓ Compliant</span>
                      : <span style={{ color: "#f87171", fontSize: "0.72rem" }}>✗ Breach</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              No shipments match your search
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
