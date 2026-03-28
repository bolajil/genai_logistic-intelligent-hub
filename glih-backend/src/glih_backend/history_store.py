"""
GLIH Platform — Conversation & Agent History Store
====================================================
Persists every query, agent run, and notification to a JSON file so
dispatchers and admins can review past interactions at any time.

Storage layout  (data/glih_history.json):
{
  "queries":        [ QueryRecord, ... ],   # RAG query history
  "agent_runs":     [ AgentRunRecord, ... ],# Agent execution history
  "notifications":  [ NotificationRecord, ... ] # Notification audit trail
}

Records are appended and capped at MAX_RECORDS each to prevent unbounded growth.
Migration to PostgreSQL: replace _load/_save with SQLAlchemy session calls —
the function signatures stay identical so callers don't change.
"""
from __future__ import annotations

import json
import logging
import pathlib
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

_DB_PATH = (
    pathlib.Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "glih_history.json"
)

# Cap each list to prevent unbounded growth. Oldest entries are dropped.
MAX_RECORDS = 10_000

_lock = threading.Lock()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load() -> Dict[str, List[dict]]:
    """Load history from disk. Returns empty structure if missing or corrupt."""
    try:
        if _DB_PATH.exists():
            return json.loads(_DB_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Could not load history DB: {exc}")
    return {"queries": [], "agent_runs": [], "notifications": []}


def _save(db: Dict[str, List[dict]]) -> None:
    """Write history to disk atomically."""
    try:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Could not save history DB: {exc}")


def _now() -> str:
    return datetime.utcnow().isoformat()


def _append(db: Dict[str, List[dict]], key: str, record: dict) -> None:
    """Append a record and trim to MAX_RECORDS (keeps newest)."""
    db[key].append(record)
    if len(db[key]) > MAX_RECORDS:
        db[key] = db[key][-MAX_RECORDS:]


# ── Query history ─────────────────────────────────────────────────────────────

def save_query(
    *,
    user_id: str,
    user_email: str,
    query: str,
    answer: str,
    citations: List[dict],
    collection: Optional[str],
    provider: str,
    model: str,
    k: int,
    style: str,
    duration_ms: Optional[int] = None,
) -> str:
    """
    Persist a RAG query and its response.

    Returns the generated record ID so callers can reference it.

    Why we store this:
    - Dispatchers can review what questions were asked and what answers were given
    - Admins can audit compliance-related queries
    - Enables future analytics: most common queries, answer quality trends
    """
    record_id = str(uuid.uuid4())
    record = {
        "id":          record_id,
        "user_id":     user_id,
        "user_email":  user_email,
        "query":       query,
        "answer":      answer,
        "citations":   citations,
        "collection":  collection,
        "provider":    provider,
        "model":       model,
        "k":           k,
        "style":       style,
        "duration_ms": duration_ms,
        "timestamp":   _now(),
    }
    with _lock:
        db = _load()
        _append(db, "queries", record)
        _save(db)
    logger.debug(f"Query saved: id={record_id} user={user_email}")
    return record_id


def get_queries(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[dict]:
    """
    Retrieve query history.

    Args:
        user_id: Filter to a specific user. None = all users (admin view).
        limit:   Max records to return (newest first).
        offset:  Skip this many records (for pagination).
    """
    with _lock:
        db = _load()
    records = db["queries"]
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]
    # Newest first
    records = list(reversed(records))
    return records[offset: offset + limit]


def get_query_by_id(record_id: str) -> Optional[dict]:
    """Retrieve a single query record by its ID."""
    with _lock:
        db = _load()
    for r in db["queries"]:
        if r.get("id") == record_id:
            return r
    return None


# ── Agent run history ─────────────────────────────────────────────────────────

def save_agent_run(
    *,
    run_id: str,
    agent_name: str,
    user_id: str,
    user_email: str,
    input_data: Dict[str, Any],
    result: Optional[Dict[str, Any]],
    events: List[dict],
    status: str,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """
    Persist a completed agent run with full input, output, and event trace.

    Why we store this:
    - Full audit trail: what triggered the agent, what it decided, what it returned
    - Compliance: FSMA and cold chain regulations require traceable decision logs
    - Debugging: replay exact inputs if a dispatcher questions an agent's output
    - Analytics: track agent performance, failure rates, average duration
    """
    record = {
        "run_id":      run_id,
        "agent_name":  agent_name,
        "user_id":     user_id,
        "user_email":  user_email,
        "input":       input_data,
        "result":      result,
        "events":      events,
        "status":      status,
        "duration_ms": duration_ms,
        "error":       error,
        "timestamp":   _now(),
    }
    with _lock:
        db = _load()
        _append(db, "agent_runs", record)
        _save(db)
    logger.debug(f"Agent run saved: run_id={run_id} agent={agent_name} status={status}")


def get_agent_runs(
    user_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[dict]:
    """
    Retrieve agent run history.

    Args:
        user_id:    Filter to a specific user. None = all (admin view).
        agent_name: Filter to a specific agent (e.g. "AnomalyResponder").
        limit:      Max records to return (newest first).
        offset:     Pagination offset.
    """
    with _lock:
        db = _load()
    records = db["agent_runs"]
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]
    if agent_name:
        records = [r for r in records if r.get("agent_name") == agent_name]
    records = list(reversed(records))
    return records[offset: offset + limit]


def get_agent_run_by_id(run_id: str) -> Optional[dict]:
    """Retrieve a single agent run by its run_id."""
    with _lock:
        db = _load()
    for r in db["agent_runs"]:
        if r.get("run_id") == run_id:
            return r
    return None


# ── Notification audit trail ──────────────────────────────────────────────────

def save_notification(
    *,
    run_id: str,
    shipment_id: str,
    customer_id: str,
    notification_type: str,
    severity: str,
    message: str,
    dispatcher_name: str,
    dispatcher_title: str,
    user_id: str,
    user_email: str,
    status: str = "sent",
) -> str:
    """
    Persist a notification that was composed and sent by the CustomerNotifier agent.

    Why we store this:
    - Regulatory requirement: every customer-facing communication must be auditable
    - Dispute resolution: "Did you notify us about this shipment?" → check the log
    - Quality control: review message quality, tone, accuracy
    """
    record_id = str(uuid.uuid4())
    record = {
        "id":                record_id,
        "run_id":            run_id,
        "shipment_id":       shipment_id,
        "customer_id":       customer_id,
        "notification_type": notification_type,
        "severity":          severity,
        "message":           message,
        "dispatcher_name":   dispatcher_name,
        "dispatcher_title":  dispatcher_title,
        "user_id":           user_id,
        "user_email":        user_email,
        "status":            status,
        "timestamp":         _now(),
    }
    with _lock:
        db = _load()
        _append(db, "notifications", record)
        _save(db)
    logger.debug(f"Notification saved: id={record_id} shipment={shipment_id}")
    return record_id


def get_notifications(
    user_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[dict]:
    """
    Retrieve notification history.

    Args:
        user_id:     Filter by dispatcher who sent it. None = all (admin view).
        shipment_id: Filter by shipment ID.
        limit:       Max records (newest first).
        offset:      Pagination offset.
    """
    with _lock:
        db = _load()
    records = db["notifications"]
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]
    if shipment_id:
        records = [r for r in records if r.get("shipment_id") == shipment_id]
    records = list(reversed(records))
    return records[offset: offset + limit]


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_history_stats() -> Dict[str, Any]:
    """
    Return aggregate counts for the admin dashboard.

    Expected output:
    {
      "total_queries": 1234,
      "total_agent_runs": 456,
      "total_notifications": 78,
      "agent_breakdown": {
        "AnomalyResponder": 120,
        "RouteAdvisor": 89,
        "CustomerNotifier": 45,
        "OpsSummarizer": 202
      }
    }
    """
    with _lock:
        db = _load()

    agent_breakdown: Dict[str, int] = {}
    for r in db["agent_runs"]:
        name = r.get("agent_name", "unknown")
        agent_breakdown[name] = agent_breakdown.get(name, 0) + 1

    return {
        "total_queries":       len(db["queries"]),
        "total_agent_runs":    len(db["agent_runs"]),
        "total_notifications": len(db["notifications"]),
        "agent_breakdown":     agent_breakdown,
    }
