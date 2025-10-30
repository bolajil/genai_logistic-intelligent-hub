#!/bin/bash
# Start all MCP servers in separate terminal windows
# Run this from the mcp-servers directory

echo "Starting all MCP servers..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "✗ Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Python found: $PYTHON_VERSION"

# Check if dependencies are installed
echo "Checking dependencies..."
if python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependencies missing. Installing..."
    pip3 install -r requirements.txt
fi

echo ""
echo "Starting MCP servers in background..."
echo ""

# Start WMS Server
echo "Starting WMS Server (port 8080)..."
python3 wms_server.py > wms_server.log 2>&1 &
WMS_PID=$!
sleep 2

# Start IoT Server
echo "Starting IoT Server (port 8081)..."
python3 iot_server.py > iot_server.log 2>&1 &
IOT_PID=$!
sleep 2

# Start Docs Server
echo "Starting Docs Server (port 8082)..."
python3 docs_server.py > docs_server.log 2>&1 &
DOCS_PID=$!
sleep 2

echo ""
echo "✓ All MCP servers started!"
echo ""
echo "Process IDs:"
echo "  - WMS:  $WMS_PID"
echo "  - IoT:  $IOT_PID"
echo "  - Docs: $DOCS_PID"
echo ""
echo "Servers running on:"
echo "  - WMS:  http://localhost:8080"
echo "  - IoT:  http://localhost:8081"
echo "  - Docs: http://localhost:8082"
echo ""
echo "Testing connectivity..."
sleep 3

# Test each server
for port in 8080 8081 8082; do
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "  ✓ Port $port: OK"
    else
        echo "  ✗ Port $port: Not responding"
    fi
done

echo ""
echo "Logs are being written to:"
echo "  - wms_server.log"
echo "  - iot_server.log"
echo "  - docs_server.log"
echo ""
echo "To stop all servers, run:"
echo "  kill $WMS_PID $IOT_PID $DOCS_PID"
echo ""
echo "Next steps:"
echo "  1. Edit config/glih.toml and set [mcp] enabled = true"
echo "  2. Run: python3 test_mcp_client.py"
echo "  3. Start GLIH backend in another terminal"
echo ""
