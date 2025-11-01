# GLIH Quick Reference Card

Fast reference for common tasks and commands.

---

## 🚀 Startup Commands

### Start Everything
```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app

# Terminal 2: Frontend
streamlit run glih-frontend/src/glih_frontend/app.py

# Terminal 3: MCP Servers
cd mcp-servers
./start_all.ps1
```

### Access Points
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WMS Server**: http://localhost:8080
- **IoT Server**: http://localhost:8081
- **Docs Server**: http://localhost:8082

---

## 📥 Ingestion Workflow

```
1. Choose Collection
   ├─ Existing: Select from dropdown
   └─ New: Enter name (e.g., lineage-sops)

2. Configure Processing
   ├─ Chunk Size: 1000 (default)
   └─ Overlap: 200 (default)

3. Select Source
   ├─ Upload Files: PDF, TXT
   └─ URL: Web page or PDF

4. Ingest
   └─ Click "🚀 Ingest Files" or "🚀 Ingest URL"
```

**Storage Location**: `data/{vector_store}/{collection_name}/`

---

## 🔍 Query Workflow

```
1. Select Knowledge Base
   ├─ Choose collection from dropdown
   ├─ Check status (✅ has documents / ⚠️ empty)
   └─ View Stats to see document count

2. Ask Your Question
   ├─ Click example query buttons (auto-fills)
   └─ Or type your own question

3. Configure Search
   ├─ Top-K: 4 (default, 1-20)
   ├─ Max Distance: Optional (e.g., 0.5)
   └─ Style: concise, bulleted, detailed, json-list

4. Search Knowledge Base
   └─ Click "🚀 Search Knowledge Base"

5. Review Results
   ├─ Read AI-generated answer
   ├─ Check citations (auto-displayed)
   └─ Verify source documents
```

**Important**: Query tab searches **ingested documents only**. For live shipment/sensor data, use **MCP tab**.

---

## 🔌 MCP Quick Actions

### Check Shipment Temperature
```
MCP Tab → Shipments (WMS) → Select ID → Get Details
```

### Monitor Sensor Live
```
MCP Tab → Sensors (IoT) → Select Type → Select Sensor → ✓ Auto-refresh
```

### Read SOP
```
MCP Tab → Documents (Docs) → Select Type → Select Document → Get Document
```

---

## ⚙️ Configuration Quick Settings

### Change Vector Store
```
Configuration Tab → Select Vector Database → Update glih.toml → Restart
```

### Change LLM
```
Configuration Tab → Select Provider & Model → Apply Provider/Model
```

### Change Embeddings
```
Configuration Tab → Select Provider & Model → Apply Embeddings
```

---

## 🛠️ Admin Quick Actions

### View Collection Stats
```
Admin Tab → Select Collection → Get Stats
```

### Delete Collection
```
Admin Tab → Select Collection → Delete Collection → Confirm
```

### Check System Health
```
Admin Tab → Check Detailed Health
```

---

## 📁 File Locations

### Configuration
- **Main Config**: `config/glih.toml`
- **Environment**: `.env`

### Data Storage
- **ChromaDB**: `data/chromadb/{collection}/`
- **FAISS**: `data/faiss/{collection}/`
- **Raw Data**: `data/raw/`
- **Processed**: `data/processed/`

### Logs
- **Backend**: Console output
- **Frontend**: Console output
- **MCP Servers**: Individual terminal windows

---

## 🧪 Testing

### Test MCP Client
```powershell
python test_mcp_client.py
```

### Expected Results
```
✅ PASS: List Resources
✅ PASS: Read Shipment
✅ PASS: Read Sensor
✅ PASS: Read Document
✅ PASS: Query Sensors
✅ PASS: Cache Performance

Total: 6/6 tests passed (100%)
```

---

## 🔧 Common Fixes

### Backend Not Connecting
```powershell
# Check if running on port 8000
netstat -ano | findstr :8000

# Restart backend
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

### MCP Servers Offline
```powershell
cd mcp-servers
./start_all.ps1
```

### Collection Dimension Mismatch
```powershell
# Quick fix - resets entire ChromaDB
.\.venv\Scripts\python.exe force_reset_chromadb.py

# Then restart backend
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app

# Refresh browser (Ctrl+R)
```

**Alternative** (keep other collections):
```
Admin Tab → Select Collection → Delete Collection → Confirm
```

### No Query Results
```
1. Check collection has documents (Admin → Get Stats)
2. Increase Top-K value
3. Remove Max Distance filter
4. Try broader query
```

---

## 📊 Default Settings

### Chunking
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Estimated**: ~12 chunks per 10k chars

### Query
- **Top-K**: 4 results
- **Style**: concise
- **Max Distance**: None (all results)

### Vector Store
- **Provider**: ChromaDB
- **Collection**: glih-default
- **Location**: `data/chromadb/`

### LLM
- **Provider**: OpenAI
- **Model**: gpt-4o
- **API Key**: From .env

### Embeddings
- **Provider**: OpenAI
- **Model**: text-embedding-3-small
- **Dimension**: 1536

---

## 🎯 Use Case Examples

### Lineage SOPs
```
Collection: lineage-sops
Chunk Size: 1000
Overlap: 200
Query: "What is the temperature breach protocol?"
```

### Facility Manuals
```
Collection: facility-chicago
Chunk Size: 1500
Overlap: 300
Query: "How do I reset the cooling system?"
```

### Cold Chain Docs
```
Collection: cold-chain-docs
Chunk Size: 800
Overlap: 150
Query: "What are the HACCP requirements for seafood?"
```

---

## 📞 Quick Help

### Documentation
- **UI Guide**: [UI_FEATURES_GUIDE.md](UI_FEATURES_GUIDE.md)
- **MCP Guide**: [MCP_UI_GUIDE.md](MCP_UI_GUIDE.md)
- **Setup**: [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

### Key Files
- **Main README**: [README.md](README.md)
- **Lineage README**: [README_LINEAGE.md](README_LINEAGE.md)
- **Config**: `config/glih.toml`

---

## 🔑 Environment Variables

Required in `.env`:
```bash
# LLM (choose one)
OPENAI_API_KEY=sk-...
MISTRAL_API_KEY=...
ANTHROPIC_API_KEY=...

# Optional
GLIH_BACKEND_URL=http://localhost:8000
```

---

## 📈 Performance Tips

### Ingestion
- Batch upload multiple files at once
- Use appropriate chunk size for document type
- Monitor storage location size

### Query
- Start with Top-K=4, adjust as needed
- Use specific questions for better results
- Check citations for accuracy

### MCP
- Use auto-refresh only when needed
- Monitor critical sensors first
- Keep MCP servers running in background

---

**For detailed information, see [UI_FEATURES_GUIDE.md](UI_FEATURES_GUIDE.md)**
