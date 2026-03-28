"use client";
import { useAuth } from "@/app/contexts/AuthContext";

/**
 * GLIH Permission Hook
 * --------------------
 * Mirrors the backend PERMISSIONS map in permissions.py.
 * Usage:
 *   const { can } = usePermissions();
 *   if (can("agents:run")) { ... }
 */

type Permission =
  | "rag:query"
  | "documents:view"
  | "documents:ingest"
  | "agents:run"
  | "fleet:view"
  | "fleet:manage"
  | "shipments:view"
  | "alerts:view"
  | "analytics:view"
  | "history:own"
  | "history:all"
  | "settings:view"
  | "settings:edit"
  | "admin:users"
  | "admin:system";

const ROLE_PERMISSIONS: Record<string, Set<Permission>> = {
  viewer: new Set([
    "rag:query",
    "documents:view",
    "fleet:view",
    "shipments:view",
    "alerts:view",
    "analytics:view",
    "history:own",
  ]),
  analyst: new Set([
    "rag:query",
    "documents:view",
    "documents:ingest",
    "agents:run",
    "fleet:view",
    "fleet:manage",
    "shipments:view",
    "alerts:view",
    "analytics:view",
    "history:own",
  ]),
  admin: new Set([
    "rag:query",
    "documents:view",
    "documents:ingest",
    "agents:run",
    "fleet:view",
    "fleet:manage",
    "shipments:view",
    "alerts:view",
    "analytics:view",
    "history:own",
    "history:all",
    "settings:view",
    "settings:edit",
    "admin:users",
    "admin:system",
  ]),
};

export function usePermissions() {
  const { user } = useAuth();
  const role = (user as any)?.role ?? "viewer";
  const perms = ROLE_PERMISSIONS[role] ?? ROLE_PERMISSIONS["viewer"];

  const can = (permission: Permission): boolean => perms.has(permission);

  return { can, role };
}
