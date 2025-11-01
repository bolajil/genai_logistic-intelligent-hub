# GLIH Changelog

All notable changes to the GenAI Logistics Intelligence Hub project.

---

## [1.1.0] - October 30, 2025

### 🎉 Major Features

#### **Redesigned Query Tab**
- **Step-by-step workflow** with clear guidance
- **Important notice** distinguishing vector search from live data (MCP)
- **Collection status indicators**: Green checkmark for documents, warning for empty
- **Example query buttons**: 4 pre-built queries for common use cases
- **Text area input**: Multi-line support for longer questions
- **Enhanced results display**: Immediate citation display, similarity percentages
- **Smart error handling**: Helpful troubleshooting when "I don't know" is returned
- **Inline help section**: Expandable tips and best practices
- **Quick navigation**: Links to Ingestion, MCP, and Admin tabs
- **Better UX**: Clear distinction between what you can/cannot search

#### **MCP UI Integration**
- Added new "MCP" tab to Streamlit dashboard
- Real-time server status monitoring (WMS, IoT, Docs)
- Interactive resource browser for shipments, sensors, and documents
- Live sensor monitoring with auto-refresh (5-second intervals)
- Temperature breach detection and highlighting
- Full document viewer with metadata display

#### **Redesigned Ingestion Tab**
- **Step-by-step workflow**:
  1. Choose storage location (existing or new collection)
  2. Configure document processing (chunk size, overlap)
  3. Select data source (files or URL)
- **Storage visibility**: Shows vector store type and file paths
- **Collection mode**: Radio buttons for "Use Existing" vs "Create New"
- **Enhanced feedback**: Progress indicators, file details, success metrics
- **Best practices**: Expandable tips section with guidelines
- **Collection stats**: View existing collections with document counts

### ✅ Improvements

#### **MCP Client**
- Fixed HTTP client lifecycle management
- Resolved "client has been closed" error
- Singleton pattern properly implemented
- All 6 test cases now passing (100%)

#### **Schema Updates**
- Changed `SensorResource.value` from `float` to `Any`
- Now supports temperature (float), GPS (string), door (int) sensors
- Proper validation for all sensor types

#### **Configuration**
- Updated `glih.toml` with comprehensive settings
- Added Lineage-specific configuration section
- MCP servers enabled by default
- Temperature ranges for all product types

#### **Documentation**
- Created `UI_FEATURES_GUIDE.md` - Complete UI walkthrough
- Created `MCP_UI_GUIDE.md` - MCP tab usage guide
- Created `MCP_UI_FEATURES.md` - Visual feature guide
- Created `MCP_IMPLEMENTATION_SUMMARY.md` - Implementation overview
- Updated `README.md` with UI features section
- Updated `README_LINEAGE.md` with latest release notes

### 🐛 Bug Fixes

- Fixed MCP client closing prematurely between tests
- Fixed sensor value type validation error
- Fixed collection dimension mismatch handling
- Fixed storage location visibility in UI
- Added ChromaDB reset scripts for dimension mismatch errors

### 🛠️ Tools & Scripts

- **force_reset_chromadb.py**: Quick reset for ChromaDB dimension mismatches
- **reset_chromadb.py**: Interactive ChromaDB reset with confirmation
- **delete_collection.py**: Delete specific problematic collections

### 📊 Testing

- `test_mcp_client.py`: 6/6 tests passing (100%)
  - ✅ List Resources
  - ✅ Read Shipment
  - ✅ Read Sensor
  - ✅ Read Document
  - ✅ Query Sensors
  - ✅ Cache Performance

### 📦 Dependencies

No new dependencies added. All changes use existing packages.

---

## [1.0.0] - October 2025

### 🎉 Initial Release

#### **Core Features**
- FastAPI backend with RAG pipeline
- Streamlit frontend dashboard
- Vector store support (ChromaDB, FAISS, Pinecone, Weaviate, Qdrant)
- LLM integration (OpenAI, Mistral, Anthropic)
- Embeddings support (OpenAI, HuggingFace, Mistral)

#### **Agents**
- AnomalyResponder - Temperature breach detection
- RouteAdvisor - Route optimization
- CustomerNotifier - Automated notifications
- OpsSummarizer - Operational summaries

#### **MCP Infrastructure**
- MCP client layer with caching and retries
- Mock WMS server (3 shipments)
- Mock IoT server (9 sensors)
- Mock Docs server (4 documents)
- Startup scripts for all servers

#### **UI Tabs**
- Ingestion - Upload files and URLs
- Query - Natural language search
- Configuration - System settings
- Admin - Collection management

#### **Documentation**
- README.md - Project overview
- README_LINEAGE.md - Lineage Logistics solution
- MCP_SETUP_GUIDE.md - MCP installation guide
- LINEAGE_SOLUTION_OVERVIEW.md - Comprehensive overview
- LINEAGE_PILOT_PROPOSAL.md - 12-week pilot plan
- IMPROVEMENTS.md - 16-week roadmap

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.1.0 | Oct 30, 2025 | MCP UI integration, redesigned Ingestion tab |
| 1.0.0 | Oct 2025 | Initial release with core features |

---

## Upgrade Guide

### From 1.0.0 to 1.1.0

**No breaking changes!** Simply pull the latest code and restart:

1. **Update code**:
   ```bash
   git pull origin main
   ```

2. **Enable MCP servers in config** (if not already):
   ```toml
   # config/glih.toml
   [[mcp.servers]]
   enabled = true  # Set to true for all 3 servers
   ```

3. **Restart services**:
   ```powershell
   # Stop and restart backend
   # Stop and restart frontend
   # Start MCP servers
   cd mcp-servers
   ./start_all.ps1
   ```

4. **Access new features**:
   - Open http://localhost:8501
   - Check out the new MCP tab
   - Try the redesigned Ingestion tab

**New Files**:
- `UI_FEATURES_GUIDE.md`
- `MCP_UI_GUIDE.md`
- `MCP_UI_FEATURES.md`
- `MCP_IMPLEMENTATION_SUMMARY.md`
- `CHANGELOG.md` (this file)

**Modified Files**:
- `glih-frontend/src/glih_frontend/app.py` - New MCP tab, redesigned Ingestion
- `glih-backend/src/glih_backend/mcp/schemas.py` - Sensor value type fix
- `test_mcp_client.py` - Client lifecycle fix
- `README.md` - UI features section
- `README_LINEAGE.md` - Latest release notes

---

## Roadmap

### Version 1.2.0 (Planned)
- [ ] Agent integration with MCP data sources
- [ ] Real-time alerts and notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-facility support
- [ ] Custom report generation

### Version 2.0.0 (Future)
- [ ] Production MCP server connections
- [ ] Authentication and authorization
- [ ] Multi-tenant support
- [ ] Mobile app
- [ ] Advanced AI agents

---

## Support

For issues, questions, or feature requests:
- Check documentation in `/docs` folder
- Review `UI_FEATURES_GUIDE.md` for UI help
- Review `MCP_SETUP_GUIDE.md` for MCP setup
- Check `CHANGELOG.md` for recent changes

---

*Last Updated: October 30, 2025*
