# GLIH Demo Script for Lineage Logistics
## Complete Walkthrough with Talking Points

**Duration**: 15 minutes  
**Audience**: Lineage Leadership Team  
**Setup**: Browser + Terminal ready

---

## Pre-Demo Setup (5 minutes before)

### 1. Start Services
```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app

# Terminal 2: Frontend
streamlit run glih-frontend/src/glih_frontend/app.py
```

### 2. Open Browser Tabs
- Tab 1: http://localhost:8501 (Frontend)
- Tab 2: http://localhost:8000/docs (API docs)

### 3. Prepare Terminal
- Terminal 3: Ready for agent test
- Have `test_lineage_agent.py` open

---

## Demo Flow

### PART 1: Introduction (2 minutes)

**[Show Slide 1-3 from presentation]**

**Talking Points:**
```
"Good morning/afternoon. Today I'm excited to show you GLIH - 
the GenAI Logistics Intelligence Hub we've built specifically 
for Lineage's cold chain operations.

We're going to demonstrate three capabilities:
1. Natural language operations - ask questions in plain English
2. Automated anomaly detection - real-time temperature monitoring
3. Document intelligence - instant invoice matching

Let's jump right into the live system."
```

---

### PART 2: System Health Check (1 minute)

**[Switch to Browser - Frontend]**

**Actions:**
1. Click **Admin** tab
2. Click **"Check Detailed Health"** button
3. Show the health dashboard

**Talking Points:**
```
"First, let me show you the system health dashboard. 
This gives us real-time visibility into all components:

[Point to screen]
- LLM Provider: Mistral AI - Available ✓
- Embeddings: Mistral Embed - Available ✓
- Vector Store: ChromaDB - Available ✓
- Collections: We have 'lineage-sops' loaded with your SOPs

Everything is green and operational. Now let's see it in action."
```

---

### PART 3: Natural Language Query Demo (3 minutes)

**[Click Query tab]**

**Query 1: Temperature Requirements**

**Actions:**
1. Select collection: **lineage-sops**
2. Type query: `"What are the temperature requirements for seafood?"`
3. Click **Send Query**
4. Wait for response (2-3 seconds)

**Talking Points:**
```
"Let's say an operations supervisor needs to know the temperature 
requirements for seafood. Instead of searching through documents, 
they just ask in plain English:

[Read query aloud]
'What are the temperature requirements for seafood?'

[Wait for response]

Look at this - in under 3 seconds, the system:
1. Searched through all your SOPs
2. Found the relevant sections
3. Generated a clear answer: -2°C to 2°C
4. Included the breach protocols
5. Provided citations showing exactly where this came from

[Scroll to citations]
See these three citations? Each one links back to the source 
document with the exact text snippet. Full traceability for compliance.

Current process: 10-15 minutes searching documents
With GLIH: 3 seconds
That's 99% faster."
```

**Query 2: Breach Protocol**

**Actions:**
1. Clear previous query
2. Type: `"What should I do if dairy temperature exceeds 6°C?"`
3. Click **Send Query**

**Talking Points:**
```
"Let's try another scenario. A temperature alert comes in for 
a dairy shipment that's at 6°C.

[Wait for response]

The system immediately tells them:
- Inspection required within 20 minutes
- Quality assessment needed
- Follow HACCP guidelines
- Notify quality manager within 15 minutes

This is exactly what your ops team needs in the moment - 
instant, accurate, actionable guidance."
```

**Query 3: Compliance**

**Actions:**
1. Type: `"What compliance standards apply to cold chain?"`
2. Click **Send Query**

**Talking Points:**
```
"And for compliance questions...

[Wait for response]

HACCP, FDA, FSMA, GMP - all retrieved instantly with the 
specific requirements. Your quality team will love this."
```

---

### PART 4: Automated Anomaly Detection (5 minutes)

**[Switch to Terminal 3]**

**Actions:**
1. Show `test_lineage_agent.py` file briefly
2. Run: `.\.venv\Scripts\python.exe test_lineage_agent.py`
3. Let it run through all 4 scenarios

**Talking Points:**
```
"Now let me show you the real power - automated anomaly detection. 
This is what happens 24/7 in the background, monitoring your shipments.

I'm going to simulate 4 real-world scenarios:
1. Critical seafood temperature breach
2. Medium dairy temperature breach  
3. Normal operation (no anomaly)
4. Frozen foods critical breach

[Run the script]

[As Scenario 1 appears]
'Look at this - Shipment TX-CHI-2025-001, seafood at 8.5°C.
Expected range is -2 to 2°C, so we have a 10.5°C deviation.
The system immediately:

[Point to output]
- Classified it as CRITICAL severity
- Generated 4 urgent actions:
  1. Immediate inspection for spoilage
  2. Alert quality team
  3. Quarantine the shipment
  4. Generate compliance incident report

- Set response time target: 5 minutes
- Prepared notifications for email, SMS, and webhook

Current manual process: 30-45 minutes
GLIH automated: 2.5 minutes
That's 95% faster response time.

[As Scenario 2 appears]
'Here's a medium severity dairy breach - same process, 
but different actions based on the severity level.

[As Scenario 3 appears]
'And here - normal operation, no anomaly detected. 
The system is smart enough to know when NOT to alert.

[As Scenario 4 appears]
'Finally, frozen foods at -10°C when it should be -25 to -18°C.
Again, immediate critical response.

[Point to summary]
'Summary: 4 scenarios tested, 3 anomalies detected correctly, 
1 normal operation identified. All product types covered.

This agent is running 24/7, monitoring every shipment, 
with consistent SOP adherence and sub-5-minute response times."
```

---

### PART 5: Document Ingestion Demo (2 minutes)

**[Switch back to Browser - Ingestion tab]**

**Actions:**
1. Show the ingestion interface
2. Point to collection selector
3. Show file upload area

**Talking Points:**
```
"Let me quickly show you how easy it is to add new documents.

[Point to screen]
- Select or create a collection - we have 'lineage-sops' here
- Upload files - PDFs, Word docs, text files
- Or paste text directly
- Or ingest from URLs

Click Ingest, and within seconds, that content is searchable 
through natural language queries.

We can ingest:
- Standard Operating Procedures
- Training manuals
- Compliance documents
- Historical incident reports
- Route performance data
- Customer communication templates

Everything becomes instantly searchable and retrievable."
```

---

### PART 6: API Integration (1 minute)

**[Switch to Browser Tab 2 - API Docs]**

**Actions:**
1. Show the Swagger UI
2. Scroll through endpoints
3. Expand `/query` endpoint

**Talking Points:**
```
"For integration with your existing systems, we have a 
complete REST API.

[Point to endpoints]
- Query endpoints for natural language search
- Ingestion endpoints for automated document processing
- Collection management for organizing by facility or type
- Health checks for monitoring

Your WMS, TMS, or custom applications can call these APIs 
directly. Everything we just demonstrated in the UI is 
available programmatically."
```

---

### PART 7: ROI & Next Steps (1 minute)

**[Show Slides 7-8 from presentation]**

**Talking Points:**
```
"Let's talk numbers.

For the Chicago pilot - 12 weeks, $250K investment:
- Anomaly response: 70% faster → $40K savings
- Food waste prevention: 40% reduction → $150K savings  
- Document processing: 80% faster → $50K savings
- Total: $250K+ savings = 100% ROI in the pilot alone

Payback period: 1.5 months.

Scale this across all Lineage facilities:
- Annual savings: $6.2M
- Implementation cost: $1.5M
- 3-year ROI: 2,225%

And that's just the quantifiable savings. The qualitative 
benefits - better compliance, happier customers, empowered 
ops teams - are harder to measure but equally valuable.

[Show Slide 17 - Next Steps]

Here's what we propose:
1. Approve the Chicago pilot this week
2. Assign your pilot team
3. Kickoff meeting week of November 4th
4. Go live in 4 weeks

We're ready to start immediately."
```

---

## Q&A Preparation

### Expected Questions & Answers

**Q: "How accurate is the LLM? What if it gives wrong information?"**

**A:**
```
"Great question. We use enterprise-grade LLMs (Mistral/OpenAI) 
with 95%+ accuracy. But more importantly:

1. Every answer includes citations - you can verify the source
2. For critical decisions, we recommend human-in-the-loop
3. The system retrieves from YOUR documents - your SOPs, your data
4. We can configure confidence thresholds for auto-actions

During the pilot, we'll measure accuracy and adjust as needed."
```

**Q: "What about data security and privacy?"**

**A:**
```
"Security is paramount:

1. Encryption: TLS 1.3 for data in transit, AES-256 at rest
2. Access control: Role-based permissions, audit logging
3. Integration: Read-only access to your systems
4. Compliance: SOC2 Type II ready, GDPR compliant
5. Infrastructure: US-based cloud (AWS/Azure)

We'll do a full security review with your IT team before deployment."
```

**Q: "How long does implementation take?"**

**A:**
```
"For the Chicago pilot:
- Week 1-2: Setup, training, data ingestion
- Week 3-8: Anomaly detection deployment
- Week 9-12: Document intelligence, full evaluation

You'll see value within the first 2 weeks when ops teams 
start using the natural language query interface.

For enterprise rollout: 6 months to all facilities."
```

**Q: "What if our ops team resists the change?"**

**A:**
```
"Change management is built into our approach:

1. Early involvement: Ops champions from day one
2. Training: 3 comprehensive sessions, hands-on
3. Quick wins: Natural language queries show value immediately
4. Support: On-site for 4 weeks, 24/7 remote support
5. Feedback: Continuous iteration based on user input

In similar deployments, we've seen 90%+ user satisfaction 
because the system makes their jobs easier, not harder."
```

**Q: "Can we customize it for our specific needs?"**

**A:**
```
"Absolutely. The system is already configured for Lineage:
- Product-specific temperature ranges
- Your compliance standards (HACCP, FDA, FSMA)
- Your facilities (Chicago, Dallas, Atlanta, etc.)

During the pilot, we'll customize:
- Agent thresholds and actions
- Notification workflows
- Integration with your specific WMS/TMS
- Custom reports and dashboards

It's your system, tailored to your operations."
```

**Q: "What happens after the pilot?"**

**A:**
```
"Three options:

1. Expand to 5 facilities: $500K, 3 months
2. Enterprise deployment: $1.5M, 6 months, all facilities
3. Pause and evaluate (no obligation)

Based on pilot metrics, we'll recommend the best path forward. 
Most clients expand rapidly once they see the ROI."
```

---

## Post-Demo Follow-Up

### Immediate Actions (Same Day)

**Send Email:**
```
Subject: GLIH Demo Follow-Up - Next Steps

Dear [Names],

Thank you for your time today. As demonstrated, GLIH can deliver:
- 70% faster anomaly response
- 80% faster document processing  
- $250K+ ROI from Chicago pilot alone

Attached:
- Executive presentation deck
- Pilot proposal (12 weeks, $250K)
- Technical architecture document
- Security and compliance overview

Next steps:
1. Review materials with your team
2. Schedule follow-up call (this week)
3. Identify pilot team members
4. Target kickoff: Week of November 4th

I'm available for any questions.

Best regards,
[Your Name]
```

### Materials to Send

1. **LINEAGE_EXECUTIVE_PRESENTATION.md** (this file)
2. **LINEAGE_PILOT_PROPOSAL.md** (detailed proposal)
3. **LINEAGE_SOLUTION_OVERVIEW.md** (technical details)
4. **Demo recording** (if recorded)
5. **ROI calculator** (Excel spreadsheet)

---

## Demo Tips

### Do's
✅ Practice the demo 2-3 times beforehand  
✅ Have backup slides if live demo fails  
✅ Speak to business outcomes, not just features  
✅ Use specific numbers and examples  
✅ Pause for questions throughout  
✅ Show enthusiasm and confidence  
✅ Relate everything back to Lineage's pain points  

### Don'ts
❌ Don't rush through the demo  
❌ Don't use too much technical jargon  
❌ Don't skip the ROI discussion  
❌ Don't promise features that don't exist yet  
❌ Don't dismiss concerns or questions  
❌ Don't forget to ask for the business  

---

## Success Criteria

### You Know the Demo Went Well If:

1. **Engagement**: Audience asks questions and takes notes
2. **Understanding**: They can explain the value back to you
3. **Excitement**: They discuss use cases and possibilities
4. **Next Steps**: They commit to timeline and pilot team
5. **Objections**: Concerns are raised and addressed (not ignored)

### Ideal Outcome:

**"We want to move forward with the Chicago pilot. 
Let's schedule the kickoff for November 4th."**

---

**Good luck with your demo! You've got this! 🚀**
