#!/usr/bin/env bash
set -euo pipefail
echo "[GLIH] Preflight starting..."

# Python check
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python 3.10+ and retry."; exit 1
fi

# Create venv
if [ ! -d .venv ]; then
  echo "[GLIH] Creating virtual environment .venv"
  python3 -m venv .venv
fi

# Activate
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Install editable packages
for pkg in glih-backend glih-frontend glih-agents glih-ingestion glih-eval; do
  if [ -d "$pkg" ]; then
    echo "[GLIH] Installing $pkg (editable)"
    python -m pip install -e "$pkg"
  fi
done

[ -f .env ] || cp .env.example .env

echo "[GLIH] Preflight complete. Next:"
echo "  - Edit config/glih.toml to make decisions"
echo "  - Start backend: uvicorn glih_backend.api.main:app --reload --port 8000"
echo "  - Start frontend: streamlit run glih-frontend/src/glih_frontend/app.py"
