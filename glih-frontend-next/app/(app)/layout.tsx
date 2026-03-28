"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/app/contexts/AuthContext";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { loading } = useAuth();
  const router = useRouter();

  // If the user is logged in but hasn't changed their default password yet,
  // block access to every app page and redirect them to /change-password.
  useEffect(() => {
    if (loading) return;
    try {
      const stored = localStorage.getItem("glih_user");
      if (stored) {
        const u = JSON.parse(stored);
        if (u.force_password_change) {
          router.replace("/change-password");
        }
      }
    } catch {
      // ignore parse errors
    }
  }, [loading, router]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "var(--bg-primary)", color: "var(--text-muted)", fontSize: 13 }}>
        Loading…
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: "auto", background: "var(--bg-primary)" }}>
        {children}
      </main>
    </div>
  );
}
