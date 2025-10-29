import os
import io
import uuid
import re
import time
import logging
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from ..config import load_config, save_config
from ..utils import sanitize_config
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

app = FastAPI(title="GLIH Backend", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration and providers at import-time for simplicity.
_cfg = load_config()
_emb = make_embeddings_provider(_cfg)
_vs = make_vector_store(_cfg)
_llm = make_llm_provider(_cfg)

logger.info(f"GLIH Backend initialized: LLM={_llm.provider}/{_llm.model}, Embeddings={_emb.provider}/{_emb.model}, VectorStore={_vs.provider}")


@app.get("/")
def root():
    return {"service": "GLIH Backend", "status": "ok", "endpoints": ["/health", "/config", "/query"]}


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
    metadatas: List[Dict[str, Any]] | None = None
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
    model: str | None = None


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
    model: str | None = None


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
    chunk_size = chunk_size if chunk_size > 0 else 1000
    overlap = overlap if overlap >= 0 else 0
    out: List[str] = []
    i = 0
    n = len(text)
    step = max(1, chunk_size - overlap)
    while i < n:
        s = text[i : i + chunk_size]
        if s.strip():
            out.append(s)
        i += step
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
        return {"ingested": count, "collection": coll_name, "provider": _vs.provider, "documents": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest_file_failed: {e}")


class URLIngestRequest(BaseModel):
    urls: List[str]
    chunk_size: int = 1000
    overlap: int = 200
    collection: Optional[str] = None


def _fetch_url_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            return _normalize_text(_extract_pdf_bytes(r.content))
        # Treat as text/HTML
        text = r.text
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
        raise RuntimeError(f"fetch_failed: {e}")


@app.post("/ingest/url")
def ingest_url(req: URLIngestRequest):
    try:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        for u in req.urls:
            raw = _fetch_url_text(u)
            doc_id = str(uuid.uuid4())
            chunks = _chunk_text(raw, req.chunk_size, req.overlap)
            for idx, ch in enumerate(chunks):
                if ch.strip():
                    texts.append(ch)
                    metas.append({"source_url": u, "doc_id": doc_id, "chunk_id": idx})
        if not texts:
            return {"ingested": 0, "collection": req.collection or _vs.collection, "provider": _vs.provider, "urls": len(req.urls)}
        embeddings = _emb.embed(texts)
        if req.collection:
            count = _vs.index_to(req.collection, texts, embeddings, metas)
            coll_name = req.collection
        else:
            count = _vs.index(texts, embeddings, metas)
            coll_name = _vs.collection
        return {"ingested": count, "collection": coll_name, "provider": _vs.provider, "urls": len(req.urls)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest_url_failed: {e}")


@app.get("/query")
def query(q: str = "hello", k: int = 4, collection: Optional[str] = None, max_distance: Optional[float] = None, style: str = "concise"):
    logger.info(f"Query received: q='{q[:50]}...', collection={collection}, k={k}, max_distance={max_distance}, style={style}")
    try:
        q_emb = _emb.embed([q])[0]
        if collection:
            results = _vs.search_in(collection, q_emb, k=k)
            coll_name = collection
        else:
            results = _vs.search(q_emb, k=k)
            coll_name = _vs.collection
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
