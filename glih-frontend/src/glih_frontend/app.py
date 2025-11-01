import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
# Support both BACKEND_URL (Hugging Face) and GLIH_BACKEND_URL (local)
BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("GLIH_BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="GLIH Dashboard", layout="wide")
st.title("GenAI Logistics Intelligence Hub (GLIH)")

st.caption(f"Backend: {BACKEND_URL}")

# Tabs: Ingestion | Query | Configuration | Admin | MCP
tab_ingest, tab_query, tab_config, tab_admin, tab_mcp = st.tabs(["Ingestion", "Query", "Configuration", "Admin", "MCP"])

with tab_query:
    st.subheader("🔍 Knowledge Base Query")
    st.caption("Search your ingested documents using natural language")
    
    # Important notice
    st.info("""
    💡 **What can I search here?**
    - Documents you've **ingested** (PDFs, SOPs, manuals, procedures)
    - Content stored in your **vector database collections**
    
    ⚠️ **Not available here:**
    - Live shipment data → Use **MCP Tab**
    - Real-time sensor readings → Use **MCP Tab**
    - External system data → Use **MCP Tab**
    """)
    
    # Collection selection
    st.markdown("### 1️⃣ Select Knowledge Base")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        try:
            idx = requests.get(f"{BACKEND_URL}/index/collections", timeout=5).json()
            collections = idx.get("collections", [])
            default_coll = idx.get("default", "glih-default")
            
            if collections:
                sel_q_coll = st.selectbox(
                    "Choose Collection",
                    collections,
                    index=collections.index(default_coll) if default_coll in collections else 0,
                    key="query_collection",
                    help="Select which collection to search"
                )
                
                # Show collection stats
                try:
                    stats_r = requests.get(f"{BACKEND_URL}/index/collections/{sel_q_coll}/stats", timeout=5)
                    if stats_r.status_code == 200:
                        stats = stats_r.json()
                        doc_count = stats.get('count', 0)
                        if doc_count > 0:
                            st.success(f"✅ Collection **{sel_q_coll}** has **{doc_count}** documents")
                        else:
                            st.warning(f"⚠️ Collection **{sel_q_coll}** is empty. Ingest documents first!")
                except:
                    pass
            else:
                st.warning("⚠️ No collections found. Please ingest documents first in the **Ingestion** tab.")
                sel_q_coll = st.text_input(
                    "Collection Name",
                    value="glih-default",
                    key="query_collection_fallback"
                )
        except Exception as e:
            st.error(f"Could not fetch collections: {e}")
            sel_q_coll = st.text_input("Collection", value="glih-default", key="query_collection_error")
    
    with col2:
        st.metric("Collection", sel_q_coll)
        if st.button("📊 View Stats", key="view_stats"):
            try:
                stats_r = requests.get(f"{BACKEND_URL}/index/collections/{sel_q_coll}/stats", timeout=5)
                if stats_r.status_code == 200:
                    st.json(stats_r.json())
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Query input
    st.markdown("### 2️⃣ Ask Your Question")
    
    # Example queries based on common use cases
    st.markdown("**💡 Example Queries:**")
    example_col1, example_col2 = st.columns(2)
    
    with example_col1:
        if st.button("📋 Temperature breach protocol", key="ex1"):
            st.session_state["query_text"] = "What is the temperature breach response protocol?"
        if st.button("🧊 Cold chain requirements", key="ex2"):
            st.session_state["query_text"] = "What are the cold chain requirements for seafood?"
    
    with example_col2:
        if st.button("📦 HACCP procedures", key="ex3"):
            st.session_state["query_text"] = "What are the HACCP procedures for frozen foods?"
        if st.button("🔧 Equipment maintenance", key="ex4"):
            st.session_state["query_text"] = "How do I maintain refrigeration equipment?"
    
    q = st.text_area(
        "Enter your question",
        value=st.session_state.get("query_text", ""),
        placeholder="Example: What should I do if temperature exceeds the safe range?",
        height=100,
        help="Ask questions about the documents you've ingested"
    )
    
    # Clear the session state after using it
    if "query_text" in st.session_state and q:
        del st.session_state["query_text"]
    
    st.markdown("---")
    
    # Search configuration
    st.markdown("### 3️⃣ Configure Search")
    
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        top_k = st.number_input(
            "Top-K Results",
            min_value=1,
            max_value=20,
            value=4,
            step=1,
            key="k",
            help="Number of document chunks to retrieve"
        )
    with cc2:
        max_dist = st.text_input(
            "Max Distance (optional)",
            value="",
            key="maxdist",
            placeholder="e.g., 0.5",
            help="Maximum similarity distance (lower = more similar). Leave empty for no limit."
        )
    with cc3:
        style = st.selectbox(
            "Answer Style",
            ["concise", "bulleted", "detailed", "json-list"],
            index=0,
            key="style",
            help="How should the AI format the answer?"
        )
    
    # Style descriptions
    style_descriptions = {
        "concise": "Brief, direct answers",
        "bulleted": "Organized bullet points",
        "detailed": "Comprehensive explanations",
        "json-list": "Structured JSON format"
    }
    st.caption(f"**{style}**: {style_descriptions.get(style, '')}")
    
    st.markdown("---")
    
    # Send query button
    if st.button("🚀 Search Knowledge Base", type="primary", use_container_width=True):
        if not q.strip():
            st.warning("⚠️ Please enter a question")
        else:
            with st.spinner("🔍 Searching knowledge base..."):
                try:
                    params = {"q": q, "collection": sel_q_coll, "k": int(top_k), "style": style}
                    if max_dist.strip():
                        try:
                            params["max_distance"] = float(max_dist)
                        except Exception:
                            st.warning("Invalid max distance value, ignoring")
                    
                    r = requests.get(f"{BACKEND_URL}/query", params=params, timeout=20)
                    
                    if r.status_code == 200:
                        res = r.json()
                        
                        # Display answer
                        st.markdown("### 📝 Answer")
                        answer = res.get("answer", "No answer provided")
                        
                        if answer and answer != "I don't know.":
                            st.success(answer)
                        else:
                            st.warning("⚠️ **No relevant information found in the knowledge base.**")
                            st.info("""
                            **Possible reasons:**
                            - The collection is empty (no documents ingested)
                            - Your question doesn't match ingested content
                            - You're asking about live data (use MCP tab instead)
                            
                            **Try:**
                            1. Check collection has documents (Admin tab → Get Stats)
                            2. Ingest relevant documents first (Ingestion tab)
                            3. Rephrase your question
                            4. If asking about shipments/sensors, use the **MCP tab**
                            """)
                        
                        # Metadata
                        st.caption(f"🤖 LLM: {res.get('provider', 'unknown')}/{res.get('model', 'unknown')} | 📊 Retrieved: {res.get('k', 0)} chunks | 📏 Max Distance: {res.get('max_distance', 'none')}")
                        
                        # Store result for citations
                        st.session_state["last_query_result"] = res
                        
                        # Show citations immediately if answer was found
                        if answer and answer != "I don't know.":
                            st.markdown("---")
                            st.markdown("### 📚 Sources & Citations")
                            cits = res.get("citations", [])
                            if cits:
                                for i, c in enumerate(cits, 1):
                                    with st.expander(f"📄 Citation [{i}] - Distance: {c.get('distance', 'N/A')}", expanded=(i==1)):
                                        col1, col2 = st.columns([1, 1])
                                        with col1:
                                            st.write(f"**Source:** {c.get('source', 'Unknown')}")
                                            st.write(f"**Document ID:** {c.get('doc_id', 'N/A')}")
                                        with col2:
                                            st.write(f"**Chunk ID:** {c.get('chunk_id', 'N/A')}")
                                            st.write(f"**Similarity:** {1 - float(c.get('distance', 1)):.2%}")
                                        st.markdown("**Content:**")
                                        st.code(c.get("snippet", "No content"), language="text")
                            else:
                                st.info("No citations available")
                    else:
                        st.error(f"❌ Query failed: {r.status_code}")
                        st.code(r.text)
                        
                except Exception as e:
                    st.error(f"❌ Query error: {e}")
                    st.info("Make sure the backend is running and the collection exists")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ Help & Tips"):
        st.markdown("""
        ### How to Use This Tab
        
        **1. Select Collection**
        - Choose which knowledge base to search
        - Check that it has documents (look for the green checkmark)
        
        **2. Ask Your Question**
        - Use natural language
        - Be specific about what you need
        - Click example queries for inspiration
        
        **3. Configure Search**
        - **Top-K**: More results = more context (but slower)
        - **Max Distance**: Lower = stricter matching
        - **Style**: Choose how you want the answer formatted
        
        ### What Can I Search?
        
        ✅ **Available:**
        - SOPs and procedures you've ingested
        - Manuals and documentation
        - Policies and guidelines
        - Training materials
        - Any PDF or text files you've uploaded
        
        ❌ **Not Available (Use MCP Tab):**
        - Live shipment tracking
        - Real-time sensor data
        - Current system status
        - External database queries
        
        ### Troubleshooting
        
        **"I don't know" response:**
        - Collection might be empty → Ingest documents first
        - Question doesn't match content → Rephrase
        - Asking about live data → Use MCP tab
        
        **No results:**
        - Increase Top-K value
        - Remove Max Distance filter
        - Try broader questions
        - Check collection has documents
        
        **Need live data?**
        - Switch to **MCP Tab** for shipments, sensors, and real-time data
        """)
    
    # Quick navigation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📥 **Need to add documents?**\n\nGo to **Ingestion** tab")
    with col2:
        st.info("🔌 **Need live data?**\n\nGo to **MCP** tab")
    with col3:
        st.info("🛠️ **Manage collections?**\n\nGo to **Admin** tab")

with tab_ingest:
    st.subheader("📥 Data Ingestion")
    st.caption("Ingest documents into vector database for AI-powered search and retrieval")
    
    # ===== STEP 1: Collection Configuration =====
    st.markdown("### 1️⃣ Choose Storage Location")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get existing collections
        try:
            idx = requests.get(f"{BACKEND_URL}/index/collections", timeout=5).json()
            collections = idx.get("collections", [])
            default_coll = idx.get("default", "glih-default")
            vector_provider = idx.get("vector_store", "chromadb")
        except Exception as e:
            collections = ["glih-default"]
            default_coll = "glih-default"
            vector_provider = "chromadb"
            st.warning(f"⚠️ Could not fetch collections: {e}")
        
        # Collection selection mode
        collection_mode = st.radio(
            "Collection Mode",
            ["Use Existing Collection", "Create New Collection"],
            horizontal=True,
            key="collection_mode"
        )
        
        if collection_mode == "Use Existing Collection":
            if collections:
                sel_i_coll = st.selectbox(
                    "Select Collection",
                    collections,
                    index=collections.index(default_coll) if default_coll in collections else 0,
                    key="ingest_collection_select",
                    help="Choose an existing collection to add documents to"
                )
            else:
                st.info("No existing collections found. Create a new one below.")
                sel_i_coll = st.text_input(
                    "Collection Name",
                    value="glih-default",
                    key="ingest_new_coll_fallback",
                    help="Enter a name for your new collection"
                )
        else:
            sel_i_coll = st.text_input(
                "New Collection Name",
                value="",
                placeholder="e.g., lineage-sops, cold-chain-docs, facility-manuals",
                key="ingest_new_coll",
                help="Use lowercase with hyphens. Example: lineage-sops"
            )
            if sel_i_coll and not sel_i_coll.replace("-", "").replace("_", "").isalnum():
                st.error("⚠️ Collection name should only contain letters, numbers, hyphens, and underscores")
    
    with col2:
        # Storage info box
        st.info(f"""
        **Storage Info**
        
        📦 **Vector Store**: {vector_provider.upper()}
        
        📁 **Location**: `data/{vector_provider}/`
        
        🔢 **Collections**: {len(collections)}
        """)
    
    if not sel_i_coll or not sel_i_coll.strip():
        st.warning("⚠️ Please select or create a collection name before ingesting documents")
        st.stop()
    
    # Show selected collection
    st.success(f"✅ **Target Collection**: `{sel_i_coll}`")
    
    st.markdown("---")
    
    # ===== STEP 2: Chunking Configuration =====
    st.markdown("### 2️⃣ Configure Document Processing")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        chunk_size = st.number_input(
            "Chunk Size (characters)",
            min_value=200,
            max_value=4000,
            value=1000,
            step=100,
            help="Size of text chunks for embedding. Larger = more context, smaller = more precise"
        )
    with col2:
        overlap = st.number_input(
            "Overlap (characters)",
            min_value=0,
            max_value=1000,
            value=200,
            step=50,
            help="Overlap between chunks to maintain context across boundaries"
        )
    with col3:
        st.metric("Chunks per 10k chars", f"~{10000 // (chunk_size - overlap)}")
        st.caption("Estimated chunks")
    
    st.markdown("---")
    
    # ===== STEP 3: Source Selection =====
    st.markdown("### 3️⃣ Select Data Source")
    
    source_type = st.radio(
        "Choose Source Type",
        ["📄 Upload Files", "🌐 Ingest from URL"],
        horizontal=True,
        key="source_type"
    )
    
    if source_type == "📄 Upload Files":
        st.markdown("#### Upload Documents")
        uploads = st.file_uploader(
            "Choose files to ingest",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            help="Supported formats: PDF, TXT"
        )
        
        if uploads:
            st.info(f"📎 **{len(uploads)} file(s) selected**: {', '.join([f.name for f in uploads])}")
            
            # Show file details
            with st.expander("📋 File Details"):
                for f in uploads:
                    size_kb = len(f.getvalue()) / 1024
                    st.write(f"- **{f.name}** ({size_kb:.1f} KB, {f.type})")
        
        if st.button("🚀 Ingest Files", type="primary", use_container_width=True):
            if not uploads:
                st.warning("⚠️ Please select at least one file to ingest")
            else:
                with st.spinner(f"Ingesting {len(uploads)} file(s) into `{sel_i_coll}`..."):
                    try:
                        files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in uploads]
                        params = {"chunk_size": int(chunk_size), "overlap": int(overlap), "collection": sel_i_coll}
                        r = requests.post(f"{BACKEND_URL}/ingest/file", params=params, files=files, timeout=120)
                        
                        if r.status_code == 200:
                            result = r.json()
                            st.success("✅ **Ingestion Complete!**")
                            
                            # Show detailed results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Files Processed", len(uploads))
                            with col2:
                                st.metric("Collection", sel_i_coll)
                            with col3:
                                st.metric("Storage", vector_provider.upper())
                            
                            st.json(result)
                            st.info(f"💾 **Stored in**: `data/{vector_provider}/{sel_i_coll}/`")
                        else:
                            st.error(f"❌ Ingestion failed: {r.status_code}")
                            st.code(r.text)
                    except Exception as e:
                        st.error(f"❌ Ingestion error: {e}")
    
    else:  # URL Ingestion
        st.markdown("#### Ingest from URL")
        url = st.text_input(
            "Enter URL",
            placeholder="https://example.com/document.pdf or https://example.com/page",
            help="Supported: Web pages (HTML) and PDF documents"
        )
        
        if url:
            st.info(f"🔗 **Target URL**: {url}")
        
        if st.button("🚀 Ingest URL", type="primary", use_container_width=True):
            if not url.strip():
                st.warning("⚠️ Please enter a URL to ingest")
            else:
                with st.spinner(f"Fetching and ingesting from {url}..."):
                    try:
                        payload = {
                            "urls": [url],
                            "chunk_size": int(chunk_size),
                            "overlap": int(overlap),
                            "collection": sel_i_coll
                        }
                        r = requests.post(f"{BACKEND_URL}/ingest/url", json=payload, timeout=60)
                        
                        if r.status_code == 200:
                            result = r.json()
                            st.success("✅ **Ingestion Complete!**")
                            
                            # Show detailed results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("URLs Processed", 1)
                            with col2:
                                st.metric("Collection", sel_i_coll)
                            with col3:
                                st.metric("Storage", vector_provider.upper())
                            
                            st.json(result)
                            st.info(f"💾 **Stored in**: `data/{vector_provider}/{sel_i_coll}/`")
                        else:
                            st.error(f"❌ Ingestion failed: {r.status_code}")
                            st.code(r.text)
                    except Exception as e:
                        st.error(f"❌ Ingestion error: {e}")
    
    st.markdown("---")
    
    # ===== Quick Tips =====
    with st.expander("💡 Ingestion Tips & Best Practices"):
        st.markdown("""
        ### Collection Naming
        - Use descriptive names: `lineage-sops`, `facility-chicago`, `cold-chain-docs`
        - Separate different document types into different collections
        - Use hyphens or underscores, lowercase only
        
        ### Chunk Size Guidelines
        - **Small (200-500)**: Precise retrieval, good for Q&A
        - **Medium (500-1500)**: Balanced, good for most use cases
        - **Large (1500-4000)**: More context, good for summarization
        
        ### Overlap Guidelines
        - **10-20% of chunk size** is recommended
        - Prevents context loss at chunk boundaries
        - Higher overlap = more redundancy but better context
        
        ### Supported Formats
        - **PDF**: Extracts text from PDF documents
        - **TXT**: Plain text files
        - **URLs**: Web pages and online PDFs
        
        ### Storage Location
        - Files are stored in: `data/{vector_store}/{collection_name}/`
        - Each collection is independent
        - Collections can be deleted from the Admin tab
        """)
    
    # ===== Collection Stats =====
    if collections:
        with st.expander("📊 Existing Collections"):
            for coll in collections:
                try:
                    r = requests.get(f"{BACKEND_URL}/index/collections/{coll}/stats", timeout=5)
                    if r.status_code == 200:
                        stats = r.json()
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{coll}**")
                        with col2:
                            st.write(f"📄 {stats.get('count', 0)} docs")
                        with col3:
                            if st.button("View", key=f"view_{coll}"):
                                st.info(f"Switch to Query tab and select `{coll}` to search this collection")
                except:
                    pass

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

with tab_mcp:
    st.subheader("Model Context Protocol (MCP)")
    st.caption("Standardized access to external data sources (WMS, IoT, Documents)")
    
    # Check if MCP servers are running
    mcp_servers = [
        {"name": "WMS Server", "url": "http://localhost:8080", "description": "Warehouse Management System"},
        {"name": "IoT Server", "url": "http://localhost:8081", "description": "IoT Sensor Data"},
        {"name": "Docs Server", "url": "http://localhost:8082", "description": "Document Storage"}
    ]
    
    st.markdown("### Server Status")
    cols = st.columns(3)
    server_status = {}
    
    for idx, server in enumerate(mcp_servers):
        with cols[idx]:
            try:
                r = requests.get(f"{server['url']}/health", timeout=2)
                if r.status_code == 200:
                    st.success(f"✅ {server['name']}")
                    st.caption(server['description'])
                    server_status[server['name']] = True
                else:
                    st.error(f"❌ {server['name']}")
                    st.caption("Not responding")
                    server_status[server['name']] = False
            except Exception:
                st.error(f"❌ {server['name']}")
                st.caption("Not running")
                server_status[server['name']] = False
    
    if not any(server_status.values()):
        st.warning("⚠️ No MCP servers are running. Start them with:")
        st.code("cd mcp-servers\n./start_all.ps1  # Windows\n# or\n./start_all.sh   # macOS/Linux", language="bash")
        st.info("See MCP_SETUP_GUIDE.md for detailed instructions.")
    
    st.markdown("---")
    
    # Resource Browser
    st.markdown("### Resource Browser")
    
    resource_type = st.selectbox(
        "Select Resource Type",
        ["Shipments (WMS)", "Sensors (IoT)", "Documents (Docs)"],
        key="mcp_resource_type"
    )
    
    if resource_type == "Shipments (WMS)":
        if not server_status.get("WMS Server"):
            st.warning("WMS Server is not running")
        else:
            try:
                # List shipments
                r = requests.get("http://localhost:8080/resources", timeout=5)
                resources = r.json().get("resources", [])
                
                if resources:
                    st.caption(f"Found {len(resources)} shipments")
                    
                    # Extract shipment IDs
                    shipment_ids = [res["uri"].split("/")[-1] for res in resources]
                    selected_shipment = st.selectbox("Select Shipment", shipment_ids, key="mcp_shipment")
                    
                    if st.button("Get Shipment Details", key="get_shipment"):
                        try:
                            r = requests.get(f"http://localhost:8080/resources/shipments/{selected_shipment}", timeout=5)
                            shipment = r.json()
                            
                            # Display shipment info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Origin", shipment.get("origin", "N/A"))
                                st.metric("Product Type", shipment.get("product_type", "N/A"))
                            with col2:
                                st.metric("Destination", shipment.get("destination", "N/A"))
                                st.metric("Status", shipment.get("status", "N/A"))
                            with col3:
                                temp = shipment.get("current_temperature")
                                temp_range = shipment.get("temperature_range", [])
                                if temp is not None and len(temp_range) == 2:
                                    temp_min, temp_max = temp_range
                                    if temp < temp_min or temp > temp_max:
                                        st.metric("Temperature", f"{temp}°C", delta="⚠️ BREACH", delta_color="inverse")
                                    else:
                                        st.metric("Temperature", f"{temp}°C", delta="✅ OK", delta_color="normal")
                                else:
                                    st.metric("Temperature", "N/A")
                                st.caption(f"Required: {temp_range[0]}°C to {temp_range[1]}°C" if len(temp_range) == 2 else "")
                            
                            # Full details
                            with st.expander("Full Shipment Data"):
                                st.json(shipment)
                        
                        except Exception as e:
                            st.error(f"Failed to get shipment: {e}")
                else:
                    st.info("No shipments found")
            
            except Exception as e:
                st.error(f"Failed to list shipments: {e}")
    
    elif resource_type == "Sensors (IoT)":
        if not server_status.get("IoT Server"):
            st.warning("IoT Server is not running")
        else:
            try:
                # List sensors
                r = requests.get("http://localhost:8081/resources", timeout=5)
                resources = r.json().get("resources", [])
                
                if resources:
                    st.caption(f"Found {len(resources)} sensors")
                    
                    # Group by type
                    sensor_types = {}
                    for res in resources:
                        sensor_type = res["metadata"].get("type", "unknown")
                        if sensor_type not in sensor_types:
                            sensor_types[sensor_type] = []
                        sensor_types[sensor_type].append(res["uri"].split("/")[-1])
                    
                    # Filter by type
                    selected_type = st.selectbox("Sensor Type", list(sensor_types.keys()), key="mcp_sensor_type")
                    selected_sensor = st.selectbox("Select Sensor", sensor_types[selected_type], key="mcp_sensor")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False, key="auto_refresh")
                    with col2:
                        if st.button("Get Sensor Reading", key="get_sensor") or auto_refresh:
                            try:
                                r = requests.get(f"http://localhost:8081/resources/sensors/{selected_sensor}", timeout=5)
                                sensor = r.json()
                                
                                # Display sensor reading
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Sensor ID", sensor.get("sensor_id", "N/A"))
                                with col2:
                                    st.metric("Type", sensor.get("sensor_type", "N/A"))
                                with col3:
                                    value = sensor.get("value")
                                    unit = sensor.get("unit", "")
                                    st.metric("Value", f"{value} {unit}" if value is not None else "N/A")
                                with col4:
                                    status = sensor.get("status", "unknown")
                                    if status == "critical":
                                        st.metric("Status", "🔴 CRITICAL")
                                    elif status == "warning":
                                        st.metric("Status", "🟡 WARNING")
                                    else:
                                        st.metric("Status", "🟢 NORMAL")
                                
                                st.caption(f"Shipment: {sensor.get('shipment_id', 'N/A')} | Timestamp: {sensor.get('timestamp', 'N/A')}")
                                
                                # Full details
                                with st.expander("Full Sensor Data"):
                                    st.json(sensor)
                                
                                if auto_refresh:
                                    import time
                                    time.sleep(5)
                                    st.rerun()
                            
                            except Exception as e:
                                st.error(f"Failed to get sensor reading: {e}")
                else:
                    st.info("No sensors found")
            
            except Exception as e:
                st.error(f"Failed to list sensors: {e}")
    
    elif resource_type == "Documents (Docs)":
        if not server_status.get("Docs Server"):
            st.warning("Docs Server is not running")
        else:
            try:
                # List documents
                r = requests.get("http://localhost:8082/resources", timeout=5)
                resources = r.json().get("resources", [])
                
                if resources:
                    st.caption(f"Found {len(resources)} documents")
                    
                    # Group by type
                    doc_types = {}
                    for res in resources:
                        doc_type = res["metadata"].get("type", "unknown")
                        if doc_type not in doc_types:
                            doc_types[doc_type] = []
                        doc_types[doc_type].append({
                            "id": res["uri"].split("/")[-1],
                            "name": res["name"]
                        })
                    
                    # Filter by type
                    selected_type = st.selectbox("Document Type", list(doc_types.keys()), key="mcp_doc_type")
                    doc_options = {doc["name"]: doc["id"] for doc in doc_types[selected_type]}
                    selected_doc_name = st.selectbox("Select Document", list(doc_options.keys()), key="mcp_doc")
                    selected_doc_id = doc_options[selected_doc_name]
                    
                    if st.button("Get Document", key="get_doc"):
                        try:
                            r = requests.get(f"http://localhost:8082/resources/documents/{selected_doc_id}", timeout=5)
                            doc = r.json()
                            
                            # Display document info
                            st.markdown(f"### {doc.get('title', 'Untitled')}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Type", doc.get("document_type", "N/A").upper())
                            with col2:
                                st.metric("Created", doc.get("created_at", "N/A")[:10])
                            with col3:
                                tags = doc.get("tags", [])
                                st.caption(f"Tags: {', '.join(tags)}" if tags else "No tags")
                            
                            if doc.get("shipment_id"):
                                st.info(f"📦 Associated with shipment: {doc['shipment_id']}")
                            
                            # Document content
                            st.markdown("#### Content")
                            content = doc.get("content", "")
                            if content:
                                st.text_area("", value=content, height=400, key="doc_content")
                            else:
                                st.info("No content available")
                            
                            # Full details
                            with st.expander("Full Document Metadata"):
                                st.json(doc)
                        
                        except Exception as e:
                            st.error(f"Failed to get document: {e}")
                else:
                    st.info("No documents found")
            
            except Exception as e:
                st.error(f"Failed to list documents: {e}")
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Search All Resources", key="search_all"):
            st.info("Search functionality coming soon...")
    
    with col2:
        if st.button("📊 View Analytics Dashboard", key="analytics"):
            st.info("Analytics dashboard coming soon...")
    
    st.markdown("---")
    st.caption("💡 **Tip**: MCP provides standardized access to WMS, IoT sensors, and documents. See MCP_SETUP_GUIDE.md for more details.")
