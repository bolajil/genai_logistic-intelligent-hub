"use client";
import { Bell, RefreshCw, Settings } from "lucide-react";
import Link from "next/link";

interface HeaderProps {
  title: string;
  subtitle?: string;
  live?: boolean;
}

export default function Header({ title, subtitle, live = false }: HeaderProps) {
  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "14px 24px",
      borderBottom: "1px solid var(--border)",
      background: "var(--bg-secondary)",
    }}>
      <div>
        <h1 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
          {title}
        </h1>
        {subtitle && (
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: 2 }}>
            {subtitle}
          </div>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {live && (
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "#052e16", border: "1px solid #14532d",
            borderRadius: 6, padding: "4px 10px",
          }}>
            <span className="pulse-dot green" />
            <span style={{ color: "#4ade80", fontSize: "0.65rem", fontWeight: 700 }}>LIVE</span>
          </div>
        )}
        <Link href="/alerts">
          <button style={{
            background: "var(--bg-card)", border: "1px solid var(--border)",
            borderRadius: 6, padding: "6px 8px", cursor: "pointer",
            color: "var(--text-secondary)", display: "flex", alignItems: "center",
          }}>
            <Bell size={14} />
          </button>
        </Link>
        <Link href="/settings">
          <button style={{
            background: "var(--bg-card)", border: "1px solid var(--border)",
            borderRadius: 6, padding: "6px 8px", cursor: "pointer",
            color: "var(--text-secondary)", display: "flex", alignItems: "center",
          }}>
            <Settings size={14} />
          </button>
        </Link>
      </div>
    </header>
  );
}
