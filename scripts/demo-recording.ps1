# ============================================================================
# GLIH DEMO RECORDING SCRIPT
# GenAI Logistics Intelligence Hub - Live Demo Automation
# ============================================================================
# 
# INSTRUCTIONS:
# 1. Start OBS/Loom recording FIRST
# 2. Run this script: .\demo-recording.ps1
# 3. Follow the on-screen prompts for your speech
# 4. The script will auto-navigate pages with timing
#
# TOTAL RUNTIME: ~7 minutes
# ============================================================================

$host.UI.RawUI.WindowTitle = "GLIH Demo Script"
$BASE_URL = "http://localhost:9000"

function Show-Prompt {
    param([string]$Section, [string]$Duration, [string]$Speech, [ConsoleColor]$Color = "Cyan")
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor $Color
    Write-Host " $Section ($Duration)" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor $Color
    Write-Host ""
    Write-Host $Speech -ForegroundColor White
    Write-Host ""
}

function Countdown {
    param([int]$Seconds)
    for ($i = $Seconds; $i -gt 0; $i--) {
        Write-Host "`r  ⏱  $i seconds remaining...  " -NoNewline -ForegroundColor DarkGray
        Start-Sleep -Seconds 1
    }
    Write-Host "`r  ✓  Moving to next section...    " -ForegroundColor Green
}

# ============================================================================
# PRE-DEMO CHECKLIST
# ============================================================================
Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "  ║           GLIH DEMO RECORDING SCRIPT                      ║" -ForegroundColor Magenta
Write-Host "  ║     GenAI Logistics Intelligence Hub                      ║" -ForegroundColor Magenta
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Host "  PRE-FLIGHT CHECKLIST:" -ForegroundColor Yellow
Write-Host "  ☐ Backend running on port 9001" -ForegroundColor White
Write-Host "  ☐ Frontend running on port 9000" -ForegroundColor White
Write-Host "  ☐ Browser zoom set to 110%" -ForegroundColor White
Write-Host "  ☐ Browser in full screen (F11)" -ForegroundColor White
Write-Host "  ☐ OBS/Loom recording STARTED" -ForegroundColor White
Write-Host "  ☐ Microphone ready" -ForegroundColor White
Write-Host ""
Write-Host "  Press ENTER when ready to begin..." -ForegroundColor Green
Read-Host

# ============================================================================
# SECTION 0: LOGIN (10 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 0: LOGIN" "10 sec" @"
[Login as Admin]
- Username: admin
- Password: lineage2026

Quick login, then we go to Dashboard.
"@

Start-Process "$BASE_URL/login"
Countdown 10

# ============================================================================
# SECTION 1: DASHBOARD (90 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 1: OPERATIONS DASHBOARD" "90 sec" @"
SPEECH:

"This is the nerve center. The moment a dispatcher opens their shift, 
they see everything that matters - right now. 847 active shipments. 
3 alerts. 99.1% temperature compliance."

"This Live Sensor Feed refreshes every 5 seconds. CHI-ATL-2025-089 
is running at +5.6C - that's a BREACH. The system flagged it 
automatically. No spreadsheet. No radio call."

"Down here is the Agent Activity panel - AI agents already working 
the problem. AnomalyResponder fired 3 minutes ago. CustomerNotifier 
sent an email 7 minutes ago. All logged, all audit-ready."

ACTIONS:
- Point to KPI cards at top
- Highlight the BREACH badge in sensor feed
- Scroll to show Agent Activity panel
"@

Start-Process "$BASE_URL/dashboard"
Countdown 90

# ============================================================================
# SECTION 2: AI AGENTS (120 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 2: AI AGENTS" "2 min" @"
SPEECH:

"Let me show you the agents. These are GPT-4o powered AI workers 
that handle specific operational tasks."

[Click AnomalyResponder → Select a preset → Click RUN]

"In under 4 seconds: identified the breach, cross-referenced your 
cold chain SOP, generated a step-by-step action plan, assessed 
spoilage risk, and cited the exact SOP clause. SOP-COLD-CHAIN-003. 
That's your document. Your rule. Your compliance record - generated 
automatically."

"Four agents. Four jobs that currently require four people making 
judgment calls under time pressure. This platform makes those calls 
in seconds - and shows its reasoning every time."

ACTIONS:
- Select AnomalyResponder agent
- Pick a demo preset (Breach → Sysco)
- Click RUN and wait for result
- Highlight the SOP citation in the response
- Optionally show CustomerNotifier with dispatcher selector
"@

Start-Process "$BASE_URL/agents"
Countdown 120

# ============================================================================
# SECTION 3: KNOWLEDGE BASE / DOCUMENTS (90 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 3: KNOWLEDGE BASE & RAG" "90 sec" @"
SPEECH:

"Every answer those agents give is grounded in real documents - 
your SOPs, USDA FSIS guidelines, GCCA best practices. This isn't 
a chatbot making things up. It's a retrieval-augmented system - 
it reads your actual policy before it speaks."

[Type a query like: "What is the correct procedure for a temperature breach?"]

"GPT-4o just read 4 chunks from the GCCA Best Practices Guide and 
your cold chain SOP, synthesized the answer, and cited the exact 
source. If your compliance team needs to prove what procedure was 
followed - it's right here."

ACTIONS:
- Navigate to Documents page
- Type a natural language query
- Show the RAG response with citations
- Highlight source documents referenced
"@

Start-Process "$BASE_URL/documents"
Countdown 90

# ============================================================================
# SECTION 4: ALERTS (30 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 4: ALERTS" "30 sec" @"
SPEECH:

"Alerts prioritized by severity. Color-coded. Nothing gets buried."

ACTIONS:
- Show the alerts list
- Point out HIGH severity items in red
- Show the filtering/sorting options
"@

Start-Process "$BASE_URL/alerts"
Countdown 30

# ============================================================================
# SECTION 5: SHIPMENTS (30 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 5: SHIPMENTS" "30 sec" @"
SPEECH:

"Shipments - search and filter across your entire active fleet. 
Every shipment. Every status. Every temperature reading. One screen."

ACTIONS:
- Show shipment list
- Use search to filter
- Click on a shipment to show details
"@

Start-Process "$BASE_URL/shipments"
Countdown 30

# ============================================================================
# SECTION 6: SETTINGS - DISPATCHERS (30 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 6: DISPATCHER MANAGEMENT" "30 sec" @"
SPEECH:

"Admin can manage dispatcher accounts right here. Each dispatcher's 
name and title automatically appears in customer notifications - 
personalized, professional, audit-ready."

ACTIONS:
- Navigate to Settings → Dispatchers tab
- Show the dispatcher list
- Briefly show Add Dispatcher form
"@

Start-Process "$BASE_URL/settings"
Countdown 30

# ============================================================================
# SECTION 7: MCP CONNECTORS (60 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 7: MCP CONNECTORS" "60 sec" @"
SPEECH:

"This is where GLIH connects to the real world. MCP - Model Context 
Protocol - is the standard that lets AI agents talk to external systems."

[Click on Connection Mode tab]

"Four connectors out of the box:

GPS-Trace - Real-time truck tracking, mileage, engine hours, geofences. 
Every truck in your fleet, live on the map.

OpenWeatherMap - Weather forecasts for route planning. The system knows 
if there's a heatwave on the I-95 corridor before your dispatcher does.

IoT Sensors - Temperature sensors, door status, humidity monitoring. 
This is where the breach data comes from - direct from the trailer.

Traffic & Routing - Real-time traffic for ETA optimization. Reroute 
around a 3-hour backup before the driver even sees it."

[Click on API Keys & IoT tab]

"Each connector can run in DEMO mode with simulated data, or REAL mode 
with your actual API keys. Plug in your credentials, hit Test, and 
you're live."

ACTIONS:
- Show Connection Mode tab (DEMO vs REAL status)
- Click API Keys & IoT tab
- Show configuration fields for each connector
- Highlight the Test Connection button
"@

Start-Process "$BASE_URL/settings"
Countdown 60

# ============================================================================
# SECTION 8: CLOSING (60 seconds)
# ============================================================================
Clear-Host
Show-Prompt "SECTION 8: CLOSING" "60 sec" @"
SPEECH:

[Return to Dashboard. Pause. Speak slowly.]

"Lineage Logistics processed over 2 billion cases of product last 
year. Each percentage point improvement in temperature compliance 
translates to tens of millions of dollars in recovered value."

"This platform is built. It's running. The AI is wired. The agents 
work. The knowledge base is loaded with your industry's own standards."

"I'm not here to sell you a concept. I'm here to show you something 
that works - and to have a conversation about how we move it into 
your environment."

[Face cam if using Loom - look directly at camera]

"If you want to see what AI can actually do for cold chain logistics - 
not a concept, a working system - I'd love to talk."

ACTIONS:
- Return to Dashboard
- End with dashboard visible
- Stop recording
"@

Start-Process "$BASE_URL/dashboard"
Countdown 60

# ============================================================================
# END
# ============================================================================
Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║              DEMO COMPLETE!                               ║" -ForegroundColor Green
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  ✓ Stop your recording now" -ForegroundColor Yellow
Write-Host ""
Write-Host "  POST-PRODUCTION TIPS:" -ForegroundColor Cyan
Write-Host "  • Add captions (85% of LinkedIn videos watched muted)" -ForegroundColor White
Write-Host "  • Target runtime: 2:45 - 3:15 (trim silence with Descript)" -ForegroundColor White
Write-Host "  • Thumbnail: Dashboard with BREACH badge visible" -ForegroundColor White
Write-Host "  • Upload to Loom (tracks views) + YouTube unlisted" -ForegroundColor White
Write-Host ""
Write-Host "  TOOLS:" -ForegroundColor Cyan
Write-Host "  • Descript - Auto-trim silence, add captions (Free)" -ForegroundColor White
Write-Host "  • Canva - Title cards, lower thirds (Free)" -ForegroundColor White
Write-Host ""
