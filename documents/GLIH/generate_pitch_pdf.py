"""Generate GLIH Business Pitch Package PDF."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "GLIH_Business_Pitch_Package.pdf")

# ── Colour palette ──────────────────────────────────────────────────────────
DARK_BG   = colors.HexColor("#070d1a")
TEAL      = colors.HexColor("#22d3ee")
AMBER     = colors.HexColor("#f59e0b")
GREEN     = colors.HexColor("#10b981")
RED       = colors.HexColor("#ef4444")
SLATE     = colors.HexColor("#1e3a5f")
LIGHT_TXT = colors.HexColor("#e2e8f0")
MID_TXT   = colors.HexColor("#94a3b8")
WHITE     = colors.white
BLACK     = colors.HexColor("#0f1f3d")

# ── Styles ───────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

cover_title = S("CoverTitle", fontSize=36, textColor=WHITE,
                leading=44, alignment=TA_CENTER, fontName="Helvetica-Bold")
cover_sub   = S("CoverSub",   fontSize=14, textColor=TEAL,
                leading=20, alignment=TA_CENTER, fontName="Helvetica")
cover_meta  = S("CoverMeta",  fontSize=10, textColor=MID_TXT,
                leading=14, alignment=TA_CENTER, fontName="Helvetica")

part_title  = S("PartTitle",  fontSize=22, textColor=TEAL,
                leading=28, fontName="Helvetica-Bold",
                spaceBefore=24, spaceAfter=8)
section_hd  = S("SectionHd",  fontSize=14, textColor=AMBER,
                leading=18, fontName="Helvetica-Bold",
                spaceBefore=16, spaceAfter=6)
sub_hd      = S("SubHd",      fontSize=11, textColor=TEAL,
                leading=15, fontName="Helvetica-Bold",
                spaceBefore=10, spaceAfter=4)
body        = S("Body",       fontSize=9,  textColor=LIGHT_TXT,
                leading=14, fontName="Helvetica", spaceAfter=4)
quote       = S("Quote",      fontSize=9,  textColor=AMBER,
                leading=14, fontName="Helvetica-Oblique",
                leftIndent=20, spaceAfter=6)
bullet_st   = S("BulletSt",   fontSize=9,  textColor=LIGHT_TXT,
                leading=14, fontName="Helvetica",
                leftIndent=16, bulletIndent=4, spaceAfter=2)
code_st     = S("CodeSt",     fontSize=8,  textColor=GREEN,
                leading=12, fontName="Courier",
                leftIndent=16, spaceAfter=2, backColor=DARK_BG)
label_st    = S("LabelSt",    fontSize=8,  textColor=MID_TXT,
                leading=12, fontName="Helvetica-Bold",
                spaceBefore=8, spaceAfter=2)

# ── Helper builders ──────────────────────────────────────────────────────────
def HR(color=SLATE, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceBefore=6, spaceAfter=6)

def P(text, style=body):
    return Paragraph(text, style)

def B(text):
    return Paragraph(f"• &nbsp; {text}", bullet_st)

def tbl(data, col_widths, row_styles=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    base = [
        ("BACKGROUND", (0,0), (-1,0), SLATE),
        ("TEXTCOLOR",  (0,0), (-1,0), TEAL),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLACK, colors.HexColor("#0a1628")]),
        ("TEXTCOLOR",  (0,1), (-1,-1), LIGHT_TXT),
        ("GRID",       (0,0), (-1,-1), 0.3, SLATE),
        ("LEFTPADDING",(0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]
    if row_styles:
        base.extend(row_styles)
    t.setStyle(TableStyle(base))
    return t

def section_block(label, content_flowables):
    """Wrap content in a shaded card."""
    return KeepTogether([
        P(label, section_hd),
        HR(),
        *content_flowables,
        Spacer(1, 8),
    ])

# ── Document setup ───────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.75*inch, bottomMargin=0.75*inch,
    title="GLIH Business Pitch Package",
    author="Lanre Bolaji",
)

def draw_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.restoreState()

story = []

# ════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════════════════════
story += [
    Spacer(1, 1.4*inch),
    P("GLIH", cover_title),
    P("GenAI Logistics Intelligence Hub", cover_sub),
    Spacer(1, 0.3*inch),
    HR(TEAL, 1.5),
    Spacer(1, 0.2*inch),
    P("Business Pitch Package", S("cp2", fontSize=16, textColor=WHITE,
       leading=22, alignment=TA_CENTER, fontName="Helvetica-Bold")),
    Spacer(1, 0.5*inch),
    P("Cold Chain AI · Real-Time Breach Detection · GPT-4o Agents · RAG Compliance", cover_meta),
    Spacer(1, 0.15*inch),
    P("Built for Lineage Logistics &amp; the Cold Chain Industry", cover_meta),
    Spacer(1, 1.6*inch),
    HR(SLATE),
    P("Prepared by: <b>Lanre Bolaji</b>   |   AI Engineer &amp; Platform Author   |   2025",
      S("covfoot", fontSize=9, textColor=MID_TXT, alignment=TA_CENTER,
        fontName="Helvetica", leading=13)),
    P("Confidential — For Review Purposes Only", cover_meta),
    PageBreak(),
]

# ════════════════════════════════════════════════════════════════════════════
# PART 1 — DEMO SPEECH
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 1 — DEMO SPEECH", part_title), HR(TEAL, 1)]

speech = [
    ("OPENING — Hook", "60 seconds", [
        "Deliver standing, no slides. Direct eye contact.",
        '"Every year, the cold chain industry loses between <b>$35–$50 billion</b> in spoiled goods, compliance penalties, and delayed shipments. The root cause isn\'t the weather — it\'s the <b>gap between when a problem happens and when a human being finds out.</b>"',
        '"Lineage Logistics moves more temperature-controlled product than any company on earth. You have the network, the facilities, the fleet. What I\'ve built gives you the <b>intelligence layer</b> that sits on top of all of it — detecting problems in seconds, recommending actions in real time, and documenting everything automatically for FDA compliance."',
        '"This is GLIH. The GenAI Logistics Intelligence Hub. Let me show you what it does."',
    ]),
    ("SECTION 1 — Operations Dashboard", "90 seconds", [
        "<i>Navigate to /dashboard</i>",
        '"This is the nerve center. The moment a dispatcher opens their shift, they see everything that matters — right now. <b>847 active shipments. 3 alerts. 99.1% temperature compliance.</b>"',
        '"This Live Sensor Feed refreshes every 5 seconds. CHI-ATL-2025-089 is running at +5.6°C — that\'s a BREACH. The system flagged it automatically. No spreadsheet. No radio call."',
        '"Down here is the Agent Activity panel — AI agents already working the problem. AnomalyResponder fired 3 minutes ago. CustomerNotifier sent an email 7 minutes ago. All logged, all audit-ready."',
    ]),
    ("SECTION 2 — AI Agents", "2 minutes", [
        "<i>Navigate to /agents — select AnomalyResponder — hit Run</i>",
        '"In under 4 seconds: identified the breach, cross-referenced your cold chain SOP, generated a step-by-step action plan, assessed spoilage risk, and cited the exact SOP clause. SOP-COLD-CHAIN-003. That\'s your document. Your rule. Your compliance record — generated automatically."',
        '"Four agents. Four jobs that currently require four people making judgment calls under time pressure. This platform makes those calls in seconds — and shows its reasoning every time."',
    ]),
    ("SECTION 3 — Knowledge Base & RAG Query", "90 seconds", [
        "<i>Navigate to /documents — type a query</i>",
        '"Every answer those agents give is grounded in real documents — your SOPs, USDA FSIS guidelines, GCCA best practices. This isn\'t a chatbot making things up. It\'s a retrieval-augmented system — it reads your actual policy before it speaks."',
        '"GPT-4o just read 4 chunks from the GCCA Best Practices Guide and your cold chain SOP, synthesized the answer, and cited the exact source. If your compliance team needs to prove what procedure was followed — it\'s right here."',
    ]),
    ("SECTION 4 — Alerts & Shipments", "60 seconds", [
        "<i>Navigate to /alerts then /shipments</i>",
        '"Alerts prioritized by severity. Color-coded. Nothing gets buried."',
        '"Shipments — search and filter across your entire active fleet. Every shipment. Every status. Every temperature reading. One screen."',
    ]),
    ("CLOSING — The Ask", "60 seconds", [
        "<i>Return to Dashboard. Pause. Speak slowly.</i>",
        '"Lineage Logistics processed over 2 billion cases of product last year. Each percentage point improvement in temperature compliance translates to tens of millions of dollars in recovered value."',
        '"This platform is built. It\'s running. The AI is wired. The agents work. The knowledge base is loaded with your industry\'s own standards."',
        '"I\'m not here to sell you a concept. I\'m here to show you something that works — and to have a conversation about how we move it into your environment. I have three specific proposals. I\'d like to walk you through them."',
    ]),
]

for title, timing, lines in speech:
    items = [P(f'<font color="#f59e0b"><b>{title}</b></font>  <font color="#94a3b8">— {timing}</font>', sub_hd)]
    for line in lines:
        if line.startswith('"'):
            items.append(P(line, quote))
        else:
            items.append(B(line))
    items.append(Spacer(1, 4))
    story += items

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# PART 2 — ROI & BUSINESS CASE
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 2 — ROI &amp; BUSINESS CASE", part_title), HR(TEAL, 1)]

story.append(section_block("Why GLIH Saves Lineage Money", [
    tbl(
        [["PROBLEM TODAY", "CURRENT COST", "GLIH IMPACT"],
         ["Late breach detection (avg 22 min)", "$800–$4,200 per incident", "Detection in <60 sec — 95% loss window reduction"],
         ["Manual shift handoff reports × 400 facilities", "~$8M/year in supervisor labor", "OpsSummarizer generates in 30 seconds"],
         ["Compliance documentation (manual)", "$1.2M/yr + $500K audit penalty risk", "Auto-generated, traceable, audit-ready"],
         ["Customer notification delays", "SLA penalties + churn", "CustomerNotifier sends within minutes"],
         ["Route decisions by feel, not data", "Suboptimal reroutes, late deliveries", "RouteAdvisor — data-backed in real time"],
         ["SOP knowledge locked in PDFs", "Training lag, inconsistent response", "Any agent can query SOPs in plain English"]],
        [2.1*inch, 1.9*inch, 2.5*inch],
    ),
]))

story.append(section_block("Conservative 12-Month Value Estimate", [
    tbl(
        [["VALUE DRIVER", "CALCULATION", "ANNUAL VALUE"],
         ["Faster breach response (80% improvement)", "60K events × $1,200 × 80%", "$57,600,000"],
         ["Supervisor report labor saved", "400 fac × 2 shifts × 2hr × $45 × 365", "$26,280,000"],
         ["Compliance audit risk reduction", "Conservative estimate", "$2,000,000"],
         ["Customer churn prevention (1% retention)", "Based on revenue base", "$15,000,000+"],
         ["TOTAL ESTIMATED ANNUAL VALUE", "", "~$100,000,000+"]],
        [2.5*inch, 2.3*inch, 1.7*inch],
        row_styles=[
            ("BACKGROUND", (0,5), (-1,5), colors.HexColor("#0d2a1a")),
            ("TEXTCOLOR",  (0,5), (-1,5), GREEN),
            ("FONTNAME",   (0,5), (-1,5), "Helvetica-Bold"),
        ]
    ),
    Spacer(1, 6),
    P("<i>Even at 10% of this estimate — $10M/year — from a platform that already exists.</i>", quote),
]))

story.append(section_block("Competitive Positioning", [
    tbl(
        [["FEATURE", "GLIH", "LEGACY WMS", "GENERIC BI"],
         ["Real-time AI agent response", "YES", "NO", "NO"],
         ["SOP-grounded answers", "YES", "NO", "NO"],
         ["Auto-generated compliance records", "YES", "NO", "Partial"],
         ["Hybrid BM25 + vector search", "YES", "NO", "NO"],
         ["Built for cold chain specifically", "YES", "Partial", "NO"],
         ["Deployable in days, not months", "YES", "NO (18mo avg)", "Partial"]],
        [2.8*inch, 1.1*inch, 1.1*inch, 1.1*inch],
        row_styles=[
            ("TEXTCOLOR", (1,1), (1,-1), GREEN),
            ("TEXTCOLOR", (2,1), (3,-1), RED),
        ]
    ),
]))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# PART 3 — OUTREACH STRATEGY
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 3 — OUTREACH STRATEGY", part_title), HR(TEAL, 1)]

story.append(section_block("Who to Target Inside Lineage Logistics", [
    tbl(
        [["TITLE", "WHY THEY CARE", "HOW TO REACH"],
         ["Chief Technology Officer", "Platform architecture, build-vs-buy", "LinkedIn + email"],
         ["Chief Operating Officer", "P&L impact, breach reduction, compliance", "LinkedIn + warm intro"],
         ["VP of Innovation / Digital Transformation", "This is literally their job", "LinkedIn + tech conferences"],
         ["VP of Operations", "Daily pain — dispatchers, breach reports", "LinkedIn"],
         ["Director of Food Safety & Compliance", "Audit trails, SOP enforcement, GFSI", "LinkedIn + industry forums"],
         ["Head of Data Science / AI", "Technical credibility conversation", "GitHub + LinkedIn"]],
        [2.0*inch, 2.5*inch, 2.0*inch],
    ),
]))

story.append(section_block("5-Step Outreach Sequence", [
    P("<b>Step 1 — Polish Your Digital Presence (Week 1)</b>", sub_hd),
    B("Push GLIH to a public GitHub repo with README, demo GIF, and architecture diagram"),
    B("Record a 3-minute Loom video demo"),
    B('Update LinkedIn: <i>"Built GenAI cold chain intelligence platform — real-time AI agents for temperature compliance, breach response, and operational automation"</i>'),
    P("<b>Step 2 — LinkedIn Warm Outreach (Week 2)</b>", sub_hd),
    P('<i>"Hi [Name] — I\'ve built a working AI platform specifically for cold chain operations — real-time breach detection, GPT-4o agents grounded in GCCA and FSIS SOPs, automated compliance documentation, and WMS connector architecture. I\'d love to show you a 15-minute live demo. No pitch deck — just a working system. Would you be open to a quick call?"</i>', quote),
    P("<b>Step 3 — Industry Channels (Week 2–3)</b>", sub_hd),
    B("Post demo video on LinkedIn: #coldchain #supplychain #genai #logistics"),
    B("Submit to GCCA member news — they publish member innovations"),
    B("Post on Food Logistics and Supply Chain Dive industry sites"),
    P("<b>Step 4 — Conference Presence (Month 2)</b>", sub_hd),
    B("GCCA Annual Conference — Lineage executives attend every year"),
    B("ProMat / Modex — Supply chain technology show, Chicago"),
    B("Gartner Supply Chain Symposium — Executive-level buyers"),
    P("<b>Step 5 — Warm Introduction Path</b>", sub_hd),
    B("Find 2nd-degree connections to Lineage on LinkedIn"),
    B("Reach out to Lineage's VC investors — Stonepeak, Bay Grove Capital"),
]))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# PART 4 — LEGAL FRAMEWORK & ENGAGEMENT OPTIONS
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 4 — LEGAL FRAMEWORK &amp; ENGAGEMENT OPTIONS", part_title), HR(TEAL, 1)]

story.append(section_block("Before Any Conversation — Protect Yourself First", [
    B("Document your invention date — email yourself the GitHub commit history and screenshots"),
    B("Send a Mutual NDA before every demo — both parties protected"),
    B("<b>Do NOT sign their NDA first</b> — large company NDAs can strip your IP rights"),
    B("Keep the GitHub repo private until a deal is signed"),
]))

for opt_title, opt_sub, opt_items, opt_table in [
    (
        "Option A — Employment + IP Transfer",
        "Lineage hires you. Platform transfers as signing bonus or separately.",
        [
            "Signing bonus: $75,000–$200,000 (platform transfer value)",
            "Title: Senior Principal Engineer, AI or Director of AI Products",
            "Salary: $160,000–$220,000 (Senior AI roles in logistics tech)",
            "Equity/RSUs — they IPO'd in 2024",
            "Inventor credit and public attribution of GLIH",
        ],
        None
    ),
    (
        "Option B — Outright Purchase (Acquisition)",
        "Lineage buys GLIH as a software asset. Lump sum. Optional consulting retainer.",
        [
            "Opening ask: $2,000,000–$4,000,000 for full IP transfer",
            "12-month implementation consulting retainer: $15,000–$25,000/month",
            "Right to reference platform in your portfolio",
            "Performance bonus tied to measured ROI (optional)",
        ],
        [["VALUATION METHOD", "ESTIMATE"],
         ["Development cost replacement (time × market rate)", "$180,000–$400,000"],
         ["3× annual value to buyer (10% ROI case)", "$3,000,000–$10,000,000"],
         ["Comparable AI tool acquisitions (early-stage)", "$500,000–$2,000,000"]]
    ),
    (
        "Option C — Licensing + Consulting (Recommended if they hesitate)",
        "You retain ownership. Lineage pays monthly license. You consult on customisation.",
        [],
        [["TIER", "WHAT'S INCLUDED", "PRICE"],
         ["Pilot (3 facilities, 90 days)", "Platform access + setup + support", "$10,000–$15,000/month"],
         ["Regional (50 facilities)", "Full platform + custom agents + SLA", "$35,000/month"],
         ["Enterprise (400+ facilities)", "Full network + WMS integration + dedicated support", "$120,000–$200,000/month"]]
    ),
]:
    items = [P(f"<b>{opt_title}</b>", sub_hd), P(opt_sub, body)]
    if opt_table:
        items.append(tbl(opt_table, [3.0*inch, 1.7*inch] if len(opt_table[0])==2 else [1.5*inch, 3.0*inch, 2.0*inch]))
        items.append(Spacer(1, 6))
    for item in opt_items:
        items.append(B(item))
    story.append(section_block("", items))

story.append(section_block("Engagement Decision Tree", [
    P('<font color="#22d3ee">Lineage says "We love it, we want it"</font>', sub_hd),
    B("They want you too → Option A (negotiate hard on price + title)"),
    B("They want the platform → Option B (never go below $500K)"),
    B("They want to try first → Option C (pilot, then escalate to B)"),
    P('<font color="#22d3ee">Lineage says "Interesting, we need to evaluate"</font>', sub_hd),
    B("Offer Option C pilot → 90 days, 3 facilities, $25K total"),
    P('<font color="#22d3ee">Lineage says "We might build something similar internally"</font>', sub_hd),
    B("Send the NDA immediately. Document your invention date. This is a sign they see value."),
]))

story.append(section_block("Legal Documents You Need", [
    tbl(
        [["DOCUMENT", "PURPOSE", "WHEN"],
         ["Mutual NDA", "Protect IP before every demo", "Before first conversation"],
         ["IP Assignment Agreement", "For any sale or employment transfer", "At signing"],
         ["Software License Agreement", "For Option C licensing", "Pilot start"],
         ["Consulting Services Agreement", "For any implementation work", "Post-deal"],
         ["Letter of Intent (LOI)", "Non-binding first step", "Before full contract"]],
        [2.0*inch, 2.5*inch, 2.0*inch],
    ),
    Spacer(1, 6),
    P("<b>Recommended:</b> Hire an IP/tech attorney for 2 hours ($400–$800) to review any NDA or LOI before signing.", quote),
]))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# PART 5 — VIDEO PRODUCTION GUIDE
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 5 — VIDEO PRODUCTION GUIDE", part_title), HR(TEAL, 1)]

story.append(section_block("Tools (Free or Cheap)", [
    tbl(
        [["TOOL", "USE", "COST"],
         ["Loom", "Screen record with face cam — tracks who watched", "Free"],
         ["OBS Studio", "Full screen + webcam overlay, highest quality", "Free"],
         ["Descript", "Auto-transcription + trim silence + captions", "Free tier"],
         ["Canva Video", "Add title cards, lower thirds, captions", "Free"],
         ["ElevenLabs", "AI voiceover if narration-only version needed", "Free tier"]],
        [1.5*inch, 3.5*inch, 1.5*inch],
    ),
]))

story.append(section_block("3-Minute Video Script", [
    P("<b>[0:00–0:15] Title card + hook</b>", sub_hd),
    P("<i>Show: GLIH logo on dark background</i>", quote),
    P('"This is GLIH — a GenAI platform I built for cold chain logistics. Let me show you what it does in 3 minutes."', quote),
    P("<b>[0:15–0:45] Dashboard</b>", sub_hd),
    P("<i>Show: Live dashboard, sensor feed updating</i>", quote),
    P('"Live sensor data, active alerts, AI agent activity — all in one view. The sensor feed updates every 5 seconds. This breach was caught automatically."', quote),
    P("<b>[0:45–1:30] AI Agents — the money shot</b>", sub_hd),
    P("<i>Show: Agents page → select AnomalyResponder → hit Run → watch result</i>", quote),
    P('"I hit Run — and in under 4 seconds it reads your SOP, identifies the breach, generates an action plan, assesses spoilage risk, and cites the exact compliance document it used. GPT-4o grounded in your actual policies."', quote),
    P("<b>[1:30–2:00] Documents RAG</b>", sub_hd),
    P('"The knowledge base lets any dispatcher ask questions in plain English — and get answers from your own SOPs. Every answer cited. Every query logged."', quote),
    P("<b>[2:00–2:30] Alerts + Shipments</b>", sub_hd),
    P('"Alerts by severity. Shipments searchable. No spreadsheets."', quote),
    P("<b>[2:30–3:00] Closing — face cam</b>", sub_hd),
    P('"This platform is built, running, and ready for a pilot. If you want to see what AI can actually do — not a concept, a working system — I\'d love to talk. Link in the description."', quote),
]))

story.append(section_block("Production Tips", [
    B("Record at 1920×1080 — browser full screen, dark mode, zoom to 110%"),
    B("Use a USB microphone — audio quality matters more than video quality"),
    B("Add captions — 85% of LinkedIn videos are watched muted"),
    B("Set thumbnail to the dashboard with a breach badge visible"),
    B("Upload to Loom (tracks who watched) + YouTube unlisted (for embedding)"),
    B("Target runtime: 2:45–3:15 — sweet spot for LinkedIn"),
]))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# PART 6 — 30-DAY ACTION PLAN
# ════════════════════════════════════════════════════════════════════════════
story += [P("PART 6 — YOUR 30-DAY ACTION PLAN", part_title), HR(TEAL, 1)]

story.append(tbl(
    [["WEEK", "ACTIONS"],
     ["Week 1", "Fix backend, re-ingest all documents, record Loom video, write GitHub README"],
     ["Week 2", "Update LinkedIn, send first 5 outreach messages to Lineage contacts"],
     ["Week 3", "Post demo video publicly on LinkedIn, get 3 warm intro requests"],
     ["Week 4", "First call or live demo — have NDA ready, have Option A/B/C proposal printed"]],
    [1.0*inch, 5.5*inch],
))

story.append(Spacer(1, 20))

story.append(section_block("Quick Reference Card — Keep This in the Room", [
    P("<b>What it is:</b> GenAI platform for cold chain logistics — 4 AI agents | GPT-4o | RAG on SOPs | real-time monitoring", body),
    P("<b>Their problem:</b> Late breach detection → spoilage → penalties → churn", body),
    P("<b>Your solution:</b> 60-second detection → auto-remediation → auto-documentation", body),
    P("<b>The number:</b> ~$100M+/year addressable value for a network Lineage's size", body),
    Spacer(1, 6),
    tbl(
        [["OPTION", "STRUCTURE", "FLOOR PRICE"],
         ["A — Employment", "Hire + IP transfer signing bonus", "$200K–$300K signing + $220K–$280K salary"],
         ["B — Acquisition", "Full buyout + consulting retainer", "$2,000,000 minimum"],
         ["C — License (recommended first)", "Monthly license, you retain ownership", "$10K–$15K/month pilot"]],
        [1.2*inch, 2.8*inch, 2.5*inch],
    ),
    Spacer(1, 8),
    P("<b>Non-negotiables:</b>", sub_hd),
    B("Always make them sign the NDA before the demo"),
    B("Never accept less than $4,000,000 for a full platform buyout"),
    B("Keep the GitHub repo private until a deal is agreed"),
]))

# ── Build ────────────────────────────────────────────────────────────────────
doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)
print(f"PDF saved: {OUTPUT}")
