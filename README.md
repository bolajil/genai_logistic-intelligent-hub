# GenAI Logistics Intelligence Hub (GLIH)

A modular, enterprise-ready monorepo for logistics AI: ingestion, RAG, agentic workflows, backend APIs, and UI.

**Latest Updates (Dec 2025)**:
- ✅ **Cross-Platform Support**: Git Bash on Windows now fully supported
- ✅ **Redesigned Query Tab**: Step-by-step workflow, example queries, smart error handling
- ✅ **MCP UI Integration**: Browse shipments, sensors, and documents through web interface
- ✅ **Redesigned Ingestion Tab**: Step-by-step workflow with storage location visibility
- ✅ **ChromaDB Reset Tools**: Quick fix for dimension mismatch errors
- ✅ **Test Suite**: 100% passing MCP client tests
- ✅ **Production Ready**: Complete documentation and setup guides

## Structure
- `glih-backend/` FastAPI backend APIs with MCP client integration
- `glih-frontend/` Streamlit (MVP) or React dashboard
- `glih-agents/` Agentic layer (AnomalyResponder, RouteAdvisor, CustomerNotifier, OpsSummarizer)
- `glih-ingestion/` ETL and normalization
- `glih-eval/` Evaluation and monitoring
- `mcp-servers/` Model Context Protocol servers (WMS, IoT, Docs)
- `config/` Project-wide TOML configuration
- `scripts/` Developer scripts (bootstrap, dev)
- `data/` Raw/processed storage (local dev)

## Quickstart (dev)

### 1. Copy env template
```bash
# All platforms
cp .env.example .env
```

### 2. Run preflight (creates venv and installs packages)

**Windows PowerShell** (recommended for Windows):
```powershell
.\preflight.ps1
```

**Git Bash on Windows**:
```bash
bash ./preflight.sh
```

**macOS/Linux**:
```bash
bash ./preflight.sh
```

### 3. Activate virtual environment

**Windows PowerShell**:
```powershell
.\.venv\Scripts\Activate.ps1
```

**Git Bash on Windows**:
```bash
source .venv/Scripts/activate
```

**macOS/Linux**:
```bash
source .venv/bin/activate
```

### 4. Start backend (dev)
```bash
uvicorn glih_backend.api.main:app --reload --port 8000 --app-dir glih-backend/src
```

### 5. Start frontend (dev)
```bash
streamlit run glih-frontend/src/glih_frontend/app.py
```
Access at: http://localhost:8501

## Decisions needed (edit `config/glih.toml`)
- Vector store: `chromadb | faiss | pinecone | weaviate`
- Embeddings: `openai | huggingface` and model names
- Object storage: `local | s3 | azure | gcs`
- LLM provider/model: `openai | anthropic | mistral | ...`
- Agent defaults: thresholds, alerting behavior

## Model Context Protocol (MCP)

GLIH now supports **Model Context Protocol** for standardized access to external data sources:
- **WMS/TMS Integration**: Real-time shipment and inventory data
- **IoT Sensors**: Temperature, GPS, and door sensor streaming
- **Document Storage**: SOPs, invoices, and BOLs

### Quick Start with MCP

1. **Start MCP servers** (in separate terminal):
   ```powershell
   cd mcp-servers
   ./start_all.ps1  # Windows
   # or
   ./start_all.sh   # macOS/Linux
   ```

2. **Start GLIH** (if not already running):
   ```powershell
   # Backend
   .\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
   
   # Frontend (new terminal)
   streamlit run glih-frontend/src/glih_frontend/app.py
   ```

3. **Access MCP in UI**:
   - Open http://localhost:8501
   - Click the **"MCP"** tab
   - Browse shipments, sensors, and documents

4. **Test MCP programmatically**:
   ```powershell
   python test_mcp_client.py
   ```

See **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** and **[MCP_UI_GUIDE.md](MCP_UI_GUIDE.md)** for detailed instructions.

## UI Features

### Streamlit Dashboard (http://localhost:8501)

#### **Ingestion Tab** 📥
- **Step 1**: Choose collection (existing or new) with storage location info
- **Step 2**: Configure chunking (size, overlap, estimated chunks)
- **Step 3**: Select source (upload files or URL)
- **Features**: File details, progress indicators, storage path visibility, tips & best practices

#### **Query Tab** 🔍
- **Step-by-step workflow**: Select collection → Ask question → Configure → Search
- **Collection status indicators**: Green checkmark (has docs) or warning (empty)
- **Example query buttons**: Pre-built queries for common use cases
- **Smart error handling**: Helpful guidance when "I don't know" is returned
- **Inline help**: Expandable tips and troubleshooting
- **Quick navigation**: Links to Ingestion, MCP, and Admin tabs
- **Citation display**: Automatic with similarity percentages
- **Clear distinction**: Vector search vs. live data (MCP)

#### **MCP Tab** 🔌
- **Server Status**: Real-time health checks for WMS, IoT, Docs servers
- **Shipment Tracking**: View details, temperature monitoring, breach detection
- **Sensor Monitoring**: Real-time readings with auto-refresh, status indicators
- **Document Viewer**: Browse SOPs, invoices, BOLs with full content

#### **Configuration Tab** ⚙️
- Vector store selection (ChromaDB, FAISS, Pinecone, Weaviate, Qdrant)
- LLM provider/model configuration
- Embeddings provider/model configuration
- Health checks and system status

#### **Admin Tab** 🛠️
- Collection management (stats, reset, delete)
- Detailed health monitoring
- Provider availability checks

## Documentation

📚 **See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete documentation guide**

### Core Documentation
- **[README_LINEAGE.md](README_LINEAGE.md)** - Lineage Logistics solution overview with MCP details
- **[LINEAGE_SOLUTION_OVERVIEW.md](LINEAGE_SOLUTION_OVERVIEW.md)** - Comprehensive solution overview
- **[LINEAGE_PILOT_PROPOSAL.md](LINEAGE_PILOT_PROPOSAL.md)** - 12-week pilot proposal
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - 16-week technical roadmap

### MCP Documentation
- **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** - Complete MCP setup and testing guide
- **[MCP_UI_GUIDE.md](MCP_UI_GUIDE.md)** - How to use the MCP tab in the UI
- **[MCP_UI_FEATURES.md](MCP_UI_FEATURES.md)** - Visual guide to MCP UI features
- **[MCP_IMPLEMENTATION_SUMMARY.md](MCP_IMPLEMENTATION_SUMMARY.md)** - Complete implementation overview

### User Guides
- **[UI_FEATURES_GUIDE.md](UI_FEATURES_GUIDE.md)** - Complete UI walkthrough with screenshots and workflows
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and upgrade guide

## Notes
- Python 3.10+
- Packages are editable installs for rapid iteration.
- MCP integration provides $420K+ development cost savings
- CI/CD, Docker, and cloud infra can be added in Phase 8.
