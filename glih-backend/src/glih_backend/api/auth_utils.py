"""
GLIH Platform — JWT Auth Utilities
====================================
Access token  : 15-min HS256 JWT
Refresh token : 48-byte random token (in-memory store, Redis if available)
Admin seed    : admin@glih.ops / glih-admin-2025  (force_password_change=True)
"""
from __future__ import annotations

import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS   = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))
ALGORITHM                   = "HS256"

_JWT_SECRET_RAW = os.getenv("JWT_SECRET", "")
_GLIH_ENV       = os.getenv("GLIH_ENV", "development")

if not _JWT_SECRET_RAW:
    if _GLIH_ENV == "production":
        raise RuntimeError("JWT_SECRET env var is required in production. Set it before starting.")
    # Dev fallback — insecure, logged as warning
    _JWT_SECRET_RAW = "glih-dev-only-insecure-secret-do-not-use-in-production"
    logger.warning("JWT_SECRET not set — using insecure dev default. Set JWT_SECRET before deploying.")

if len(_JWT_SECRET_RAW) < 32:
    logger.warning("JWT_SECRET is shorter than 32 characters — use a longer secret in production.")

JWT_SECRET_KEY = _JWT_SECRET_RAW

_bearer = HTTPBearer(auto_error=False)

# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    from passlib.context import CryptContext
    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    from passlib.context import CryptContext
    return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain, hashed)

# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str, name: str) -> str:
    from jose import jwt as _jwt
    payload = {
        "sub":   user_id,
        "email": email,
        "name":  name,
        "exp":   datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat":   datetime.utcnow(),
        "type":  "access",
    }
    return _jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def decode_access_token(token: str) -> dict:
    from jose import JWTError, ExpiredSignatureError, jwt as _jwt
    try:
        payload = _jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")

# ── File-backed user store (survives backend restarts) ───────────────────────

import json as _json
import pathlib as _pathlib

_DB_PATH = _pathlib.Path(__file__).parent.parent.parent.parent.parent / "data" / "glih_users.json"
_mem_refresh: dict[str, str] = {}


def _load_db() -> dict:
    try:
        if _DB_PATH.exists():
            return _json.loads(_DB_PATH.read_text())
    except Exception:
        pass
    return {"by_email": {}, "by_id": {}}


def _save_db(db: dict) -> None:
    try:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DB_PATH.write_text(_json.dumps(db, indent=2))
    except Exception as e:
        logger.warning(f"Could not save user DB: {e}")


def store_user(user: dict) -> None:
    db = _load_db()
    db["by_email"][user["email"].lower()] = user
    db["by_id"][user["id"]] = user
    _save_db(db)


def get_user_by_email(email: str) -> Optional[dict]:
    return _load_db()["by_email"].get(email.lower())


def get_user_by_id(user_id: str) -> Optional[dict]:
    return _load_db()["by_id"].get(user_id)


def store_refresh_token(token: str, user_id: str) -> None:
    _mem_refresh[token] = user_id


def get_refresh_token_owner(token: str) -> Optional[str]:
    return _mem_refresh.get(token)


def delete_refresh_token(token: str) -> None:
    _mem_refresh.pop(token, None)

# ── Admin seed ────────────────────────────────────────────────────────────────

def create_admin_user() -> None:
    email = "admin@glih.ops"
    if get_user_by_email(email):
        return
    admin = {
        "id":                    str(uuid.uuid4()),
        "name":                  "GLIH Admin",
        "email":                 email,
        "hashed_password":       hash_password("glih-admin-2025"),
        "role":                  "admin",
        "created_at":            datetime.utcnow().isoformat(),
        "force_password_change": True,
    }
    store_user(admin)
    logger.info("Default admin created: admin@glih.ops (password change required on first login)")

# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    payload = decode_access_token(creds.credentials)
    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user
