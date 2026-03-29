"""
Dispatcher management for GLIH - handles dispatcher accounts and authentication.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import os
import json as _json
import pathlib as _pathlib
import secrets
import logging
from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


class Dispatcher(BaseModel):
    """Dispatcher account model."""
    id: str
    username: str
    name: str
    title: str
    email: str
    facility: str = "Chicago"
    shift: str = "Day"
    active: bool = True
    created_at: str = ""
    
    
class DispatcherCreate(BaseModel):
    """Request model for creating a dispatcher."""
    username: str
    password: str
    name: str
    title: str = "Operations Dispatcher"
    email: str
    facility: str = "Chicago"
    shift: str = "Day"


class DispatcherLogin(BaseModel):
    """Request model for dispatcher login."""
    username: str
    password: str


# Admin account — password from env var only. No default allowed in production.
_ADMIN_PASSWORD = os.getenv("DISPATCHER_ADMIN_PASSWORD", "")
if not _ADMIN_PASSWORD:
    import warnings
    warnings.warn(
        "DISPATCHER_ADMIN_PASSWORD env var is not set. "
        "Dispatcher admin login will be disabled until it is configured.",
        stacklevel=1,
    )

_admin = {
    "username": "admin",
    # bcrypt hash computed at startup from env var; empty string if not configured
    "password_hash": _pwd_ctx.hash(_ADMIN_PASSWORD) if _ADMIN_PASSWORD else "",
    "name": "System Administrator",
    "role": "admin",
}

# ── File-backed dispatcher store ─────────────────────────────────────────────
_DISP_DB_PATH = _pathlib.Path(__file__).parent.parent.parent.parent.parent / "data" / "glih_dispatchers.json"

_SEED_DISPATCHERS: Dict[str, Dict[str, Any]] = {
    "jmartinez": {
        "id": "DISP-001", "username": "jmartinez",
        "name": "John Martinez", "title": "Cold Chain Operations Dispatcher",
        "email": "john.martinez@lineagelogistics.com",
        "facility": "Chicago", "shift": "Day", "active": True,
        "created_at": "2025-01-15T08:00:00",
    },
    "sthompson": {
        "id": "DISP-002", "username": "sthompson",
        "name": "Sarah Thompson", "title": "Senior Operations Dispatcher",
        "email": "sarah.thompson@lineagelogistics.com",
        "facility": "Chicago", "shift": "Night", "active": True,
        "created_at": "2025-02-01T08:00:00",
    },
    "mwilson": {
        "id": "DISP-003", "username": "mwilson",
        "name": "Michael Wilson", "title": "Operations Dispatcher",
        "email": "michael.wilson@lineagelogistics.com",
        "facility": "Atlanta", "shift": "Day", "active": True,
        "created_at": "2025-03-01T08:00:00",
    },
}


def _load_disp_db() -> Dict[str, Dict[str, Any]]:
    """Load dispatcher records from disk, seeding static entries on first run."""
    try:
        if _DISP_DB_PATH.exists():
            data = _json.loads(_DISP_DB_PATH.read_text())
            # Merge seed entries so they always appear even if file predates them
            merged = {**_SEED_DISPATCHERS, **data}
            return merged
    except Exception:
        pass
    return dict(_SEED_DISPATCHERS)


def _save_disp_db(db: Dict[str, Dict[str, Any]]) -> None:
    try:
        _DISP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DISP_DB_PATH.write_text(_json.dumps(db, indent=2))
    except Exception as e:
        logger.warning(f"Could not save dispatcher DB: {e}")

# Active sessions (token -> dispatcher_id)
_sessions: Dict[str, str] = {}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return _pwd_ctx.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    if not password_hash:
        return False
    return _pwd_ctx.verify(password, password_hash)


def generate_token() -> str:
    """Generate a secure session token."""
    return secrets.token_hex(32)


def login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate admin and create a session.
    Only admin can login - dispatchers are managed by admin.
    Returns admin info and token if successful, None otherwise.
    """
    # Only admin can login
    if username != _admin["username"]:
        logger.warning(f"Login failed: user '{username}' not found (only admin can login)")
        return None
    
    if not verify_password(password, _admin["password_hash"]):
        logger.warning("Login failed: invalid password for admin")
        return None
    
    # Create session
    token = generate_token()
    _sessions[token] = "ADMIN"
    
    logger.info("Admin logged in successfully")
    
    return {
        "token": token,
        "user": {
            "username": _admin["username"],
            "name": _admin["name"],
            "role": _admin["role"],
        }
    }


def logout(token: str) -> bool:
    """End a dispatcher session."""
    if token in _sessions:
        del _sessions[token]
        return True
    return False


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get user info from session token (admin only)."""
    session_id = _sessions.get(token)
    if not session_id:
        return None
    
    if session_id == "ADMIN":
        return {
            "username": _admin["username"],
            "name": _admin["name"],
            "role": _admin["role"],
        }
    return None


def get_dispatcher_by_id(dispatcher_id: str) -> Optional[Dict[str, Any]]:
    """Get dispatcher info by ID."""
    for dispatcher in _load_disp_db().values():
        if dispatcher["id"] == dispatcher_id:
            return {
                "id": dispatcher["id"],
                "name": dispatcher["name"],
                "title": dispatcher["title"],
                "email": dispatcher["email"],
                "facility": dispatcher["facility"],
                "shift": dispatcher["shift"],
                "active": dispatcher["active"],
            }
    return None


def get_all_dispatchers() -> List[Dict[str, Any]]:
    """Get all dispatchers from persistent store (without passwords)."""
    db = _load_disp_db()
    return [
        {
            "id": d["id"],
            "username": d["username"],
            "name": d["name"],
            "title": d["title"],
            "email": d["email"],
            "facility": d["facility"],
            "shift": d["shift"],
            "active": d["active"],
        }
        for d in db.values()
    ]


def create_dispatcher(data: DispatcherCreate) -> Dict[str, Any]:
    """Create a new dispatcher account and persist to disk."""
    db = _load_disp_db()
    if data.username in db:
        raise ValueError(f"Username '{data.username}' already exists")

    dispatcher_id = f"DISP-{len(db) + 1:03d}"
    record = {
        "id": dispatcher_id,
        "username": data.username,
        "name": data.name,
        "title": data.title,
        "email": data.email,
        "facility": data.facility,
        "shift": data.shift,
        "active": True,
        "created_at": datetime.now().isoformat(),
    }
    db[data.username] = record
    _save_disp_db(db)

    logger.info(f"Created dispatcher account: {data.username} (persisted to disk)")

    return {
        "id": dispatcher_id,
        "username": data.username,
        "name": data.name,
        "title": data.title,
        "email": data.email,
        "facility": data.facility,
        "shift": data.shift,
    }
