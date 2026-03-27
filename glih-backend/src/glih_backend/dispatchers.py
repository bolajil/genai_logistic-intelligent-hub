"""
Dispatcher management for GLIH - handles dispatcher accounts and authentication.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import hashlib
import secrets
import logging

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


# Admin account (separate from dispatchers)
_admin = {
    "username": "admin",
    "password_hash": hashlib.sha256("lineage2026".encode()).hexdigest(),
    "name": "System Administrator",
    "role": "admin",
}

# In-memory storage for dispatchers (in production, use a real database)
_dispatchers: Dict[str, Dict[str, Any]] = {
    "jmartinez": {
        "id": "DISP-001",
        "username": "jmartinez",
        "name": "John Martinez",
        "title": "Cold Chain Operations Dispatcher",
        "email": "john.martinez@lineagelogistics.com",
        "facility": "Chicago",
        "shift": "Day",
        "active": True,
        "created_at": "2025-01-15T08:00:00"
    },
    "sthompson": {
        "id": "DISP-002",
        "username": "sthompson",
        "name": "Sarah Thompson",
        "title": "Senior Operations Dispatcher",
        "email": "sarah.thompson@lineagelogistics.com",
        "facility": "Chicago",
        "shift": "Night",
        "active": True,
        "created_at": "2025-02-01T08:00:00"
    },
    "mwilson": {
        "id": "DISP-003",
        "username": "mwilson",
        "name": "Michael Wilson",
        "title": "Operations Dispatcher",
        "email": "michael.wilson@lineagelogistics.com",
        "facility": "Atlanta",
        "shift": "Day",
        "active": True,
        "created_at": "2025-03-01T08:00:00"
    },
}

# Active sessions (token -> dispatcher_id)
_sessions: Dict[str, str] = {}


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    return hash_password(password) == password_hash


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
        logger.warning(f"Login failed: invalid password for admin")
        return None
    
    # Create session
    token = generate_token()
    _sessions[token] = "ADMIN"
    
    logger.info(f"Admin logged in successfully")
    
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
    for dispatcher in _dispatchers.values():
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
    """Get all dispatchers (without passwords)."""
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
        for d in _dispatchers.values()
    ]


def create_dispatcher(data: DispatcherCreate) -> Dict[str, Any]:
    """Create a new dispatcher account."""
    if data.username in _dispatchers:
        raise ValueError(f"Username '{data.username}' already exists")
    
    dispatcher_id = f"DISP-{len(_dispatchers) + 1:03d}"
    
    _dispatchers[data.username] = {
        "id": dispatcher_id,
        "username": data.username,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "title": data.title,
        "email": data.email,
        "facility": data.facility,
        "shift": data.shift,
        "active": True,
        "created_at": datetime.now().isoformat(),
    }
    
    logger.info(f"Created dispatcher account: {data.username}")
    
    return {
        "id": dispatcher_id,
        "username": data.username,
        "name": data.name,
        "title": data.title,
        "email": data.email,
        "facility": data.facility,
        "shift": data.shift,
    }
