import os
import io
import uuid
import re
import time
import logging
import threading
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime as _datetime

# ── Sentry (optional — only activates when SENTRY_DSN is set) ────────────────
_SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        environment=os.getenv("GLIH_ENV", "production"),
        traces_sample_rate=0.2,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
from ..config import load_config, save_config
from ..utils import sanitize_config
from ..dispatchers import (
    login as admin_login,
    logout as admin_logout,
    get_user_by_token,
    get_all_dispatchers,
    get_dispatcher_by_id,
    create_dispatcher,
    DispatcherCreate,
    DispatcherLogin,
)
from ..providers import (
    make_embeddings_provider,
    make_vector_store,
    make_llm_provider,
)
from pypdf import PdfReader
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ── Agent progress store ──────────────────────────────────────────────────────
_progress_lock = threading.Lock()
_progress_store: Dict[str, dict] = {}


def _init_run(run_id: str) -> None:
    with _progress_lock:
        _progress_store[run_id] = {"events": [], "status": "running", "result": None, "error": None}


def emit_progress(run_id: str, step: str, message: str, data: dict = None) -> None:
    event = {"step": step, "message": message, "data": data or {}, "ts": _datetime.utcnow().isoformat()}
    with _progress_lock:
        if run_id in _progress_store:
            _progress_store[run_id]["events"].append(event)
    logger.info(f"[{run_id[:8]}] {step}: {message}")


def _complete_run(run_id: str, result: dict = None, error: str = None) -> None:
    with _progress_lock:
        if run_id in _progress_store:
            _progress_store[run_id]["status"] = "error" if error else "complete"
            _progress_store[run_id]["result"] = result
            _progress_store[run_id]["error"] = error


# ── Rate limiter ──────────────────────────────────────────────────────────────
_RATE_LIMIT_QUERY   = os.getenv("RATE_LIMIT_QUERY",  "30/minute")
_RATE_LIMIT_AGENTS  = os.getenv("RATE_LIMIT_AGENTS", "20/minute")
_RATE_LIMIT_INGEST  = os.getenv("RATE_LIMIT_INGEST", "10/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="GLIH Backend", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "http://localhost:3001", "http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth setup ────────────────────────────────────────────────────────────────
from .auth_utils import (
    create_access_token, create_refresh_token, hash_password, verify_password,
    store_user, get_user_by_email, get_user_by_id,
    store_refresh_token, get_refresh_token_owner, delete_refresh_token,
    get_current_user, create_admin_user,
)
import uuid as _uuid
from datetime import datetime as _dt
from pydantic import EmailStr

@app.on_event("startup")
async def _startup():
    create_admin_user()

class _AuthRegisterReq(BaseModel):
    name:     str
    email:    str
    password: str

class _AuthLoginReq(BaseModel):
    email:    str
    password: str

class _AuthRefreshReq(BaseModel):
    refresh_token: str

class _ChangePwdReq(BaseModel):
    current_password: str
    new_password:     str

def _issue_tokens(user: dict) -> dict:
    access  = create_access_token(user["id"], user["email"], user["name"])
    refresh = create_refresh_token()
    store_refresh_token(refresh, user["id"])
    return {
        "access_token":          access,
        "refresh_token":         refresh,
        "token_type":            "bearer",
        "force_password_change": bool(user.get("force_password_change", False)),
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    }

@app.post("/auth/register", status_code=201)
def auth_register(body: _AuthRegisterReq):
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if get_user_by_email(body.email):
        raise HTTPException(409, "An account with this email already exists")
    user = {
        "id": str(_uuid.uuid4()), "name": body.name.strip(),
        "email": body.email.lower(),
        "hashed_password": hash_password(body.password),
        "role": "user", "created_at": _dt.utcnow().isoformat(),
    }
    store_user(user)
    return _issue_tokens(user)

@app.post("/auth/login")
def auth_login(body: _AuthLoginReq):
    user = get_user_by_email(body.email)
    dummy = "$2b$12$dummyhashtopreventtimingattacksXXXXXXXXXXXXXXXXXXXXXXXX"
    hashed = user["hashed_password"] if user else dummy
    if not verify_password(body.password, hashed) or not user:
        raise HTTPException(401, "Incorrect email or password")
    return _issue_tokens(user)

@app.post("/auth/refresh")
def auth_refresh(body: _AuthRefreshReq):
    user_id = get_refresh_token_owner(body.refresh_token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired refresh token")
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(401, "User no longer exists")
    delete_refresh_token(body.refresh_token)
    return _issue_tokens(user)

@app.post("/auth/logout", status_code=204)
def auth_logout(body: _AuthRefreshReq):
    delete_refresh_token(body.refresh_token)

@app.get("/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "name": current_user["name"],
            "email": current_user["email"], "role": current_user["role"]}

@app.post("/auth/change-password")
def auth_change_password(body: _ChangePwdReq, current_user: dict = Depends(get_current_user)):
    if not verify_password(body.current_password, current_user["hashed_password"]):
        raise HTTPException(400, "Current password is incorrect")
    if body.current_password == body.new_password:
        raise HTTPException(400, "New password must be different from current password")
    if len(body.new_password) < 8:
        raise HTTPException(400, "New password must be at least 8 characters")
    store_user({**current_user, "hashed_password": hash_password(body.new_password),
                "force_password_change": False})
    return {"message": "Password updated successfully"}

# Initialize configuration and providers at import-time for simplicity.
_cfg = load_config()
_emb = make_embeddings_provider(_cfg)
_vs = make_vector_store(_cfg)
_llm = make_llm_provider(_cfg)

logger.info(f"GLIH Backend initialized: LLM={_llm.provider}/{_llm.model}, Embeddings={_emb.provider}/{_emb.model}, VectorStore={_vs.provider}")

# ---------------------------------------------------------------------------
# BM25 index cache — keyed by collection name, invalidated on every ingest
# ---------------------------------------------------------------------------
_bm25_cache: Dict[str, Any] = {}


def _invalidate_bm25(collection: str) -> None:
    _bm25_cache.pop(collection, None)


def _get_bm25_index(collection: str) -> Optional[Dict[str, Any]]:
    """Return (or build and cache) a BM25Okapi index for the given collection."""
    if collection in _bm25_cache:
        return _bm25_cache[collection]
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
        coll = _vs.get_collection(collection)
        if coll is None:
            return None
        raw = coll.get(include=["documents", "metadatas"])
        docs: List[str] = raw.get("documents") or []
        ids: List[str] = raw.get("ids") or []
        metas: List[Dict] = raw.get("metadatas") or [{}] * len(docs)
        if not docs:
            return None
        tokenized = [d.lower().split() for d in docs]
        entry: Dict[str, Any] = {
            "bm25": BM25Okapi(tokenized),
            "docs": docs,
            "ids": ids,
            "metas": metas,
        }
        _bm25_cache[collection] = entry
        logger.info(f"BM25 index built for '{collection}': {len(docs)} docs")
        return entry
    except Exception as exc:
        logger.warning(f"BM25 index build failed for '{collection}': {exc}")
        return None


def _hybrid_search(
    query: str,
    collection: str,
    k: int = 4,
    fetch_k: int = 20,
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: ChromaDB vector search + BM25, fused via RRF.
    Falls back to pure vector search if BM25 is unavailable.
    """
    # --- Vector search ---
    q_emb = _emb.embed([query])[0]
    vector_results: List[Dict[str, Any]] = _vs.search_in(collection, q_emb, k=fetch_k)

    # --- BM25 search ---
    bm25_entry = _get_bm25_index(collection)
    if bm25_entry is None:
        return vector_results[:k]

    from rank_bm25 import BM25Okapi  # type: ignore (already imported above)
    bm25: BM25Okapi = bm25_entry["bm25"]
    bm25_docs: List[str] = bm25_entry["docs"]
    bm25_ids: List[str] = bm25_entry["ids"]
    bm25_metas: List[Dict] = bm25_entry["metas"]

    scores = bm25.get_scores(query.lower().split())
    top_bm25_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:fetch_k]

    # --- RRF fusion ---
    rrf_scores: Dict[str, float] = {}
    id_to_result: Dict[str, Dict[str, Any]] = {}

    for rank, result in enumerate(vector_results):
        rid = result["id"]
        rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (rrf_k + rank + 1)
        id_to_result[rid] = result

    for rank, idx in enumerate(top_bm25_idx):
        rid = bm25_ids[idx]
        rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (rrf_k + rank + 1)
        if rid not in id_to_result:
            id_to_result[rid] = {
                "id": rid,
                "document": bm25_docs[idx],
                "metadata": bm25_metas[idx],
                "distance": None,
            }

    fused_ids = sorted(rrf_scores, key=lambda d: rrf_scores[d], reverse=True)
    return [id_to_result[d] for d in fused_ids[:k]]


@app.get("/")
def root():
    return {"service": "GLIH Backend", "status": "ok", "endpoints": ["/health", "/config", "/query"]}


@app.get("/debug/bm25")
def debug_bm25(collection: str = "lineage-sops", q: str = "temperature breach dairy"):
    entry = _get_bm25_index(collection)
    if entry is None:
        return {"status": "failed", "docs": 0}
    scores = entry["bm25"].get_scores(q.lower().split())
    top5 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
    return {
        "status": "ok",
        "total_docs": len(entry["docs"]),
        "query": q,
        "top5": [{"id": entry["ids"][i], "score": round(float(scores[i]), 4), "snippet": entry["docs"][i][:120]} for i in top5],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/detailed")
def health_detailed():
    """Detailed health check with provider status."""
    llm_available = False
    if _llm.provider == "openai":
        llm_available = _llm._openai is not None
    elif _llm.provider == "mistral":
        llm_available = _llm._mistral is not None or bool(os.getenv("MISTRAL_API_KEY"))
    elif _llm.provider == "anthropic":
        llm_available = _llm._anthropic is not None
    elif _llm.provider == "deepseek":
        llm_available = _llm._deepseek is not None

    emb_available = False
    if _emb.provider == "openai":
        emb_available = _emb._openai is not None
    elif _emb.provider == "mistral":
        emb_available = _emb._mistral is not None
    elif _emb.provider == "huggingface":
        emb_available = True

    vs_available = False
    if _vs.provider == "chromadb":
        vs_available = _vs._chroma is not None

    return {
        "status": "ok",
        "timestamp": time.time(),
        "providers": {
            "llm": {
                "provider": _llm.provider,
                "model": _llm.model,
                "available": llm_available,
            },
            "embeddings": {
                "provider": _emb.provider,
                "model": _emb.model,
                "available": emb_available,
            },
            "vector_store": {
                "provider": _vs.provider,
                "collection": _vs.collection,
                "available": vs_available,
            },
        },
        "collections": _vs.list_collections(),
    }


@app.get("/config")
def get_config():
    # Expose sanitized config and chosen providers (no secrets)
    safe = sanitize_config(_cfg)
    api_key_env = (_cfg.get("llm", {}) or {}).get("api_key_env", "OPENAI_API_KEY")
    llm_api_key_present = bool(os.getenv(api_key_env))
    emb_provider = (_cfg.get("embeddings", {}) or {}).get("provider", "openai")
    emb_present = False
    if emb_provider == "openai":
        emb_present = bool(os.getenv("OPENAI_API_KEY"))
    elif emb_provider == "huggingface":
        emb_present = bool(os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN"))
    elif emb_provider == "mistral":
        emb_present = bool(os.getenv("MISTRAL_API_KEY"))
    return {
        "config": safe,
        "providers": {
            "embeddings": {"provider": _emb.provider, "model": _emb.model},
            "vector_store": {"provider": _vs.provider, "collection": _vs.collection},
            "llm": {"provider": _llm.provider, "model": _llm.model},
        },
        "env": {"llm_api_key_present": llm_api_key_present, "embeddings_api_key_present": emb_present},
    }


class IngestRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None
    collection: Optional[str] = None


@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        embeddings = _emb.embed(req.texts)
        if req.collection:
            count = _vs.index_to(req.collection, req.texts, embeddings, req.metadatas)
            coll_name = req.collection
        else:
            count = _vs.index(req.texts, embeddings, req.metadatas)
            coll_name = _vs.collection
        _invalidate_bm25(coll_name)
        return {"ingested": count, "collection": coll_name, "provider": _vs.provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest_failed: {e}")


def _llm_env_key_for(provider: str) -> str:
    mapping = {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }
    return mapping.get(provider, "OPENAI_API_KEY")


class LLMSelectRequest(BaseModel):
    provider: str
    model: Optional[str] = None


@app.get("/llm/current")
def llm_current():
    api_key_env = (_cfg.get("llm", {}) or {}).get("api_key_env", _llm_env_key_for(_cfg.get("llm", {}).get("provider", "openai")))
    return {
        "provider": _cfg.get("llm", {}).get("provider"),
        "model": _cfg.get("llm", {}).get("model"),
        "api_key_env": api_key_env,
        "api_key_present": bool(os.getenv(api_key_env)),
        "supported_providers": ["openai", "deepseek", "anthropic", "mistral"],
    }


@app.post("/llm/select")
def llm_select(req: LLMSelectRequest):
    try:
        provider = (req.provider or "openai").strip().lower()
        model = req.model
        # Update in-memory config
        _cfg.setdefault("llm", {})
        _cfg["llm"]["provider"] = provider
        if model:
            _cfg["llm"]["model"] = model
        _cfg["llm"]["api_key_env"] = _llm_env_key_for(provider)

        # Recreate LLM provider
        global _llm
        _llm = make_llm_provider(_cfg)
        try:
            save_config(_cfg)
        except Exception:
            pass

        api_key_env = _cfg["llm"]["api_key_env"]
        return {
            "ok": True,
            "provider": provider,
            "model": _cfg["llm"].get("model"),
            "api_key_env": api_key_env,
            "api_key_present": bool(os.getenv(api_key_env)),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"llm_select_failed: {e}")


def _emb_env_present_for(provider: str) -> bool:
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "huggingface":
        return bool(os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN"))
    if provider == "mistral":
        return bool(os.getenv("MISTRAL_API_KEY"))
    return False


class EmbeddingsSelectRequest(BaseModel):
    provider: str
    model: Optional[str] = None


@app.get("/embeddings/current")
def embeddings_current():
    provider = (_cfg.get("embeddings", {}) or {}).get("provider", "openai")
    model = (_cfg.get("embeddings", {}) or {}).get("openai_model" if provider == "openai" else (_cfg.get("embeddings", {}) or {}).get("hf_model"))
    return {
        "provider": provider,
        "model": model,
        "api_key_present": _emb_env_present_for(provider),
        "supported_providers": ["openai", "huggingface", "mistral"],
    }


@app.post("/embeddings/select")
def embeddings_select(req: EmbeddingsSelectRequest):
    try:
        provider = (req.provider or "openai").strip().lower()
        model = (req.model or "").strip() or None
        # Update in-memory config
        _cfg.setdefault("embeddings", {})
        _cfg["embeddings"]["provider"] = provider
        if provider == "openai":
            if model:
                _cfg["embeddings"]["openai_model"] = model
        elif provider == "huggingface":
            if model:
                _cfg["embeddings"]["hf_model"] = model
        elif provider == "mistral":
            if model:
                _cfg["embeddings"]["mistral_model"] = model

        # Recreate embeddings provider
        global _emb
        _emb = make_embeddings_provider(_cfg)
        try:
            save_config(_cfg)
        except Exception:
            pass

        return {
            "ok": True,
            "provider": provider,
            "model": _emb.model,
            "api_key_present": _emb_env_present_for(provider),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"embeddings_select_failed: {e}")


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks that always end on a sentence boundary."""
    import re as _re
    chunk_size = max(200, chunk_size)
    overlap = max(0, min(overlap, chunk_size - 1))

    # Split into sentences on ". ", "! ", "? ", "\n" boundaries
    sentence_ends = [m.end() for m in _re.finditer(r'(?<=[.!?])\s+|(?<=\n)', text)]
    # Build sentence list with positions
    positions = [0] + sentence_ends
    sentences = [text[positions[i]:positions[i+1]] for i in range(len(positions)-1)]
    if not sentences:
        return [text.strip()] if text.strip() else []

    out: List[str] = []
    start = 0  # index into sentences list
    while start < len(sentences):
        chunk_parts = []
        length = 0
        i = start
        while i < len(sentences) and length + len(sentences[i]) <= chunk_size:
            chunk_parts.append(sentences[i])
            length += len(sentences[i])
            i += 1
        # If a single sentence is longer than chunk_size, include it anyway
        if not chunk_parts and i < len(sentences):
            chunk_parts.append(sentences[i])
            i += 1
        chunk = "".join(chunk_parts).strip()
        if chunk:
            out.append(chunk)
        # Calculate overlap: step back from end by `overlap` characters worth of sentences
        overlap_len = 0
        next_start = i
        for j in range(i - 1, start, -1):
            overlap_len += len(sentences[j])
            if overlap_len >= overlap:
                next_start = j
                break
        start = max(start + 1, next_start)
    return out


def _extract_pdf_bytes_pdfminer(b: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        from pdfminer.layout import LAParams  # type: ignore
        laparams = LAParams(char_margin=2.0, line_margin=0.2, word_margin=0.3)
        bio = io.BytesIO(b)
        text = extract_text(bio, laparams=laparams) or ""
        return text
    except Exception:
        return ""


def _extract_pdf_bytes(b: bytes) -> str:
    # Try pdfminer first for better spacing
    text = _extract_pdf_bytes_pdfminer(b)
    if text and text.strip():
        return text
    try:
        reader = PdfReader(io.BytesIO(b))
        parts: List[str] = []
        for p in reader.pages:
            t = p.extract_text() or ""
            parts.append(t)
        return "\n".join(parts)
    except Exception:
        return ""


def _normalize_text(text: str) -> str:
    try:
        t = text.replace("\r\n", "\n").replace("\r", "\n")
        # Fix hyphenation across line breaks
        t = re.sub(r"-\s*\n\s*", "", t)
        # Collapse multiple newlines
        t = re.sub(r"\n+", "\n", t)
        # Collapse excessive spaces/tabs
        t = re.sub(r"[ \t]+", " ", t)
        # Convert newlines to spaces
        t = t.replace("\n", " ")
        # Final space collapse
        t = re.sub(r"\s{2,}", " ", t)
        return t.strip()
    except Exception:
        return text


@app.post("/ingest/file")
async def ingest_file(files: List[UploadFile] = File(...), chunk_size: int = 1000, overlap: int = 200, collection: Optional[str] = None):
    try:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        for f in files:
            content = await f.read()
            name = f.filename or "uploaded"
            if name.lower().endswith(".pdf"):
                text = _normalize_text(_extract_pdf_bytes(content))
            else:
                try:
                    text = _normalize_text(content.decode("utf-8", "ignore"))
                except Exception:
                    text = ""
            doc_id = str(uuid.uuid4())
            chunks = _chunk_text(text, chunk_size, overlap)
            for idx, ch in enumerate(chunks):
                texts.append(ch)
                metas.append({"source": name, "doc_id": doc_id, "chunk_id": idx})
        if not texts:
            return {"ingested": 0, "collection": collection or _vs.collection, "provider": _vs.provider}
        embeddings = _emb.embed(texts)
        if collection:
            count = _vs.index_to(collection, texts, embeddings, metas)
            coll_name = collection
        else:
            count = _vs.index(texts, embeddings, metas)
            coll_name = _vs.collection
        _invalidate_bm25(coll_name)
        return {"ingested": count, "collection": coll_name, "provider": _vs.provider, "documents": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest_file_failed: {e}")


class URLIngestRequest(BaseModel):
    urls: List[str]
    chunk_size: int = 1000
    overlap: int = 200
    collection: Optional[str] = None


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

def _fetch_url_text(url: str, max_retries: int = 3) -> str:
    """Fetch URL content with retry logic for slow government sites."""
    import time
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Create session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=2,  # 2, 4, 8 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    last_error = None
    for attempt in range(max_retries):
        try:
            # Use tuple timeout: (connect_timeout, read_timeout)
            # Government PDFs can be very slow - allow up to 180s read
            # Disable SSL verification for government sites with cert issues
            r = session.get(url, timeout=(30, 180), headers=_HEADERS, stream=True, verify=False)
            r.raise_for_status()
            
            # For large files, read in chunks
            content = b""
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                content += chunk
            
            ctype = r.headers.get("content-type", "").lower()
            if "pdf" in ctype or url.lower().endswith(".pdf"):
                return _normalize_text(_extract_pdf_bytes(content))
            # Treat as text/HTML
            text = content.decode("utf-8", errors="ignore")
            # If HTML, parse
            if "html" in ctype or ("<html" in text.lower()):
                soup = BeautifulSoup(text, "html.parser")
                # Remove non-content tags
                for tag in soup(["script", "style", "noscript", "header", "nav", "footer", "aside", "form", "button"]):
                    tag.decompose()
                # Remove common UI containers by class/id keywords
                for el in soup.find_all(True):
                    cname = " ".join((el.get("class") or [])) + " " + (el.get("id") or "")
                    if any(k in cname.lower() for k in ["header", "footer", "nav", "menu", "sidebar", "cookie", "banner", "subscribe", "modal"]):
                        el.decompose()
                # Prefer main/article content if present
                candidates = []
                candidates.extend(soup.find_all("main"))
                candidates.extend(soup.find_all("article"))
                if candidates:
                    parts = [c.get_text(" ", strip=True) for c in candidates if c]
                    text = "\n".join(p for p in parts if p)
                else:
                    text = soup.get_text(" ", strip=True)
                return _normalize_text(text)
            return _normalize_text(text)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
    raise RuntimeError(f"fetch_failed after {max_retries} attempts: {last_error}")


@app.post("/ingest/url")
def ingest_url(req: URLIngestRequest):
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    errors: List[str] = []
    for u in req.urls:
        try:
            raw = _fetch_url_text(u)
            doc_id = str(uuid.uuid4())
            chunks = _chunk_text(raw, req.chunk_size, req.overlap)
            for idx, ch in enumerate(chunks):
                if ch.strip():
                    texts.append(ch)
                    metas.append({"source_url": u, "doc_id": doc_id, "chunk_id": idx})
        except Exception as e:
            errors.append(f"{u}: {e}")
    try:
        if not texts:
            msg = "; ".join(errors) if errors else "no content extracted"
            raise HTTPException(status_code=422, detail=f"0 chunks from all URLs — {msg}")
        embeddings = _emb.embed(texts)
        if req.collection:
            count = _vs.index_to(req.collection, texts, embeddings, metas)
            coll_name = req.collection
        else:
            count = _vs.index(texts, embeddings, metas)
            coll_name = _vs.collection
        _invalidate_bm25(coll_name)
        return {"ingested": count, "collection": coll_name, "provider": _vs.provider, "urls": len(req.urls) - len(errors), "errors": errors}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest_url_failed: {e}")


@app.get("/query")
@limiter.limit(_RATE_LIMIT_QUERY)
def query(request: Request, q: str = "hello", k: int = 4, collection: Optional[str] = None, max_distance: Optional[float] = None, style: str = "concise"):
    logger.info(f"Query received: q='{q[:50]}...', collection={collection}, k={k}, max_distance={max_distance}, style={style}")
    try:
        coll_name = collection or _vs.collection
        fetch_k = min(k * 5, 40)
        results = _hybrid_search(q, coll_name, k=k, fetch_k=fetch_k)
        # Deduplicate by doc_id+chunk_id (same chunk ingested multiple times)
        seen: set = set()
        deduped = []
        for r in results:
            md = r.get("metadata") or {}
            key = (md.get("doc_id"), md.get("chunk_id"), (r.get("document") or "")[:100])
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        results = deduped
        # Filter/sort results by distance if requested
        if max_distance is not None:
            results = [r for r in results if r.get("distance") is None or r.get("distance") <= max_distance]
        results = sorted(results, key=lambda r: (r.get("distance") is None, r.get("distance") or 0.0))
        context_snippets = [r.get("document", "") for r in results if r.get("document")]
        context = "\n\n---\n\n".join(context_snippets[:k]) if context_snippets else "(no context retrieved)"
        # Style instructions
        style_map = {
            "concise": "Answer in 1-3 sentences.",
            "bulleted": "Answer with short bullet points only.",
            "detailed": "Provide a detailed but focused answer.",
            "json-list": "Return a JSON array of strings summarizing the key points.",
        }
        style_inst = style_map.get(style, style_map["concise"])
        prompt = (
            "You are a logistics intelligence assistant. Use only the provided context to answer the question. If the answer is not in the context, say you don't know.\n\n"
            f"Context:\n{context}\n\nQuestion: {q}\nInstructions: {style_inst}\nAnswer:"
        )
        answer = _llm.generate(prompt)
        citations: List[Dict[str, Any]] = []
        for r in results[:k]:
            md = r.get("metadata") or {}
            snippet = (r.get("document") or "")[:300]
            citations.append({
                "id": r.get("id"),
                "source": md.get("source") or md.get("source_url"),
                "doc_id": md.get("doc_id"),
                "chunk_id": md.get("chunk_id"),
                "distance": r.get("distance"),
                "snippet": snippet,
            })
        result = {
            "query": q,
            "answer": answer,
            "retrieved": len(context_snippets),
            "citations": citations,
            "collection": coll_name,
            "provider": _llm.provider,
            "model": _llm.model,
            "k": k,
            "max_distance": max_distance,
            "style": style,
        }
        logger.info(f"Query completed: retrieved={len(context_snippets)}, answer_length={len(answer)}")
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"query_failed: {e}")


@app.get("/index/collections")
def index_collections():
    try:
        items = _vs.list_collections()
        return {"collections": items, "default": _vs.collection}
    except Exception as e:
        logger.error(f"list_collections failed: {e}")
        raise HTTPException(status_code=500, detail=f"list_collections_failed: {e}")


@app.get("/index/collections/{name}/stats")
def collection_stats(name: str):
    """Get statistics for a specific collection."""
    try:
        if _vs.provider == "chromadb" and _vs._chroma:
            coll = _vs.get_collection(name)
            if coll:
                count = coll.count()
                metadata = getattr(coll, "metadata", {})
                return {
                    "name": name,
                    "count": count,
                    "metadata": metadata,
                    "provider": _vs.provider,
                }
        return {"name": name, "count": 0, "provider": _vs.provider}
    except Exception as e:
        logger.error(f"collection_stats failed for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"collection_stats_failed: {e}")


@app.delete("/index/collections/{name}")
def delete_collection(name: str):
    """Delete a collection permanently."""
    try:
        if name == _vs.collection:
            raise HTTPException(status_code=400, detail="Cannot delete default collection")
        if _vs.provider == "chromadb" and _vs._chroma:
            _vs._chroma.delete_collection(name)
            logger.info(f"Deleted collection: {name}")
            return {"deleted": name, "status": "ok"}
        raise HTTPException(status_code=404, detail="Collection not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"delete_collection failed for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"delete_collection_failed: {e}")


@app.post("/index/collections/{name}/reset")
def reset_collection(name: str):
    """Reset a collection (delete and recreate)."""
    try:
        if _vs.provider == "chromadb" and _vs._chroma:
            try:
                _vs._chroma.delete_collection(name)
            except Exception:
                pass
            _vs._chroma.get_or_create_collection(name)
            logger.info(f"Reset collection: {name}")
            return {"reset": name, "status": "ok"}
        raise HTTPException(status_code=404, detail="Collection not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"reset_collection failed for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"reset_collection_failed: {e}")


# ─────────────────────────────────────────────────────────────
# Agent endpoints — wire real LLM + vector search into agents
# ─────────────────────────────────────────────────────────────

import sys as _sys
import os as _os
_agents_src = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../../../../glih-agents/src"))
if _agents_src not in _sys.path:
    _sys.path.insert(0, _agents_src)

from glih_agents.anomaly_responder import AnomalyResponder
from glih_agents.route_advisor import RouteAdvisor
from glih_agents.customer_notifier import CustomerNotifier
from glih_agents.ops_summarizer import OpsSummarizer


def _make_vector_search_fn(run_id: str = None):
    """Return a closure that searches the vector store, emitting progress events."""
    def _search(query: str, collection: str = "lineage-sops", k: int = 4) -> List[Dict[str, Any]]:
        if run_id:
            emit_progress(run_id, "retrieval", f"Searching '{collection}' → \"{query[:60]}\"")
        emb = _emb.embed([query])[0]
        results = _vs.search_in(collection, emb, k=k)
        if run_id:
            emit_progress(run_id, "retrieval_done", f"Retrieved {len(results)} document chunks from {collection}", {"count": len(results), "collection": collection})
        return results
    return _search


def _make_llm_fn(run_id: str = None):
    """Return a closure that calls the LLM, emitting progress events."""
    def _generate(prompt: str) -> str:
        if run_id:
            emit_progress(run_id, "llm_call", f"Calling {_llm.provider}/{_llm.model} ({len(prompt)} char prompt)…")
        result = _llm.generate(prompt)
        if run_id:
            emit_progress(run_id, "llm_done", f"LLM response received ({len(result)} chars)", {"chars": len(result)})
        return result
    return _generate


@app.get("/agents/progress/{run_id}")
def get_agent_progress(run_id: str):
    """Poll this endpoint to get live progress events for an agent run."""
    with _progress_lock:
        data = _progress_store.get(run_id)
    if not data:
        raise HTTPException(status_code=404, detail="run_id not found")
    return data


class AnomalyRequest(BaseModel):
    shipment_id: str
    temperature_c: float
    product_type: Optional[str] = "Dairy"
    threshold_min_c: Optional[float] = 0.0
    threshold_max_c: Optional[float] = 4.0
    location: Optional[str] = "Unknown"
    breach_duration_min: Optional[int] = 0


def _run_anomaly_background(run_id: str, req: AnomalyRequest):
    start = time.time()
    try:
        emit_progress(run_id, "init", f"AnomalyResponder started for shipment {req.shipment_id}")
        emit_progress(run_id, "analyze", f"Analyzing temp {req.temperature_c}°C for {req.product_type} at {req.location}")
        agent = AnomalyResponder(_cfg)
        event = {
            "shipment_id": req.shipment_id,
            "temperature": req.temperature_c,
            "product_type": req.product_type,
            "location": req.location,
            "duration_minutes": req.breach_duration_min,
        }
        result = agent.respond_to_anomaly(event, _make_vector_search_fn(run_id), _make_llm_fn(run_id))
        duration_ms = int((time.time() - start) * 1000)
        emit_progress(run_id, "complete", f"AnomalyResponder finished in {duration_ms}ms", {"duration_ms": duration_ms})
        _complete_run(run_id, result={"run_id": run_id, "agent_name": "AnomalyResponder", "status": "success", "result": result, "duration_ms": duration_ms})
    except Exception as e:
        logger.error(f"anomaly_agent failed: {e}")
        emit_progress(run_id, "error", str(e))
        _complete_run(run_id, error=str(e))


@app.post("/agents/anomaly")
@limiter.limit(_RATE_LIMIT_AGENTS)
def run_anomaly_agent(request: Request, req: AnomalyRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    _init_run(run_id)
    emit_progress(run_id, "queued", f"AnomalyResponder queued for {req.shipment_id}")
    background_tasks.add_task(_run_anomaly_background, run_id, req)
    return {"run_id": run_id, "status": "running", "agent_name": "AnomalyResponder"}


class RouteRequest(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    product_type: Optional[str] = "Seafood"
    start_time: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = {}


def _run_route_background(run_id: str, req: RouteRequest):
    start = time.time()
    try:
        emit_progress(run_id, "init", f"RouteAdvisor started for {req.shipment_id}")
        emit_progress(run_id, "analyze", f"Evaluating route: {req.origin} → {req.destination} ({req.product_type})")
        agent = RouteAdvisor(_cfg)
        from datetime import datetime as _dt
        request_data = {
            "shipment_id": req.shipment_id,
            "origin": req.origin,
            "destination": req.destination,
            "product_type": req.product_type,
            "start_time": req.start_time or _dt.now().isoformat(),
            "constraints": req.constraints or {},
        }
        result = agent.advise_route(request_data, _make_vector_search_fn(run_id), _make_llm_fn(run_id))
        duration_ms = int((time.time() - start) * 1000)
        emit_progress(run_id, "complete", f"RouteAdvisor finished in {duration_ms}ms", {"duration_ms": duration_ms})
        _complete_run(run_id, result={"run_id": run_id, "agent_name": "RouteAdvisor", "status": "success", "result": result, "duration_ms": duration_ms})
    except Exception as e:
        logger.error(f"route_agent failed: {e}")
        emit_progress(run_id, "error", str(e))
        _complete_run(run_id, error=str(e))


@app.post("/agents/route")
@limiter.limit(_RATE_LIMIT_AGENTS)
def run_route_agent(request: Request, req: RouteRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    _init_run(run_id)
    emit_progress(run_id, "queued", f"RouteAdvisor queued for {req.shipment_id}")
    background_tasks.add_task(_run_route_background, run_id, req)
    return {"run_id": run_id, "status": "running", "agent_name": "RouteAdvisor"}


class NotifyRequest(BaseModel):
    shipment_id: str
    customer_id: str
    notification_type: str
    severity: Optional[str] = "low"
    details: Optional[Dict[str, Any]] = {}
    dispatcher_name: Optional[str] = "John Martinez"  # Default dispatcher
    dispatcher_title: Optional[str] = "Cold Chain Operations Dispatcher"


def _run_notify_background(run_id: str, req: NotifyRequest):
    start = time.time()
    try:
        emit_progress(run_id, "init", f"CustomerNotifier started for {req.customer_id}")
        emit_progress(run_id, "compose", f"Composing {req.notification_type} notification (severity: {req.severity})")
        agent = CustomerNotifier(_cfg)
        request_data = {
            "shipment_id": req.shipment_id,
            "customer_id": req.customer_id,
            "type": req.notification_type,
            "notification_type": req.notification_type,
            "severity": req.severity,
            "details": req.details or {},
            "dispatcher_name": req.dispatcher_name,
            "dispatcher_title": req.dispatcher_title,
        }
        result = agent.notify_customer(request_data, _make_llm_fn(run_id))
        duration_ms = int((time.time() - start) * 1000)
        emit_progress(run_id, "complete", f"CustomerNotifier finished in {duration_ms}ms", {"duration_ms": duration_ms})
        _complete_run(run_id, result={"run_id": run_id, "agent_name": "CustomerNotifier", "status": "success", "result": result, "duration_ms": duration_ms})
    except Exception as e:
        logger.error(f"notify_agent failed: {e}")
        emit_progress(run_id, "error", str(e))
        _complete_run(run_id, error=str(e))


@app.post("/agents/notify")
@limiter.limit(_RATE_LIMIT_AGENTS)
def run_notify_agent(request: Request, req: NotifyRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    _init_run(run_id)
    emit_progress(run_id, "queued", f"CustomerNotifier queued for {req.customer_id}")
    background_tasks.add_task(_run_notify_background, run_id, req)
    return {"run_id": run_id, "status": "running", "agent_name": "CustomerNotifier"}


class OpsSummaryRequest(BaseModel):
    time_window: Optional[str] = "24h"
    facility: Optional[str] = "all"


def _run_ops_summary_background(run_id: str, req: OpsSummaryRequest):
    start = time.time()
    try:
        emit_progress(run_id, "init", f"OpsSummarizer started — window: {req.time_window}, facility: {req.facility}")
        emit_progress(run_id, "aggregate", f"Aggregating operational events for the last {req.time_window}")
        agent = OpsSummarizer(_cfg)
        result = agent.summarize_ops(req.time_window, _make_vector_search_fn(run_id), _make_llm_fn(run_id))
        duration_ms = int((time.time() - start) * 1000)
        emit_progress(run_id, "complete", f"OpsSummarizer finished in {duration_ms}ms", {"duration_ms": duration_ms})
        _complete_run(run_id, result={"run_id": run_id, "agent_name": "OpsSummarizer", "status": "success", "result": result, "duration_ms": duration_ms})
    except Exception as e:
        logger.error(f"ops_summary_agent failed: {e}")
        emit_progress(run_id, "error", str(e))
        _complete_run(run_id, error=str(e))


@app.post("/agents/ops-summary")
@limiter.limit(_RATE_LIMIT_AGENTS)
def run_ops_summary_agent(request: Request, req: OpsSummaryRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    _init_run(run_id)
    emit_progress(run_id, "queued", f"OpsSummarizer queued — {req.time_window} window")
    background_tasks.add_task(_run_ops_summary_background, run_id, req)
    return {"run_id": run_id, "status": "running", "agent_name": "OpsSummarizer"}


# ===========================================================================
# Dispatcher Authentication
# ===========================================================================

@app.post("/auth/login")
def login(req: DispatcherLogin):
    """Login admin and return session token."""
    result = admin_login(req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return result


@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Logout admin and invalidate session."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token")
    
    token = authorization.replace("Bearer ", "")
    admin_logout(token)
    return {"status": "logged_out"}


@app.get("/auth/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current logged-in admin info."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token")
    
    token = authorization.replace("Bearer ", "")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {"user": user}


@app.get("/dispatchers/{dispatcher_id}")
def get_dispatcher(dispatcher_id: str):
    """Get a specific dispatcher by ID."""
    dispatcher = get_dispatcher_by_id(dispatcher_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")
    return {"dispatcher": dispatcher}


@app.get("/dispatchers")
def list_dispatchers():
    """List all dispatchers."""
    return {"dispatchers": get_all_dispatchers()}


@app.post("/dispatchers")
def add_dispatcher(req: DispatcherCreate):
    """Create a new dispatcher account."""
    try:
        dispatcher = create_dispatcher(req)
        return {"status": "created", "dispatcher": dispatcher}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================================================
# Settings & MCP Connector Management
# ===========================================================================

class MCPConnectorConfig(BaseModel):
    """Configuration for an MCP connector"""
    enabled: bool = True
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    endpoint: Optional[str] = None
    mqtt_broker: Optional[str] = None
    mqtt_port: Optional[int] = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    api_endpoint: Optional[str] = None
    mode: Optional[str] = "demo"
    provider: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    """Request to update settings"""
    section: str  # e.g., "mcp.connectors.gps_trace"
    values: Dict[str, Any]


@app.get("/settings")
def get_settings():
    """Get current settings (sanitized - no secrets exposed)"""
    try:
        cfg = load_config()
        # Sanitize sensitive fields
        safe_cfg = sanitize_config(cfg)
        return {"settings": safe_cfg}
    except Exception as e:
        logger.error(f"get_settings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/settings/mcp")
def get_mcp_settings():
    """Get MCP connector settings with status"""
    try:
        cfg = load_config()
        mcp_cfg = cfg.get("mcp", {})
        connectors = mcp_cfg.get("connectors", {})
        
        # Build connector status
        connector_status = []
        for name, config in connectors.items():
            # Check if API key/token is configured
            has_credentials = bool(
                config.get("api_key") or 
                config.get("api_token") or 
                config.get("mqtt_broker") or
                config.get("api_endpoint")
            )
            connector_status.append({
                "id": name,
                "name": _format_connector_name(name),
                "enabled": config.get("enabled", False),
                "configured": has_credentials,
                "mode": "real" if has_credentials else "demo",
                "description": config.get("description", ""),
                "endpoint": config.get("endpoint", config.get("api_endpoint", "")),
            })
        
        return {
            "enabled": mcp_cfg.get("enabled", False),
            "connectors": connector_status,
            "timeout_seconds": mcp_cfg.get("timeout_seconds", 30),
        }
    except Exception as e:
        logger.error(f"get_mcp_settings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _format_connector_name(key: str) -> str:
    """Format connector key to display name"""
    names = {
        "gps_trace": "GPS-Trace (Truck Tracking)",
        "openweathermap": "OpenWeatherMap (Weather)",
        "iot": "Lineage IoT Sensors",
        "traffic": "Traffic & Routing",
    }
    return names.get(key, key.replace("_", " ").title())


@app.put("/settings/mcp/connector/{connector_id}")
def update_mcp_connector(connector_id: str, config: MCPConnectorConfig):
    """Update a specific MCP connector configuration"""
    try:
        cfg = load_config()
        
        # Ensure mcp.connectors exists
        if "mcp" not in cfg:
            cfg["mcp"] = {}
        if "connectors" not in cfg["mcp"]:
            cfg["mcp"]["connectors"] = {}
        if connector_id not in cfg["mcp"]["connectors"]:
            cfg["mcp"]["connectors"][connector_id] = {}
        
        # Update only non-None values
        connector_cfg = cfg["mcp"]["connectors"][connector_id]
        update_data = config.model_dump(exclude_none=True)
        
        for key, value in update_data.items():
            if value is not None:
                connector_cfg[key] = value
        
        # Save config
        save_config(cfg)
        logger.info(f"Updated MCP connector: {connector_id}")
        
        return {
            "status": "updated",
            "connector_id": connector_id,
            "configured": bool(
                connector_cfg.get("api_key") or 
                connector_cfg.get("api_token") or
                connector_cfg.get("mqtt_broker") or
                connector_cfg.get("api_endpoint")
            )
        }
    except Exception as e:
        logger.error(f"update_mcp_connector failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/mcp/test/{connector_id}")
async def test_mcp_connector(connector_id: str):
    """Test connection to an MCP connector"""
    try:
        cfg = load_config()
        connector_cfg = cfg.get("mcp", {}).get("connectors", {}).get(connector_id, {})
        
        if not connector_cfg:
            return {"status": "not_configured", "message": f"Connector {connector_id} not found"}
        
        # Import MCP clients
        from ..mcp_client import GPSTraceMCPClient, OpenWeatherMCPClient, LineageIoTMCPClient
        
        result = {"connector_id": connector_id, "status": "unknown"}
        
        if connector_id == "gps_trace":
            client = GPSTraceMCPClient(api_token=connector_cfg.get("api_token"))
            if not client.is_configured:
                result = {"status": "demo", "message": "No API token configured - running in demo mode"}
            else:
                connected = await client.connect()
                await client.disconnect()
                result = {"status": "connected" if connected else "failed", 
                         "message": "Connection successful" if connected else "Failed to connect"}
        
        elif connector_id == "openweathermap":
            client = OpenWeatherMCPClient(api_key=connector_cfg.get("api_key"))
            if not client.is_configured:
                result = {"status": "demo", "message": "No API key configured - running in demo mode"}
            else:
                connected = await client.connect()
                await client.disconnect()
                result = {"status": "connected" if connected else "failed",
                         "message": "Connection successful" if connected else "Failed to connect - check API key"}
        
        elif connector_id == "iot":
            client = LineageIoTMCPClient(
                mqtt_broker=connector_cfg.get("mqtt_broker"),
                api_endpoint=connector_cfg.get("api_endpoint"),
                api_key=connector_cfg.get("api_key")
            )
            if not client.is_configured:
                result = {"status": "demo", "message": "No broker/endpoint configured - running in demo mode"}
            else:
                connected = await client.connect()
                await client.disconnect()
                result = {"status": "connected" if connected else "failed",
                         "message": "Connection successful" if connected else "Failed to connect"}
        
        else:
            result = {"status": "unknown", "message": f"Unknown connector: {connector_id}"}
        
        return result
    except Exception as e:
        logger.error(f"test_mcp_connector failed: {e}")
        return {"status": "error", "message": str(e)}


# ===========================================================================
# MCP Server Endpoints (Custom Lineage IoT)
# ===========================================================================

# Lazy-initialize MCP server
_mcp_server = None
_mcp_server_initialized = False

async def _get_mcp_server():
    global _mcp_server, _mcp_server_initialized
    if _mcp_server is None:
        from ..mcp_server import get_mcp_server
        # Check if IoT is in demo mode
        iot_cfg = _cfg.get("mcp", {}).get("connectors", {}).get("iot", {})
        demo_mode = iot_cfg.get("mode", "demo") == "demo" or not (
            iot_cfg.get("mqtt_broker") or iot_cfg.get("api_endpoint")
        )
        _mcp_server = get_mcp_server(demo_mode=demo_mode)
    
    if not _mcp_server_initialized:
        await _mcp_server.initialize()
        _mcp_server_initialized = True
    
    return _mcp_server


@app.get("/mcp/tools")
async def get_mcp_tools():
    """List available MCP tools"""
    server = await _get_mcp_server()
    return {"tools": server.get_tools(), "demo_mode": server.demo_mode}


@app.post("/mcp/call/{tool_name}")
async def call_mcp_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None):
    """Call an MCP tool"""
    try:
        server = await _get_mcp_server()
        result = await server.call_tool(tool_name, arguments or {})
        return {"tool": tool_name, "result": result, "demo_mode": server.demo_mode}
    except Exception as e:
        logger.error(f"MCP tool call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/trucks")
async def get_trucks():
    """Get all tracked trucks"""
    server = await _get_mcp_server()
    trucks = await server.get_all_trucks()
    return {"trucks": trucks, "count": len(trucks), "demo_mode": server.demo_mode}


@app.get("/mcp/trucks/{truck_id}")
async def get_truck(truck_id: str):
    """Get specific truck status"""
    server = await _get_mcp_server()
    truck = await server.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail=f"Truck {truck_id} not found")
    return {"truck": truck, "demo_mode": server.demo_mode}


@app.get("/mcp/sensors")
async def get_sensors(sensor_type: Optional[str] = None, location: Optional[str] = None):
    """Get IoT sensor readings"""
    server = await _get_mcp_server()
    sensors = await server.get_all_sensors(sensor_type, location)
    return {"sensors": sensors, "count": len(sensors), "demo_mode": server.demo_mode}


@app.get("/mcp/alerts/temperature")
async def get_temperature_alerts(threshold: float = 2.0):
    """Get temperature alerts"""
    server = await _get_mcp_server()
    alerts = await server.get_temperature_alerts(threshold)
    return {"alerts": alerts, "count": len(alerts), "demo_mode": server.demo_mode}


@app.get("/mcp/facility/{facility}")
async def get_facility_status(facility: str):
    """Get facility status"""
    server = await _get_mcp_server()
    status = await server.get_facility_status(facility)
    return {"facility": status, "demo_mode": server.demo_mode}


# ===========================================================================
# Fleet / Truck Management
# ===========================================================================

import json
from pathlib import Path

# Store trucks in a JSON file for persistence
TRUCKS_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "trucks.json"
TRUCKS_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_trucks() -> List[Dict[str, Any]]:
    """Load trucks from JSON file"""
    if TRUCKS_FILE.exists():
        try:
            return json.loads(TRUCKS_FILE.read_text())
        except:
            return []
    return []

def _save_trucks(trucks: List[Dict[str, Any]]):
    """Save trucks to JSON file"""
    TRUCKS_FILE.write_text(json.dumps(trucks, indent=2, default=str))


class TruckCreate(BaseModel):
    """Model for creating a truck"""
    truck_id: str
    driver_name: str
    device_id: Optional[str] = None
    license_plate: Optional[str] = None
    reefer_equipped: bool = True
    home_facility: Optional[str] = None
    notes: Optional[str] = None


class TruckUpdate(BaseModel):
    """Model for updating a truck"""
    driver_name: Optional[str] = None
    device_id: Optional[str] = None
    license_plate: Optional[str] = None
    reefer_equipped: Optional[bool] = None
    home_facility: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class BulkTruckImport(BaseModel):
    """Model for bulk importing trucks"""
    trucks: List[TruckCreate]


@app.get("/fleet/trucks")
async def list_fleet_trucks(
    active_only: bool = True,
    facility: Optional[str] = None,
    include_live_data: bool = True
):
    """List all trucks in the fleet with optional live GPS data"""
    trucks = _load_trucks()
    
    # Filter by active status
    if active_only:
        trucks = [t for t in trucks if t.get("active", True)]
    
    # Filter by facility
    if facility:
        trucks = [t for t in trucks if t.get("home_facility", "").lower() == facility.lower()]
    
    # Merge with live GPS data if available
    if include_live_data:
        try:
            server = await _get_mcp_server()
            live_trucks = await server.get_all_trucks()
            live_map = {t["truck_id"]: t for t in live_trucks}
            
            for truck in trucks:
                if truck["truck_id"] in live_map:
                    live = live_map[truck["truck_id"]]
                    truck["live_data"] = {
                        "lat": live.get("lat"),
                        "lon": live.get("lon"),
                        "speed_kmh": live.get("speed_kmh"),
                        "reefer_temp_c": live.get("reefer_temp_c"),
                        "status": live.get("status"),
                        "last_updated": live.get("last_updated"),
                    }
        except Exception as e:
            logger.warning(f"Could not fetch live truck data: {e}")
    
    return {"trucks": trucks, "count": len(trucks)}


@app.post("/fleet/trucks")
async def create_fleet_truck(truck: TruckCreate):
    """Register a new truck in the fleet"""
    trucks = _load_trucks()
    
    # Check for duplicate truck_id
    if any(t["truck_id"] == truck.truck_id for t in trucks):
        raise HTTPException(status_code=400, detail=f"Truck {truck.truck_id} already exists")
    
    new_truck = {
        **truck.dict(),
        "active": True,
        "created_at": datetime.now().isoformat(),
        "source": "manual",
    }
    trucks.append(new_truck)
    _save_trucks(trucks)
    
    return {"message": "Truck created", "truck": new_truck}


@app.put("/fleet/trucks/{truck_id}")
async def update_fleet_truck(truck_id: str, update: TruckUpdate):
    """Update a truck's information"""
    trucks = _load_trucks()
    
    for i, t in enumerate(trucks):
        if t["truck_id"] == truck_id:
            for key, value in update.dict(exclude_none=True).items():
                trucks[i][key] = value
            trucks[i]["updated_at"] = datetime.now().isoformat()
            _save_trucks(trucks)
            return {"message": "Truck updated", "truck": trucks[i]}
    
    raise HTTPException(status_code=404, detail=f"Truck {truck_id} not found")


@app.delete("/fleet/trucks/{truck_id}")
async def delete_fleet_truck(truck_id: str, hard_delete: bool = False):
    """Delete or deactivate a truck"""
    trucks = _load_trucks()
    
    for i, t in enumerate(trucks):
        if t["truck_id"] == truck_id:
            if hard_delete:
                trucks.pop(i)
                _save_trucks(trucks)
                return {"message": f"Truck {truck_id} permanently deleted"}
            else:
                trucks[i]["active"] = False
                trucks[i]["deactivated_at"] = datetime.now().isoformat()
                _save_trucks(trucks)
                return {"message": f"Truck {truck_id} deactivated"}
    
    raise HTTPException(status_code=404, detail=f"Truck {truck_id} not found")


@app.post("/fleet/trucks/bulk")
async def bulk_import_trucks(data: BulkTruckImport):
    """Bulk import trucks from CSV/Excel data"""
    trucks = _load_trucks()
    existing_ids = {t["truck_id"] for t in trucks}
    
    created = 0
    skipped = 0
    errors = []
    
    for truck in data.trucks:
        if truck.truck_id in existing_ids:
            skipped += 1
            continue
        try:
            new_truck = {
                **truck.dict(),
                "active": True,
                "created_at": datetime.now().isoformat(),
                "source": "bulk_import",
            }
            trucks.append(new_truck)
            existing_ids.add(truck.truck_id)
            created += 1
        except Exception as e:
            errors.append({"truck_id": truck.truck_id, "error": str(e)})
    
    _save_trucks(trucks)
    
    return {
        "message": f"Bulk import complete",
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "total": len(trucks),
    }


@app.post("/fleet/sync/gps-trace")
async def sync_gps_trace_trucks():
    """Sync trucks from GPS-Trace API"""
    # Check if GPS-Trace is configured
    gps_cfg = _cfg.get("mcp", {}).get("connectors", {}).get("gps_trace", {})
    if not gps_cfg.get("api_token"):
        return {"status": "skipped", "message": "GPS-Trace API token not configured"}
    
    try:
        from ..mcp_client import get_mcp_manager
        manager = get_mcp_manager()
        
        # Fetch trucks from GPS-Trace
        gps_trucks = await manager.gps_trace.get_units()
        
        if not gps_trucks:
            return {"status": "no_data", "message": "No trucks found in GPS-Trace"}
        
        # Merge with existing trucks
        trucks = _load_trucks()
        existing_ids = {t["truck_id"]: i for i, t in enumerate(trucks)}
        
        synced = 0
        added = 0
        
        for gt in gps_trucks:
            truck_id = gt.get("unit_id") or gt.get("id")
            if not truck_id:
                continue
            
            if truck_id in existing_ids:
                # Update existing truck with GPS data
                idx = existing_ids[truck_id]
                trucks[idx]["device_id"] = gt.get("device_id")
                trucks[idx]["gps_trace_synced"] = datetime.now().isoformat()
                synced += 1
            else:
                # Add new truck from GPS-Trace
                trucks.append({
                    "truck_id": truck_id,
                    "driver_name": gt.get("driver", "Unknown"),
                    "device_id": gt.get("device_id"),
                    "license_plate": gt.get("plate"),
                    "reefer_equipped": True,
                    "active": True,
                    "created_at": datetime.now().isoformat(),
                    "source": "gps_trace",
                })
                added += 1
        
        _save_trucks(trucks)
        
        return {
            "status": "success",
            "synced": synced,
            "added": added,
            "total": len(trucks),
        }
    except Exception as e:
        logger.error(f"GPS-Trace sync failed: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/fleet/stats")
async def get_fleet_stats():
    """Get fleet statistics"""
    trucks = _load_trucks()
    active = [t for t in trucks if t.get("active", True)]
    
    # Get live status counts
    try:
        server = await _get_mcp_server()
        live_trucks = await server.get_all_trucks()
        in_transit = sum(1 for t in live_trucks if t.get("status") == "in_transit")
        idle = sum(1 for t in live_trucks if t.get("status") == "idle")
        offline = len(active) - len(live_trucks)
    except:
        in_transit = 0
        idle = 0
        offline = len(active)
    
    # Count by facility
    by_facility = {}
    for t in active:
        fac = t.get("home_facility", "Unassigned")
        by_facility[fac] = by_facility.get(fac, 0) + 1
    
    return {
        "total": len(trucks),
        "active": len(active),
        "inactive": len(trucks) - len(active),
        "in_transit": in_transit,
        "idle": idle,
        "offline": offline,
        "by_facility": by_facility,
        "reefer_equipped": sum(1 for t in active if t.get("reefer_equipped", True)),
    }
