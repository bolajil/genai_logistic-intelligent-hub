"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Zap, Truck, Bell, BarChart3,
  FolderOpen, Settings, Shield, History, Lock, LogOut
} from "lucide-react";
import { usePermissions } from "@/hooks/usePermissions";
import { useAuth } from "@/app/contexts/AuthContext";

type NavItem = {
  href: string;
  icon: React.ElementType;
  label: string;
  badge?: number;
  badgeColor?: string;
  permission?: string;
};

const nav: { group: string; items: NavItem[] }[] = [
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
    { href: "/history",    icon: History,    label: "History" },
  ]},
  { group: "SYSTEM", items: [
    { href: "/settings",   icon: Settings,  label: "Settings",  permission: "settings:view" },
    { href: "/admin",      icon: Shield,    label: "Admin",     permission: "admin:users"   },
  ]},
];

export default function Sidebar() {
  const pathname = usePathname();
  const { can } = usePermissions();
  const { user, logout } = useAuth();

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
            {items.map(({ href, icon: Icon, label, badge, badgeColor, permission }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              const locked = permission ? !can(permission as any) : false;
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
                    opacity: locked ? 0.5 : 1,
                  }}
                  onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)"; }}
                  onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "var(--text-muted)"; }}
                  >
                    <Icon size={15} color={active ? "var(--teal)" : undefined} />
                    <span style={{ flex: 1 }}>{label}</span>
                    {locked && <Lock size={11} style={{ color: "var(--text-dim)", flexShrink: 0 }} />}
                    {!locked && badge && (
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

      {/* User profile + logout */}
      {user && (
        <div style={{
          padding: "12px 16px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}>
          <div style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: "var(--teal)",
            color: "#020d1a",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: "0.7rem",
            flexShrink: 0,
          }}>
            {user.name?.charAt(0).toUpperCase() ?? "U"}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user.name}
            </div>
            <div style={{ fontSize: "0.6rem", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {user.role}
            </div>
          </div>
          <button
            onClick={logout}
            title="Log out"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "var(--text-muted)",
              padding: 4,
              borderRadius: 4,
              display: "flex",
              alignItems: "center",
              flexShrink: 0,
            }}
            onMouseEnter={e => (e.currentTarget.style.color = "#ef4444")}
            onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <LogOut size={14} />
          </button>
        </div>
      )}

    </aside>
  );
}
