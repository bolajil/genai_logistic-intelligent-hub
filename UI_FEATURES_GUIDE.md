# GLIH UI Features Guide

Complete guide to using the GenAI Logistics Intelligence Hub web interface.

---

## Accessing the Dashboard

1. **Start the backend**:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
   ```

2. **Start the frontend**:
   ```powershell
   streamlit run glih-frontend/src/glih_frontend/app.py
   ```

3. **Open in browser**: http://localhost:8501

---

## Tab Overview

The dashboard has 5 main tabs:
- **Ingestion** 📥 - Upload and process documents
- **Query** 🔍 - Search your knowledge base
- **Configuration** ⚙️ - System settings
- **Admin** 🛠️ - Collection management
- **MCP** 🔌 - External data sources

---

## 📥 Ingestion Tab

### Purpose
Ingest documents into vector database for AI-powered search and retrieval.

### Workflow

#### **Step 1: Choose Storage Location**

**Option A: Use Existing Collection**
1. Select "Use Existing Collection" radio button
2. Choose from dropdown (e.g., `glih-default`, `lineage-sops`)
3. See storage info box showing:
   - Vector Store type (ChromaDB, FAISS, etc.)
   - Storage location (`data/chromadb/`)
   - Number of collections

**Option B: Create New Collection**
1. Select "Create New Collection" radio button
2. Enter collection name (e.g., `facility-chicago`, `cold-chain-docs`)
3. Use lowercase with hyphens or underscores
4. Validation ensures proper naming

**Storage Info Box** shows:
- 📦 Vector Store: CHROMADB
- 📁 Location: `data/chromadb/`
- 🔢 Collections: 3

#### **Step 2: Configure Document Processing**

**Chunk Size** (200-4000 characters)
- **Small (200-500)**: Precise retrieval, good for Q&A
- **Medium (500-1500)**: Balanced, recommended for most use cases
- **Large (1500-4000)**: More context, good for summarization
- Default: 1000 characters

**Overlap** (0-1000 characters)
- Prevents context loss at chunk boundaries
- Recommended: 10-20% of chunk size
- Default: 200 characters

**Estimated Chunks**: Shows `~12` chunks per 10k characters

#### **Step 3: Select Data Source**

**Option A: Upload Files** 📄
1. Click "Upload Files" radio button
2. Click "Browse files" or drag & drop
3. Supported formats: PDF, TXT
4. Multiple files allowed
5. See file details (name, size, type)
6. Click "🚀 Ingest Files"

**Option B: Ingest from URL** 🌐
1. Click "Ingest from URL" radio button
2. Enter URL (web page or PDF)
3. Examples:
   - `https://example.com/document.pdf`
   - `https://example.com/page`
4. Click "🚀 Ingest URL"

### Success Feedback

After ingestion, you'll see:
- ✅ **Ingestion Complete!**
- **Metrics**:
  - Files Processed: 2
  - Collection: lineage-sops
  - Storage: CHROMADB
- **Storage Path**: `data/chromadb/lineage-sops/`
- **JSON Response**: Full ingestion details

### Tips & Best Practices

**Collection Naming**:
- Use descriptive names: `lineage-sops`, `facility-chicago`
- Separate document types into different collections
- Use hyphens or underscores, lowercase only

**Chunk Size Guidelines**:
- SOPs and procedures: 1000-1500 (medium)
- Q&A knowledge base: 500-800 (small-medium)
- Long-form documents: 1500-2000 (large)

**Overlap Guidelines**:
- Standard: 200 characters (20% of 1000)
- High precision: 100-150 characters
- High context: 300-400 characters

### Existing Collections

Expand "📊 Existing Collections" to see:
- Collection names
- Document count
- Quick "View" button (switches to Query tab)

---

## 🔍 Query Tab

### Purpose
Search your ingested documents using natural language queries. This tab searches your **vector database** (documents you've uploaded), NOT live external data.

### Important Notice

**What You CAN Search:**
- ✅ Documents you've ingested (PDFs, SOPs, manuals)
- ✅ Content stored in your vector database collections
- ✅ Procedures, policies, and training materials

**What You CANNOT Search (Use MCP Tab Instead):**
- ❌ Live shipment data
- ❌ Real-time sensor readings
- ❌ External system data

### Step-by-Step Workflow

#### **Step 1: Select Knowledge Base** 📚

1. **Choose Collection**:
   - Select from dropdown
   - Shows all available collections
   - Default: `glih-default`

2. **Check Collection Status**:
   - ✅ Green checkmark = Has documents
   - ⚠️ Warning = Collection is empty
   - View Stats button shows document count

3. **Collection Metrics**:
   - Displays selected collection name
   - Shows number of documents
   - Click "📊 View Stats" for details

#### **Step 2: Ask Your Question** ❓

1. **Use Example Queries**:
   - 📋 Temperature breach protocol
   - 🧊 Cold chain requirements
   - 📦 HACCP procedures
   - 🔧 Equipment maintenance
   - Click any button to auto-fill the query

2. **Enter Your Question**:
   - Use the text area (supports multi-line)
   - Be specific about what you need
   - Natural language works best
   - Example: "What should I do if temperature exceeds the safe range?"

#### **Step 3: Configure Search** ⚙️

1. **Top-K Results** (1-20, default: 4):
   - Number of document chunks to retrieve
   - More results = more context (but slower)
   - Start with 4, adjust as needed

2. **Max Distance** (optional):
   - Maximum similarity distance
   - Lower = stricter matching
   - Leave empty for no limit
   - Example: 0.5

3. **Answer Style**:
   - **concise**: Brief, direct answers
   - **bulleted**: Organized bullet points
   - **detailed**: Comprehensive explanations
   - **json-list**: Structured JSON format

#### **Step 4: Search** 🚀

Click **"🚀 Search Knowledge Base"** button

### Results Display

#### **Answer Section** 📝
- AI-generated response based on retrieved documents
- Formatted according to selected style
- Shows metadata: LLM provider/model, chunks retrieved, max distance

#### **No Results?**
If you get "I don't know" or no relevant information:

**Possible Reasons:**
- Collection is empty (no documents ingested)
- Question doesn't match ingested content
- Asking about live data (use MCP tab)

**Solutions:**
1. Check collection has documents (Admin tab → Get Stats)
2. Ingest relevant documents first (Ingestion tab)
3. Rephrase your question
4. If asking about shipments/sensors, use **MCP tab**

#### **Sources & Citations** 📚
- Automatically displayed when answer is found
- Each citation shows:
  - **Source**: Original file/URL
  - **Document ID**: Unique identifier
  - **Chunk ID**: Specific chunk number
  - **Similarity**: Percentage match (higher = more relevant)
  - **Content**: Full text snippet
- First citation expanded by default
- Click to expand/collapse other citations

### Help & Tips Section

**Expandable "❓ Help & Tips" section includes:**
- How to use each step
- What you can and cannot search
- Troubleshooting common issues
- When to use MCP tab instead

### Quick Navigation

Three info boxes at bottom:
- 📥 **Need to add documents?** → Ingestion tab
- 🔌 **Need live data?** → MCP tab
- 🛠️ **Manage collections?** → Admin tab

### Common Use Cases

#### **Search SOPs**
```
Collection: lineage-sops
Query: "What is the temperature breach response protocol?"
Top-K: 4
Style: detailed
```

#### **Find Procedures**
```
Collection: facility-manuals
Query: "How do I reset the cooling system?"
Top-K: 3
Style: bulleted
```

#### **Compliance Questions**
```
Collection: cold-chain-docs
Query: "What are the HACCP requirements for seafood?"
Top-K: 5
Style: detailed
```

### Troubleshooting

#### **"I don't know" Response**
- Collection might be empty → Ingest documents first
- Question doesn't match content → Rephrase
- Asking about live data → Use MCP tab

#### **No Results**
- Increase Top-K value
- Remove Max Distance filter
- Try broader questions
- Check collection has documents

#### **Wrong Collection Selected**
- Use dropdown to switch collections
- Check green checkmark for document count
- View Stats to verify content

#### **Need Live Shipment/Sensor Data?**
- Switch to **MCP Tab**
- Query tab only searches ingested documents
- MCP tab accesses real-time external data

### Best Practices

1. **Collection Organization**:
   - Keep related documents in same collection
   - Use descriptive collection names
   - Separate document types

2. **Query Optimization**:
   - Be specific in your questions
   - Include context when needed
   - Use example queries as templates

3. **Result Verification**:
   - Always check citations
   - Verify source documents
   - Cross-reference important information

4. **Performance**:
   - Start with Top-K=4
   - Increase only if needed
   - Use Max Distance for stricter matching

---

## 🔌 MCP Tab

### Purpose
Access external data sources (WMS, IoT sensors, documents) through Model Context Protocol.

### Server Status Dashboard

Shows real-time status of 3 MCP servers:
- ✅ **WMS Server** (port 8080) - Warehouse Management System
- ✅ **IoT Server** (port 8081) - IoT Sensor Data
- ✅ **Docs Server** (port 8082) - Document Storage

**If servers are offline**: Shows instructions to start them:
```powershell
cd mcp-servers
./start_all.ps1
```

### Resource Browser

#### **Shipments (WMS)**

1. Select "Shipments (WMS)" from dropdown
2. See count: "Found 3 shipments"
3. Select shipment ID from dropdown
4. Click "Get Shipment Details"

**Displays**:
- **Origin**: Dallas
- **Destination**: Chicago
- **Product Type**: Seafood
- **Status**: in_transit
- **Temperature**: 0.5°C with ✅ OK or ⚠️ BREACH indicator
- **Required Range**: -2°C to 2°C
- **ETA**: 2025-10-31 14:00:00

**Temperature Breach Detection**:
- Green ✅ OK: Within range
- Red ⚠️ BREACH: Outside range (highlighted)

#### **Sensors (IoT)**

1. Select "Sensors (IoT)" from dropdown
2. Choose sensor type: temperature, GPS, door
3. Select specific sensor
4. **Optional**: Check "Auto-refresh (5s)" for live monitoring
5. Click "Get Sensor Reading"

**Displays**:
- **Sensor ID**: TEMP-001
- **Type**: temperature
- **Value**: -0.91 celsius
- **Status**: 🟢 NORMAL / 🟡 WARNING / 🔴 CRITICAL
- **Shipment**: Associated shipment ID
- **Timestamp**: Reading time

**Auto-Refresh**:
- Updates every 5 seconds
- Perfect for monitoring critical sensors
- Shows live temperature changes

#### **Documents (Docs)**

1. Select "Documents (Docs)" from dropdown
2. Choose document type: sop, invoice, bol
3. Select document from dropdown
4. Click "Get Document"

**Displays**:
- **Title**: Temperature Breach Response Protocol
- **Type**: SOP
- **Created**: 2024-01-15
- **Tags**: sop, temperature, breach, response
- **Associated Shipment**: If applicable
- **Full Content**: Complete document text

### Use Cases

**Monitor Temperature Breach**:
```
MCP Tab → Shipments → CHI-ATL-2025-089 → See 5.2°C breach
```

**Live Sensor Monitoring**:
```
MCP Tab → Sensors → temperature → TEMP-001 → ✓ Auto-refresh
```

**Read Response Procedures**:
```
MCP Tab → Documents → sop → Temperature Breach Protocol
```

---

## ⚙️ Configuration Tab

### Health & Config

**Check Backend Health**:
- Click button to verify backend is running
- Shows status and configuration

**Show Backend Config**:
- Displays full configuration JSON
- Shows all settings from `glih.toml`

### Vector Store Settings

**Select Vector Database**:
- ChromaDB (Local, Persistent) - Default
- FAISS (Local, Fast)
- Pinecone (Cloud, Managed)
- Weaviate (Cloud/Self-hosted)
- Qdrant (Cloud/Self-hosted)
- Milvus (Coming Soon)

**Info for each store**:
- ✅ Local storage - No setup required
- ☁️ Cloud managed - Requires API key
- 🔧 Requires setup - Configuration needed

**To switch vector stores**:
1. Select new provider
2. See warning with TOML config snippet
3. Update `config/glih.toml`
4. Restart backend

### LLM Settings

**Configure Language Model**:
- **Provider**: openai, deepseek, anthropic, mistral
- **Model**: gpt-4o, gpt-4o-mini, claude-3, etc.
- **API Key**: Shows if detected in environment

**Apply Changes**:
1. Select provider and model
2. Click "Apply Provider/Model"
3. Confirmation message on success

### Embeddings Settings

**Configure Embeddings**:
- **Provider**: openai, huggingface, mistral
- **Model**: 
  - OpenAI: text-embedding-3-small
  - Mistral: mistral-embed
  - HuggingFace: sentence-transformers/all-MiniLM-L6-v2

**Apply Changes**:
1. Select provider and model
2. Click "Apply Embeddings"
3. Confirmation message on success

---

## 🛠️ Admin Tab

### System Health

**Check Detailed Health**:
- Click button to see comprehensive health status
- **Displays**:
  - LLM Provider & Model (with availability)
  - Embeddings Provider & Model (with availability)
  - Vector Store Provider & Collection (with availability)
  - List of all collections

### Collection Management

**Get Stats**:
1. Select collection from dropdown
2. Click "Get Stats"
3. See document count and metadata

**Reset Collection**:
1. Select collection
2. Click "Reset Collection"
3. Click again to confirm
4. Clears all documents, keeps collection

**Delete Collection**:
1. Select collection
2. Click "Delete Collection"
3. Click again to confirm (⚠️ PERMANENT)
4. Removes collection entirely

---

## Common Workflows

### Workflow 1: Ingest SOPs

```
1. Ingestion Tab
2. Create New Collection: "lineage-sops"
3. Chunk Size: 1000, Overlap: 200
4. Upload Files: Select all SOP PDFs
5. Click "Ingest Files"
6. See success: "Stored in data/chromadb/lineage-sops/"
```

### Workflow 2: Search Knowledge Base

```
1. Query Tab
2. Select Collection: "lineage-sops"
3. Enter Query: "What is the temperature breach protocol?"
4. Top-K: 4, Style: detailed
5. Click "Send Query"
6. Read answer and check citations
```

### Workflow 3: Monitor Shipment

```
1. MCP Tab
2. Select "Shipments (WMS)"
3. Choose shipment: CHI-ATL-2025-089
4. Click "Get Shipment Details"
5. See temperature breach: 5.2°C (⚠️ BREACH)
6. Switch to Documents → Read SOP-TEMP-BREACH-001
```

### Workflow 4: Live Sensor Monitoring

```
1. MCP Tab
2. Select "Sensors (IoT)"
3. Sensor Type: temperature
4. Select: TEMP-002
5. Check "Auto-refresh (5s)"
6. Click "Get Sensor Reading"
7. Watch live updates every 5 seconds
```

---

## Troubleshooting

### "Backend connection failed"
**Fix**: Start backend on port 8000
```powershell
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

### "MCP servers not running"
**Fix**: Start MCP servers
```powershell
cd mcp-servers
./start_all.ps1
```

### "Collection expecting embedding with dimension of X, got Y"
This error occurs when you change embeddings models or have test data with wrong dimensions.

**Quick Fix**:
```powershell
# Run the reset script
.\.venv\Scripts\python.exe force_reset_chromadb.py

# Then restart backend
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app

# Refresh browser (Ctrl+R)
```

**What it does**:
- Deletes entire ChromaDB directory
- Removes all collections with wrong dimensions
- Backend creates new collections with correct dimensions automatically

**Note**: You'll lose ingested data and need to re-ingest documents.

**Alternative (Keep other collections)**:
1. Go to Admin tab
2. Select problematic collection
3. Click "Delete Collection"
4. Confirm deletion
5. Refresh browser

### "No documents found"
**Fix**: Ingest documents first in Ingestion tab

### "Query returns no results"
**Fix**: 
- Check collection has documents (Admin → Get Stats)
- Try broader query
- Increase Top-K value
- Remove Max Distance filter

### "Query returns 'I don't know'"
**Possible causes**:
1. Collection is empty → Ingest documents first
2. Question doesn't match content → Rephrase query
3. Asking about live data → Use MCP tab instead

**Fix**:
- Check collection status (green checkmark)
- Click "📊 View Stats" to see document count
- Try example queries to test
- If asking about shipments/sensors, switch to MCP tab

---

## Best Practices

### Collection Organization
- Separate collections by document type
- Use descriptive names
- Don't mix different content types

### Chunking Strategy
- Start with defaults (1000/200)
- Adjust based on document type
- Test with sample queries

### Query Optimization
- Use specific questions
- Include context in query
- Check citations for accuracy

### MCP Monitoring
- Use auto-refresh for critical sensors
- Check shipment temperatures regularly
- Read SOPs before responding to incidents

---

## Keyboard Shortcuts

- **Ctrl+R**: Refresh page
- **Tab**: Navigate between fields
- **Enter**: Submit forms (in some contexts)
- **Esc**: Close modals/expanders

---

**For technical details, see [README.md](README.md) and [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)**
