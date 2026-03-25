"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Zap, Truck, Bell, BarChart3,
  FolderOpen, Settings, Shield, ChevronRight
} from "lucide-react";

const nav = [
  { group: "OPERATIONS", items: [
    { href: "/dashboard",  icon: LayoutDashboard, label: "Dashboard" },
    { href: "/agents",     icon: Zap,             label: "Agents",    badge: 4 },
    { href: "/fleet",      icon: Truck,           label: "Fleet" },
    { href: "/shipments",  icon: Truck,           label: "Shipments" },
    { href: "/alerts",     icon: Bell,            label: "Alerts",    badge: 3, badgeColor: "#f59e0b" },
  ]},
  { group: "INTELLIGENCE", items: [
    { href: "/analytics",  icon: BarChart3,  label: "Analytics" },
    { href: "/documents",  icon: FolderOpen, label: "Documents" },
  ]},
  { group: "SYSTEM", items: [
    { href: "/settings",   icon: Settings,  label: "Settings" },
    { href: "/admin",      icon: Shield,    label: "Admin" },
  ]},
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside style={{
      width: 220,
      minWidth: 220,
      background: "var(--bg-secondary)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      position: "sticky",
      top: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 16px 16px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ color: "var(--teal)", fontWeight: 800, fontSize: "0.95rem", letterSpacing: "0.1em" }}>
          GLIH OPS
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.6rem", letterSpacing: "0.08em", marginTop: 2 }}>
          COLD CHAIN INTELLIGENCE
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "12px 0" }}>
        {nav.map(({ group, items }) => (
          <div key={group} style={{ marginBottom: 8 }}>
            <div style={{
              padding: "8px 16px 4px",
              fontSize: "0.58rem",
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: "var(--text-dim)",
            }}>
              {group}
            </div>
            {items.map(({ href, icon: Icon, label, badge, badgeColor }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link key={href} href={href} style={{ textDecoration: "none" }}>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "8px 16px",
                    fontSize: "0.78rem",
                    color: active ? "var(--text-primary)" : "var(--text-muted)",
                    background: active ? "var(--bg-card)" : "transparent",
                    borderRight: active ? "2px solid var(--teal)" : "2px solid transparent",
                    cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                  onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)"; }}
                  onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "var(--text-muted)"; }}
                  >
                    <Icon size={15} color={active ? "var(--teal)" : undefined} />
                    <span style={{ flex: 1 }}>{label}</span>
                    {badge && (
                      <span style={{
                        background: badgeColor || "var(--teal)",
                        color: badgeColor ? "#1a0a00" : "#020d1a",
                        borderRadius: 10,
                        fontSize: "0.6rem",
                        fontWeight: 700,
                        padding: "1px 6px",
                        minWidth: 18,
                        textAlign: "center",
                      }}>{badge}</span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Demo mode + user */}
      <div style={{ borderTop: "1px solid var(--border)", padding: "12px 16px" }}>
        <div style={{
          background: "#052e16",
          border: "1px solid #14532d",
          borderRadius: 6,
          padding: "6px 10px",
          marginBottom: 10,
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}>
          <span className="pulse-dot green" />
          <span style={{ color: "#4ade80", fontSize: "0.65rem", fontWeight: 700 }}>DEMO MODE</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 30, height: 30,
            borderRadius: "50%",
            background: "var(--teal-dim)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--teal)",
            fontWeight: 700,
            fontSize: "0.7rem",
          }}>LB</div>
          <div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-primary)" }}>Lanre Bolaji</div>
            <div style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>ops-manager</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
