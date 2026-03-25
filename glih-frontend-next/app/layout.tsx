import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./contexts/AuthContext";

export const metadata: Metadata = {
  title: "GLIH OPS — Cold Chain Intelligence",
  description: "GenAI Logistics Intelligence Hub — Production Operations Platform",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full" style={{ background: "var(--bg-primary)", color: "var(--text-primary)" }}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
