#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
( uvicorn glih_backend.api.main:app --reload --port 8000 & )
streamlit run glih-frontend/src/glih_frontend/app.py
