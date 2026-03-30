"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/app/contexts/AuthContext";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { loading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    // No user after hydration — cookie was stale, send to login
    if (!user) {
      router.replace("/login");
      return;
    }
    // Mandatory password change — block all app routes
    if ((user as any).force_password_change) {
      router.replace("/change-password");
    }
  }, [loading, user, router]);

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
