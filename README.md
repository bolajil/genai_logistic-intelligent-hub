# GenAI Logistics Intelligence Hub (GLIH)

A modular, enterprise-ready monorepo for logistics AI: ingestion, RAG, agentic workflows, backend APIs, and UI.

## Structure
- `glih-backend/` FastAPI backend APIs
- `glih-frontend/` Streamlit (MVP) or React dashboard
- `glih-agents/` Agentic layer (AnomalyResponder, RouteAdvisor, CustomerNotifier, OpsSummarizer)
- `glih-ingestion/` ETL and normalization
- `glih-eval/` Evaluation and monitoring
- `config/` Project-wide TOML configuration
- `scripts/` Developer scripts (bootstrap, dev)
- `data/` Raw/processed storage (local dev)

## Quickstart (dev)
1. Copy env template and edit:
   - Windows PowerShell:
     ```powershell
     Copy-Item .env.example .env
     ```
   - macOS/Linux:
     ```bash
     cp .env.example .env
     ```
2. Run preflight (creates a venv and installs editable packages):
   - Windows PowerShell:
     ```powershell
     ./preflight.ps1
     ```
   - macOS/Linux:
     ```bash
     bash ./preflight.sh
     source .venv/Scripts/activate
     ```
3. Start backend (dev):
   ```powershell
   pip install -e glih-backend -e glih-frontend -e glih-agents -e glih-ingestion -e glih-eval
   ./.venv/Scripts/python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
   ```
4. Start frontend (dev):
   ```powershell
   streamlit run glih-frontend/src/glih_frontend/app.py
   ```

## Decisions needed (edit `config/glih.toml`)
- Vector store: `chromadb | faiss | pinecone | weaviate`
- Embeddings: `openai | huggingface` and model names
- Object storage: `local | s3 | azure | gcs`
- LLM provider/model: `openai | anthropic | mistral | ...`
- Agent defaults: thresholds, alerting behavior

## Notes
- Python 3.10+
- Packages are editable installs for rapid iteration.
- CI/CD, Docker, and cloud infra can be added in Phase 8.
