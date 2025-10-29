Param(
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
Write-Host "[GLIH] Preflight starting..." -ForegroundColor Cyan

# Python check
try {
  $pyVersion = (& python --version) 2>$null
} catch {
  try { $pyVersion = (& py --version) } catch { throw "Python not found. Install Python 3.10+ and retry." }
}
Write-Host "[GLIH] Using $pyVersion"

# Create venv
if (-not (Test-Path .\.venv) -or $Force) {
  Write-Host "[GLIH] Creating virtual environment .venv"
  & python -m venv .venv
}

# Activate
$venvActivate = Join-Path (Get-Location) ".venv/Scripts/Activate.ps1"
. $venvActivate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install editable packages
$packages = @(
  "glih-backend",
  "glih-frontend",
  "glih-agents",
  "glih-ingestion",
  "glih-eval"
)
foreach ($pkg in $packages) {
  if (Test-Path $pkg) {
    Write-Host "[GLIH] Installing $pkg (editable)"
    python -m pip install -e $pkg
  }
}

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "[GLIH] Created .env from template"
}

Write-Host "[GLIH] Preflight complete. Next:"
Write-Host "  - Edit config/glih.toml to make decisions"
Write-Host "  - Start backend: uvicorn glih_backend.api.main:app --reload --port 8000"
Write-Host "  - Start frontend: streamlit run glih-frontend/src/glih_frontend/app.py"
