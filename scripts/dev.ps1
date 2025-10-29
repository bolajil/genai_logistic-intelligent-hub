$ErrorActionPreference = 'Stop'
. .\.venv\Scripts\Activate.ps1
$py = Join-Path (Get-Location) ".venv/Scripts/python.exe"
Start-Process powershell -ArgumentList "-NoExit -Command `"$py`" -m uvicorn glih_backend.api.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit -Command `"$py`" -m streamlit run glih-frontend/src/glih_frontend/app.py"
