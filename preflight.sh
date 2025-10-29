#!/usr/bin/env bash
set -euo pipefail
echo "[GLIH] Preflight starting..."

# Resolve Python interpreter cross-platform
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
elif command -v py >/dev/null 2>&1; then
  PY="py -3"
else
  echo "Python 3.10+ not found. Install Python and retry."; exit 1
fi

# Create venv
if [ ! -d .venv ]; then
  echo "[GLIH] Creating virtual environment .venv"
  eval "$PY -m venv .venv"
fi

# Activate (supports Linux/macOS and Git Bash on Windows)
if [ -f .venv/bin/activate ]; then
  # Linux/macOS
  # shellcheck source=/dev/null
  source .venv/bin/activate
elif [ -f .venv/Scripts/activate ]; then
  # Git Bash on Windows
  # shellcheck source=/dev/null
  source .venv/Scripts/activate
else
  echo "[GLIH] Could not find venv activate script. Try PowerShell: ./preflight.ps1"; exit 1
fi

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
