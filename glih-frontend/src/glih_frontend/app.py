import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("GLIH_BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="GLIH Dashboard", layout="wide")
st.title("GenAI Logistics Intelligence Hub (GLIH)")

st.caption(f"Backend: {BACKEND_URL}")

# Tabs: Ingestion | Query | Configuration | Admin
tab_ingest, tab_query, tab_config, tab_admin = st.tabs(["Ingestion", "Query", "Configuration", "Admin"])

with tab_query:
    # Select target collection for querying
    try:
        idx = requests.get(f"{BACKEND_URL}/index/collections", timeout=5).json()
        collections = idx.get("collections", [])
        default_coll = idx.get("default")
        sel_q_coll = st.selectbox(
            "Select index (collection) to query",
            collections if collections else [default_coll or "glih-default"],
            index=(collections.index(default_coll) if (default_coll in collections) else 0),
            key="query_collection",
        )
        new_q_coll = st.text_input("Or type a new collection name", value="", key="query_new_coll")
        if new_q_coll.strip():
            sel_q_coll = new_q_coll.strip()
    except Exception as e:
        sel_q_coll = st.text_input("Collection", value="glih-default", help=f"Failed to list collections: {e}", key="query_collection_fallback")

    q = st.text_input("Query", "Where is shipment TX-CHI-2025-001?")
    cc1, cc2, cc3 = st.columns([1, 1, 1])
    with cc1:
        top_k = st.number_input("Top-K", min_value=1, max_value=20, value=4, step=1, key="k")
    with cc2:
        max_dist = st.text_input("Max distance (optional)", value="", key="maxdist")
    with cc3:
        style = st.selectbox("Answer style", ["concise", "bulleted", "detailed", "json-list"], index=0, key="style")
    if st.button("Send Query"):
        try:
            params = {"q": q, "collection": sel_q_coll, "k": int(top_k), "style": style}
            if max_dist.strip():
                try:
                    params["max_distance"] = float(max_dist)
                except Exception:
                    pass
            r = requests.get(f"{BACKEND_URL}/query", params=params, timeout=20)
            res = r.json()
            st.json(res)
            try:
                st.caption(f"LLM: {res.get('provider')}/{res.get('model')} | k={res.get('k')} | max_distance={res.get('max_distance')}")
            except Exception:
                pass
            st.session_state["last_query_result"] = res
        except Exception as e:
            st.error(f"Query failed: {e}")

    with st.expander("Citations (last query)", expanded=False):
        res = st.session_state.get("last_query_result")
        if not res:
            st.info("Run a query to see citations.")
        else:
            cits = res.get("citations", [])
            if not cits:
                st.info("No citations returned.")
            else:
                for i, c in enumerate(cits, 1):
                    st.markdown(f"**[{i}]** source: {c.get('source')} | doc_id: {c.get('doc_id')} | chunk: {c.get('chunk_id')} | distance: {c.get('distance')}")
                    st.code(c.get("snippet", ""))

with tab_ingest:
    # Select target collection for ingestion
    try:
        idx = requests.get(f"{BACKEND_URL}/index/collections", timeout=5).json()
        collections = idx.get("collections", [])
        default_coll = idx.get("default")
        sel_i_coll = st.selectbox(
            "Select target index (collection) for ingestion",
            collections if collections else [default_coll or "glih-default"],
            index=(collections.index(default_coll) if (default_coll in collections) else 0),
            key="ingest_collection",
        )
        new_i_coll = st.text_input("Or type a new collection name", value="", key="ingest_new_coll")
        if new_i_coll.strip():
            sel_i_coll = new_i_coll.strip()
    except Exception as e:
        sel_i_coll = st.text_input("Collection", value="glih-default", help=f"Failed to list collections: {e}", key="ingest_collection_fallback")

    st.subheader("URL Ingestion")
    url = st.text_input("URL to ingest", placeholder="https://example.com/page-or.pdf")
    c1, c2 = st.columns(2)
    with c1:
        chunk_size = st.number_input("Chunk size (chars)", min_value=200, max_value=4000, value=1000, step=100)
    with c2:
        overlap = st.number_input("Overlap (chars)", min_value=0, max_value=1000, value=200, step=50)
    if st.button("Ingest URL"):
        if not url.strip():
            st.warning("Please enter a URL.")
        else:
            try:
                payload = {"urls": [url], "chunk_size": int(chunk_size), "overlap": int(overlap), "collection": sel_i_coll}
                r = requests.post(f"{BACKEND_URL}/ingest/url", json=payload, timeout=60)
                if r.status_code == 200:
                    st.success(r.json())
                else:
                    st.error(f"URL ingestion failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"URL ingestion failed: {e}")

    st.markdown("---")
    st.subheader("File Ingestion")
    uploads = st.file_uploader("Choose PDF or TXT files", type=["pdf", "txt"], accept_multiple_files=True)
    if st.button("Ingest Files"):
        if not uploads:
            st.warning("Please select at least one file.")
        else:
            try:
                files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in uploads]
                params = {"chunk_size": int(chunk_size), "overlap": int(overlap), "collection": sel_i_coll}
                r = requests.post(f"{BACKEND_URL}/ingest/file", params=params, files=files, timeout=120)
                if r.status_code == 200:
                    st.success(r.json())
                else:
                    st.error(f"File ingestion failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"File ingestion failed: {e}")

with tab_config:
    st.subheader("Health & Config")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Check Backend Health"):
            try:
                r = requests.get(f"{BACKEND_URL}/health", timeout=5)
                st.success(r.json())
            except Exception as e:
                st.error(f"Health check failed: {e}")
    with c2:
        if st.button("Show Backend Config"):
            try:
                r = requests.get(f"{BACKEND_URL}/config", timeout=5)
                st.json(r.json())
            except Exception as e:
                st.error(f"Config fetch failed: {e}")

    st.markdown("---")
    st.subheader("Vector Store Settings")
    
    # Vector Store Selection
    vector_stores = {
        "chromadb": "ChromaDB (Local, Persistent)",
        "faiss": "FAISS (Local, Fast)",
        "pinecone": "Pinecone (Cloud, Managed)",
        "weaviate": "Weaviate (Cloud/Self-hosted)",
        "qdrant": "Qdrant (Cloud/Self-hosted)",
        "milvus": "Milvus (Coming Soon)"
    }
    
    try:
        # Get current vector store config
        config_resp = requests.get(f"{BACKEND_URL}/config", timeout=5)
        if config_resp.status_code == 200:
            config_data = config_resp.json()
            current_vs = config_data.get("vector_store", {}).get("provider", "chromadb")
        else:
            current_vs = "chromadb"
    except:
        current_vs = "chromadb"
    
    vs_options = list(vector_stores.keys())
    vs_index = vs_options.index(current_vs) if current_vs in vs_options else 0
    
    col_vs1, col_vs2 = st.columns([2, 1])
    with col_vs1:
        selected_vs = st.selectbox(
            "Select Vector Database",
            vs_options,
            index=vs_index,
            format_func=lambda x: vector_stores[x],
            key="vector_store_select",
            help="Choose where to store your document embeddings"
        )
    
    # Show info about selected vector store
    vs_info = {
        "chromadb": "✅ **Local storage** - No setup required. Data stored in `data/chromadb/`",
        "faiss": "✅ **Local storage** - Fast similarity search. Data stored in `data/faiss/`",
        "pinecone": "☁️ **Cloud managed** - Requires API key. Set `PINECONE_API_KEY` in .env",
        "weaviate": "🔧 **Requires setup** - Cloud or self-hosted. Configure URL and API key in `config/glih.toml`",
        "qdrant": "🔧 **Requires setup** - Cloud or self-hosted. Configure URL and API key in `config/glih.toml`",
        "milvus": "🚧 **Coming soon** - Enterprise-grade vector database"
    }
    
    st.info(vs_info.get(selected_vs, ""))
    
    if selected_vs != current_vs:
        st.warning(f"⚠️ To switch from **{current_vs}** to **{selected_vs}**, update `config/glih.toml` and restart backend:")
        st.code(f'[vector_store]\nprovider = "{selected_vs}"', language="toml")
    else:
        st.success(f"✅ Currently using: **{vector_stores[current_vs]}**")
    
    st.markdown("---")
    st.subheader("LLM Settings")
    try:
        cur = requests.get(f"{BACKEND_URL}/llm/current", timeout=5).json()
        providers = cur.get("supported_providers", ["openai", "deepseek", "anthropic", "mistral"])  # type: ignore
        current_provider = cur.get("provider") or providers[0]
        current_model = cur.get("model") or ""
        api_key_info = "Yes" if cur.get("api_key_present") else "No"
        st.caption(f"API key detected: {api_key_info}")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            sel_provider = st.selectbox("Provider", providers, index=providers.index(current_provider) if current_provider in providers else 0)
        with c2:
            sel_model = st.text_input("Model", value=current_model)
        with c3:
            if st.button("Apply Provider/Model"):
                try:
                    payload = {"provider": sel_provider, "model": sel_model}
                    resp = requests.post(f"{BACKEND_URL}/llm/select", json=payload, timeout=8)
                    if resp.status_code == 200:
                        st.success(resp.json())
                    else:
                        st.error(f"Apply failed: {resp.status_code} {resp.text}")
                except Exception as e:
                    st.error(f"Apply failed: {e}")
    except Exception as e:
        st.error(f"Failed to read LLM status: {e}")

    st.subheader("Embeddings Settings")
    try:
        cur = requests.get(f"{BACKEND_URL}/embeddings/current", timeout=5).json()
        providers = cur.get("supported_providers", ["openai", "huggingface", "mistral"])  # type: ignore
        current_provider = cur.get("provider") or providers[0]
        if current_provider == "openai":
            default_model = "text-embedding-3-small"
        elif current_provider == "mistral":
            default_model = "mistral-embed"
        else:
            default_model = "sentence-transformers/all-MiniLM-L6-v2"
        current_model = cur.get("model") or default_model
        api_key_info = "Yes" if cur.get("api_key_present") else "No"
        st.caption(f"API key detected for embeddings: {api_key_info}")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            sel_provider = st.selectbox("Provider", providers, index=providers.index(current_provider) if current_provider in providers else 0, key="emb_provider")
        with c2:
            sel_model = st.text_input("Model", value=current_model, key="emb_model")
        with c3:
            if st.button("Apply Embeddings"):
                try:
                    payload = {"provider": sel_provider, "model": sel_model}
                    resp = requests.post(f"{BACKEND_URL}/embeddings/select", json=payload, timeout=8)
                    if resp.status_code == 200:
                        st.success(resp.json())
                    else:
                        st.error(f"Apply failed: {resp.status_code} {resp.text}")
                except Exception as e:
                    st.error(f"Apply failed: {e}")
    except Exception as e:
        st.error(f"Failed to read embeddings status: {e}")

with tab_admin:
    st.subheader("System Health")
    if st.button("Check Detailed Health"):
        try:
            r = requests.get(f"{BACKEND_URL}/health/detailed", timeout=5)
            health = r.json()
            st.success(f"Status: {health.get('status')}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("LLM Provider", health.get('providers', {}).get('llm', {}).get('provider', 'N/A'))
                st.caption(f"Model: {health.get('providers', {}).get('llm', {}).get('model', 'N/A')}")
                st.caption(f"Available: {'✅' if health.get('providers', {}).get('llm', {}).get('available') else '❌'}")
            with col2:
                st.metric("Embeddings Provider", health.get('providers', {}).get('embeddings', {}).get('provider', 'N/A'))
                st.caption(f"Model: {health.get('providers', {}).get('embeddings', {}).get('model', 'N/A')}")
                st.caption(f"Available: {'✅' if health.get('providers', {}).get('embeddings', {}).get('available') else '❌'}")
            with col3:
                st.metric("Vector Store", health.get('providers', {}).get('vector_store', {}).get('provider', 'N/A'))
                st.caption(f"Collection: {health.get('providers', {}).get('vector_store', {}).get('collection', 'N/A')}")
                st.caption(f"Available: {'✅' if health.get('providers', {}).get('vector_store', {}).get('available') else '❌'}")
            
            st.caption(f"Collections: {', '.join(health.get('collections', []))}")
        except Exception as e:
            st.error(f"Health check failed: {e}")
    
    st.markdown("---")
    st.subheader("Collection Management")
    
    try:
        idx = requests.get(f"{BACKEND_URL}/index/collections", timeout=5).json()
        collections = idx.get("collections", [])
        
        if collections:
            selected_coll = st.selectbox("Select collection", collections, key="admin_coll")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Get Stats"):
                    try:
                        r = requests.get(f"{BACKEND_URL}/index/collections/{selected_coll}/stats", timeout=5)
                        stats = r.json()
                        st.json(stats)
                    except Exception as e:
                        st.error(f"Failed to get stats: {e}")
            
            with c2:
                if st.button("Reset Collection", type="secondary"):
                    if st.session_state.get("confirm_reset") != selected_coll:
                        st.session_state["confirm_reset"] = selected_coll
                        st.warning(f"Click again to confirm reset of '{selected_coll}'")
                    else:
                        try:
                            r = requests.post(f"{BACKEND_URL}/index/collections/{selected_coll}/reset", timeout=10)
                            if r.status_code == 200:
                                st.success(r.json())
                                st.session_state["confirm_reset"] = None
                            else:
                                st.error(f"Reset failed: {r.status_code} {r.text}")
                        except Exception as e:
                            st.error(f"Reset failed: {e}")
            
            with c3:
                if st.button("Delete Collection", type="primary"):
                    if st.session_state.get("confirm_delete") != selected_coll:
                        st.session_state["confirm_delete"] = selected_coll
                        st.warning(f"⚠️ Click again to PERMANENTLY delete '{selected_coll}'")
                    else:
                        try:
                            r = requests.delete(f"{BACKEND_URL}/index/collections/{selected_coll}", timeout=10)
                            if r.status_code == 200:
                                st.success(r.json())
                                st.session_state["confirm_delete"] = None
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {r.status_code} {r.text}")
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
        else:
            st.info("No collections found.")
    except Exception as e:
        st.error(f"Failed to load collections: {e}")
