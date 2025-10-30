# Start all MCP servers in separate PowerShell windows
# Run this from the mcp-servers directory

Write-Host "Starting all MCP servers..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastapi, uvicorn" 2>$null
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Dependencies missing. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "Starting MCP servers in separate windows..." -ForegroundColor Green
Write-Host ""

# Start WMS Server
Write-Host "Starting WMS Server (port 8080)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python wms_server.py"
Start-Sleep -Seconds 2

# Start IoT Server
Write-Host "Starting IoT Server (port 8081)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python iot_server.py"
Start-Sleep -Seconds 2

# Start Docs Server
Write-Host "Starting Docs Server (port 8082)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python docs_server.py"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✓ All MCP servers started!" -ForegroundColor Green
Write-Host ""
Write-Host "Servers running on:" -ForegroundColor Yellow
Write-Host "  - WMS:  http://localhost:8080" -ForegroundColor White
Write-Host "  - IoT:  http://localhost:8081" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8082" -ForegroundColor White
Write-Host ""
Write-Host "Testing connectivity..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test each server
$servers = @(
    @{Name="WMS"; Port=8080},
    @{Name="IoT"; Port=8081},
    @{Name="Docs"; Port=8082}
)

foreach ($server in $servers) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($server.Port)/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ $($server.Name) Server: OK" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ $($server.Name) Server: Not responding" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit config/glih.toml and set [mcp] enabled = true" -ForegroundColor White
Write-Host "  2. Run: python test_mcp_client.py" -ForegroundColor White
Write-Host "  3. Start GLIH backend in another terminal" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit (servers will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
