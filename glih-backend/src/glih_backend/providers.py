from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List
import json

import requests
import time

try:
    from openai import OpenAI  # openai >= 1.x
except Exception:  # pragma: no cover - allow import-time flexibility
    OpenAI = None  # type: ignore

# Optional providers
try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover
    anthropic = None  # type: ignore

try:
    from mistralai.client import MistralClient  # type: ignore
    from mistralai.models.chat_completion import ChatMessage  # type: ignore
except Exception:  # pragma: no cover
    MistralClient = None  # type: ignore
    ChatMessage = None  # type: ignore

try:
    # chromadb >= 0.5 has PersistentClient
    from chromadb import PersistentClient as _ChromaPersistentClient  # type: ignore
    _HAVE_PERSISTENT = True
except Exception:  # chromadb < 0.5 fallback
    _HAVE_PERSISTENT = False
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore


class EmbeddingsProvider:
    def __init__(self, provider: str, model: str | None = None) -> None:
        self.provider = provider
        self.model = model
        self._openai: OpenAI | None = None
        self._mistral = None
        if self.provider == "openai" and OpenAI is not None:
            self._openai = OpenAI()
        elif self.provider == "mistral" and MistralClient is not None:
            ms_key = os.getenv("MISTRAL_API_KEY")
            if ms_key:
                self._mistral = MistralClient(api_key=ms_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "openai" and self._openai is not None:
            model = self.model or "text-embedding-3-small"
            resp = self._openai.embeddings.create(model=model, input=texts)
            return [d.embedding for d in resp.data]
        if self.provider == "huggingface":
            # Use HF Inference API models endpoint (recommended) to avoid heavy local installs
            model = self.model or "sentence-transformers/all-MiniLM-L6-v2"
            token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            url = f"https://api-inference.huggingface.co/models/{model}"
            vecs: List[List[float]] = []
            for t in texts:
                r = requests.post(
                    url,
                    headers=headers,
                    json={"inputs": t, "options": {"wait_for_model": True}},
                    timeout=60,
                )
                try:
                    r.raise_for_status()
                except Exception:
                    # Try to surface helpful error body
                    raise RuntimeError(f"HF embeddings error {r.status_code}: {r.text}")
                arr = r.json()
                # Responses may be [dims] or [[dims]] depending on tokenizer
                vec = arr[0] if (isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], list)) else arr
                vecs.append([float(x) for x in vec])
            return vecs
        if self.provider == "mistral" and self._mistral is not None:
            model = self.model or "mistral-embed"
            last_err = None
            for attempt in range(3):
                try:
                    resp = self._mistral.embeddings.create(model=model, input=texts)  # type: ignore[attr-defined]
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    if attempt < 2:
                        time.sleep(0.6 * (2 ** attempt))
                        continue
            if last_err is not None:
                raise RuntimeError(f"Mistral embeddings error: {last_err}")
            vecs: List[List[float]] = []
            # Be flexible about response shape across SDK versions
            data = getattr(resp, "data", None) or getattr(resp, "embeddings", None) or []
            for item in data:
                emb = getattr(item, "embedding", None) or getattr(item, "values", None)
                if emb is None:
                    raise RuntimeError("Mistral embeddings: unexpected response format")
                vecs.append([float(x) for x in emb])
            return vecs
        # Fallback placeholder
        return [[float(len(t) % 7), 0.0, 1.0] for t in texts]


class VectorStore:
    def __init__(self, provider: str, collection: str | None = None) -> None:
        self.provider = provider
        self.collection = collection or "default"
        self._chroma = None
        self._chroma_coll = None
        if self.provider == "chromadb":
            persist_dir = os.getenv("GLIH_CHROMA_DIR", os.path.join(os.getcwd(), "data", "chroma"))
            os.makedirs(persist_dir, exist_ok=True)
            if _HAVE_PERSISTENT:
                self._chroma = _ChromaPersistentClient(path=persist_dir)
            else:
                self._chroma = chromadb.Client(Settings(persist_directory=persist_dir, anonymized_telemetry=False))  # type: ignore
            self._chroma_coll = self._chroma.get_or_create_collection(name=self.collection)

    def get_collection(self, name: str):
        if self.provider == "chromadb" and self._chroma is not None:
            return self._chroma.get_or_create_collection(name=name)
        return None

    def list_collections(self) -> List[str]:
        if self.provider == "chromadb" and self._chroma is not None:
            try:
                cols = self._chroma.list_collections()
                out: List[str] = []
                for c in cols:
                    nm = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
                    if nm:
                        out.append(nm)
                return sorted(set(out))
            except Exception:
                return [self.collection]
        return [self.collection]

    def index(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] | None = None,
    ) -> int:
        if self.provider == "chromadb" and self._chroma_coll is not None:
            n = len(texts)
            ids = [str(uuid.uuid4()) for _ in range(n)]
            # Some Chroma versions reject empty metadata dicts. If metadata is missing or empty,
            # omit the parameter entirely to avoid errors like:
            # "Expected metadata to be a non-empty dict".
            has_meta = bool(metadatas) and any(bool(m) for m in (metadatas or []))
            if has_meta:
                self._chroma_coll.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            else:
                self._chroma_coll.add(documents=texts, embeddings=embeddings, ids=ids)
            return n
        # Fallback no-op
        return len(embeddings)

    def index_to(
        self,
        collection: str,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] | None = None,
    ) -> int:
        if self.provider == "chromadb" and self._chroma is not None:
            coll = self.get_collection(collection)
            n = len(texts)
            ids = [str(uuid.uuid4()) for _ in range(n)]
            has_meta = bool(metadatas) and any(bool(m) for m in (metadatas or []))
            if has_meta:
                coll.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)  # type: ignore
            else:
                coll.add(documents=texts, embeddings=embeddings, ids=ids)  # type: ignore
            return n
        return self.index(texts, embeddings, metadatas)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if self.provider == "chromadb" and self._chroma_coll is not None:
            try:
                res = self._chroma_coll.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception:
                res = self._chroma_coll.query(query_embeddings=[query_embedding], n_results=k)
            out: List[Dict[str, Any]] = []
            docs = (res.get("documents") or [[ ]])[0]
            metas = (res.get("metadatas") or [[ ]])[0]
            ids = (res.get("ids") or [[ ]])[0]
            dists = (res.get("distances") or [[ ]])[0] if "distances" in res else [None] * len(docs)
            for i in range(len(docs)):
                out.append({
                    "id": ids[i] if i < len(ids) else None,
                    "document": docs[i],
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None,
                })
            return out
        return []

    def search_in(self, collection: str, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if self.provider == "chromadb" and self._chroma is not None:
            coll = self.get_collection(collection)
            try:
                res = coll.query(query_embeddings=[query_embedding], n_results=k, include=["documents", "metadatas", "distances"])  # type: ignore
            except Exception:
                res = coll.query(query_embeddings=[query_embedding], n_results=k)  # type: ignore
            out: List[Dict[str, Any]] = []
            docs = (res.get("documents") or [[ ]])[0]
            metas = (res.get("metadatas") or [[ ]])[0]
            ids = (res.get("ids") or [[ ]])[0]
            dists = (res.get("distances") or [[ ]])[0] if "distances" in res else [None] * len(docs)
            for i in range(len(docs)):
                out.append({
                    "id": ids[i] if i < len(ids) else None,
                    "document": docs[i],
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None,
                })
            return out
        return self.search(query_embedding, k)


class LLMProvider:
    def __init__(self, provider: str, model: str | None = None) -> None:
        self.provider = provider
        self.model = model
        self._openai: OpenAI | None = None
        self._deepseek: OpenAI | None = None
        self._anthropic = None
        self._mistral = None

        if self.provider == "openai" and OpenAI is not None:
            self._openai = OpenAI()
        elif self.provider == "deepseek" and OpenAI is not None:
            ds_key = os.getenv("DEEPSEEK_API_KEY")
            if ds_key:
                self._deepseek = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        elif self.provider == "anthropic" and anthropic is not None:
            self._anthropic = anthropic.Anthropic()
        elif self.provider == "mistral" and MistralClient is not None:
            ms_key = os.getenv("MISTRAL_API_KEY")
            if ms_key:
                self._mistral = MistralClient(api_key=ms_key)

    def generate(self, prompt: str) -> str:
        if self.provider == "openai" and self._openai is not None:
            model = self.model or "gpt-4o-mini"
            resp = self._openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for logistics intelligence."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return (resp.choices[0].message.content or "").strip()
        if self.provider == "deepseek" and self._deepseek is not None:
            model = self.model or "deepseek-chat"
            resp = self._deepseek.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for logistics intelligence."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return (resp.choices[0].message.content or "").strip()
        if self.provider == "anthropic" and self._anthropic is not None:
            model = self.model or "claude-3-sonnet-20240229"
            resp = self._anthropic.messages.create(
                model=model,
                system="You are a helpful assistant for logistics intelligence.",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            try:
                # anthropic response content is a list of blocks
                return "".join([b.text for b in (resp.content or []) if getattr(b, "text", None)])
            except Exception:
                return str(resp)
        if self.provider == "mistral":
            model = self.model or "open-mistral-7b"
            # Prefer SDK path if available
            if self._mistral is not None and ChatMessage is not None:
                last_err = None
                for attempt in range(3):
                    try:
                        resp = self._mistral.chat(
                            model=model,
                            messages=[
                                ChatMessage(role="system", content="You are a helpful assistant for logistics intelligence."),
                                ChatMessage(role="user", content=prompt),
                            ],
                            temperature=0.2,
                        )
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        if attempt < 2:
                            time.sleep(0.6 * (2 ** attempt))
                            continue
                if last_err is None:
                    try:
                        return (resp.choices[0].message.content or "").strip()
                    except Exception:
                        return str(resp)
                # Fallthrough to REST on error
            # REST fallback if SDK unavailable or errored
            ms_key = os.getenv("MISTRAL_API_KEY")
            if ms_key:
                try:
                    headers = {"Authorization": f"Bearer {ms_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant for logistics intelligence."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                    }
                    r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=30)
                    r.raise_for_status()
                    jr = r.json()
                    return (jr.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
                except Exception as e:
                    return f"[LLM:mistral/{model}] REST error: {e}"
        return f"[LLM:{self.provider}/{self.model}] Echo: {prompt}"


def make_embeddings_provider(cfg: Dict[str, Any]) -> EmbeddingsProvider:
    e = cfg.get("embeddings", {}) if isinstance(cfg, dict) else {}
    provider = e.get("provider", "openai")
    if provider == "openai":
        model = e.get("openai_model")
    elif provider == "huggingface":
        model = e.get("hf_model")
    elif provider == "mistral":
        model = e.get("mistral_model")
    else:
        model = None
    return EmbeddingsProvider(provider=provider, model=model)


def make_vector_store(cfg: Dict[str, Any]) -> VectorStore:
    v = cfg.get("vector_store", {}) if isinstance(cfg, dict) else {}
    provider = v.get("provider", "chromadb")
    collection = v.get("collection", "glih-default")
    return VectorStore(provider=provider, collection=collection)


def make_llm_provider(cfg: Dict[str, Any]) -> LLMProvider:
    l = cfg.get("llm", {}) if isinstance(cfg, dict) else {}
    provider = l.get("provider", "openai")
    model = l.get("model", "gpt-4o-mini")
    return LLMProvider(provider=provider, model=model)
