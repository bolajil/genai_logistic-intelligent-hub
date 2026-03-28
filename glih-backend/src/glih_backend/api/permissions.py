"""
GLIH Platform — Role-Based Permission Enforcement
===================================================
Roles (lowest → highest):
  viewer   — read-only: query, view dashboards, own history
  analyst  — operational: run agents, ingest docs, manage fleet/shipments
  admin    — full access: system config, user management, all history

Usage in endpoints:
    @app.post("/ingest")
    async def ingest(..., _=Depends(require_permission("documents:ingest"))):
        ...
"""
from __future__ import annotations

from typing import Set
from fastapi import Depends, HTTPException

from .auth_utils import get_current_user

# ── Permission catalogue ───────────────────────────────────────────────────────

PERMISSIONS: dict[str, Set[str]] = {
    "viewer": {
        "rag:query",
        "fleet:view",
        "shipments:view",
        "alerts:view",
        "analytics:view",
        "history:own",
        "documents:view",
    },
    "analyst": {
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
    },
    "admin": {
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
    },
}


def _role_can(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())


# ── FastAPI dependency factory ────────────────────────────────────────────────

def require_permission(permission: str):
    """
    Returns a FastAPI dependency that enforces the given permission.
    Raises 403 if the authenticated user's role does not have it.
    """
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role", "viewer")
        if not _role_can(role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — '{permission}' requires a higher role (you are '{role}').",
            )
        return current_user
    return _check


def require_role(minimum_role: str):
    """
    Shortcut: enforce a minimum role level.
    Order: viewer < analyst < admin
    """
    _order = {"viewer": 0, "analyst": 1, "admin": 2}
    required_level = _order.get(minimum_role, 99)

    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role", "viewer")
        if _order.get(role, -1) < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — requires '{minimum_role}' role or higher (you are '{role}').",
            )
        return current_user
    return _check
