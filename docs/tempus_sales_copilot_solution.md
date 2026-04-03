# Tempus Sales Copilot — Complete Case Study Solution

---

## 1. PRODUCT DEFINITION

### The Exact Problem

Tempus sales reps manage 100–300+ accounts across oncology clinics and hospital systems. Before every 15-minute meeting with a CMO or oncologist, they manually cross-reference three disconnected data sources:

1. **Salesforce CRM notes** — unstructured text from previous interactions ("Dr. Smith worried about TAT," "interested in liquid biopsy")
2. **Market intelligence** — provider lists, patient volumes, cancer type mix, competitive testing usage
3. **Tempus product catalog** — which panels (xT CDx, xR, xF/xF+, xG, xM, xE) match which clinical needs, with what evidence

This prep takes **2–4 hours per meeting**. A rep with 8 meetings/week loses 16–32 hours to prep that should take minutes. Worse, the synthesis quality varies wildly — junior reps miss obvious connections (e.g., a high-volume lung oncologist who isn't ordering xR RNA sequencing, which catches fusions DNA-only panels miss).

### The User

**Primary:** Tempus Oncology Sales Representatives (field-based, territory ~150 accounts)
**Secondary:** Sales managers reviewing territory strategy and prioritization

**Daily struggle:** "I have 150 accounts. Which 10 should I call this week, and what exactly should I say to each one?"

### The Core Insight

This is not a search problem — it's a **synthesis problem**. The rep doesn't need to find data. They need three things fused into one actionable brief:

- **WHO** to call (ranked by revenue opportunity × likelihood to convert)
- **WHAT** to say (personalized to the doctor's specialty, patient mix, and known concerns)
- **HOW** to handle pushback (grounded in real Tempus performance data, not generic talking points)

The Copilot doesn't replace the rep's judgment — it gives them a pre-built briefing package so they walk into every meeting prepared like a 10-year veteran.

---

## 2. SOLUTION DESIGN

### System Inputs

| Data Source | Format | Content | Update Frequency |
|---|---|---|---|
| Market Intelligence | CSV | Provider name, NPI, specialty, institution, est. annual patient volume, cancer types, current testing vendor, territory | Monthly |
| CRM Notes | Text/JSON | Free-text interaction logs per provider — objections, interests, relationship status, last contact date | Per interaction |
| Product Knowledge Base | Markdown/PDF | Tempus test panels (xT CDx, xR, xF/xF+, xG/xG+, xE, xM), capabilities, turnaround times, evidence, competitive advantages | Quarterly |

### System Outputs

#### Output 1: Ranked Provider List

**Ranking algorithm (deterministic, not LLM):**

```
PRIORITY_SCORE = (
    0.35 × VOLUME_SCORE        # Normalized patient volume (higher = more tests)
  + 0.25 × FIT_SCORE           # Product-market fit: cancer types × Tempus panel coverage
  + 0.20 × RECENCY_PENALTY     # Days since last contact (decays over time)
  + 0.15 × OBJECTION_RESOLVABILITY  # Can we now address their concern? (binary boost)
  + 0.05 × RELATIONSHIP_WARMTH # Sentiment from CRM notes (positive/neutral/cold)
)
```

**Why deterministic:** Ranking is a scoring problem with clear business logic. Using an LLM here adds latency, cost, and non-determinism for zero benefit. Traditional weighted scoring is auditable, tunable, and fast.

**LLM role in ranking:** The LLM extracts structured fields FROM CRM notes (objections, sentiment, interests) that feed INTO the scoring formula. The LLM classifies, not decides.

#### Output 2: Objection Handler

**How it works:**

1. LLM extracts the specific objection from CRM notes (e.g., "concerned about turnaround time")
2. System retrieves relevant product knowledge chunks via semantic search (e.g., Tempus xT CDx turnaround = 10–14 calendar days from specimen receipt)
3. LLM generates a response that:
   - Acknowledges the concern directly
   - Cites a specific, verifiable Tempus metric
   - Reframes the concern as an advantage

**Example output:**

> **Objection:** "Dr. Patel is concerned about turnaround time affecting treatment planning."
>
> **Suggested Response:** "Dr. Patel, I understand timing is critical for your NSCLC patients. Tempus xT CDx results are typically delivered within 10–14 days of specimen receipt. Additionally, our auto-conversion feature means if tissue is insufficient, we automatically reflex to xF liquid biopsy — so your patient never waits for a reorder. That's faster end-to-end than resubmitting to another lab."
>
> **Source:** Tempus Patient Resources — turnaround time documentation; xT/xR product page — auto-conversion feature.

**Grounding mechanism:** Every claim in the objection handler is tagged with its source document and chunk. If the knowledge base doesn't contain a relevant metric, the system says "No verified data available — escalate to Medical Affairs" instead of hallucinating.

#### Output 3: Meeting Script (30-Second Elevator Pitch)

**Personalization inputs:**
- Doctor's specialty and cancer type focus (from market data)
- Known interests or concerns (from CRM notes)
- Best-fit Tempus product (from product-market matching)
- Recent relevant evidence (from knowledge base)

**Generation approach:** LLM receives a structured prompt with all personalization fields filled in, plus a strict format constraint (3–4 sentences, must mention the specific panel, must reference the doctor's patient population).

**Example output:**

> **For: Dr. Sarah Chen, Medical Oncologist, breast cancer focus, Memorial Hospital**
>
> "Dr. Chen, with your breast cancer patient volume, I wanted to share how Tempus xT CDx is helping oncologists like you identify actionable PIK3CA and ESR1 mutations that inform targeted therapy selection. Our 648-gene panel with matched tumor-normal sequencing reduces false positives by filtering out germline variants — meaning cleaner results for your treatment decisions. I'd love to walk you through a recent case study showing how dual tissue and liquid biopsy testing caught resistance mutations in 9% of patients that tissue-only testing missed."

### Step-by-Step System Flow

```
[1] DATA INGESTION
    ├── CSV → Pandas DataFrame (market data)
    ├── Text files → Raw string per provider (CRM notes)
    └── Markdown/PDF → Chunked + embedded (product KB)

[2] KNOWLEDGE BASE INDEXING
    └── Product KB chunks → sentence-transformer embeddings → vector store

[3] CRM NOTE EXTRACTION (LLM)
    └── For each provider's notes:
        ├── Extract: objections[], interests[], sentiment, relationship_stage
        └── Store as structured JSON

[4] PROVIDER SCORING (Code, not LLM)
    └── Compute PRIORITY_SCORE per provider using weighted formula
    └── Sort descending → Ranked list

[5] CONTENT GENERATION (LLM + RAG)
    └── For selected provider:
        ├── Retrieve relevant KB chunks via semantic search
        ├── Generate objection handler (grounded in retrieved chunks)
        └── Generate meeting script (personalized with all context)

[6] OUTPUT ASSEMBLY
    └── Render: ranked list + per-provider briefing card
```

### Where LLM vs. Traditional Code

| Task | Approach | Why |
|---|---|---|
| Parse CSV market data | **Code** (Pandas) | Structured data, deterministic |
| Extract objections from CRM notes | **LLM** | Unstructured text understanding |
| Score and rank providers | **Code** (weighted formula) | Auditable, tunable, fast |
| Chunk and embed product KB | **Code** (sentence-transformers) | Standard NLP pipeline |
| Retrieve relevant KB chunks | **Code** (cosine similarity) | Vector search, deterministic |
| Generate objection responses | **LLM + RAG** | Requires synthesis + natural language |
| Generate meeting scripts | **LLM + RAG** | Requires personalization + fluency |
| Validate output grounding | **Code** (source tagging) | Traceability requirement |

---

## 3. TECHNICAL ARCHITECTURE

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     STREAMLIT UI                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Provider  │  │  Objection   │  │  Meeting Script   │  │
│  │ Rankings  │  │  Handler     │  │  Generator        │  │
│  └─────┬────┘  └──────┬───────┘  └────────┬──────────┘   │
└────────┼───────────────┼──────────────────┼──────────────┘
         │               │                  │
    ┌────▼───────────────▼──────────────────▼─────┐
    │              ORCHESTRATION LAYER            │
    │         (Python — business logic)           │
    │                                             │
    │  ┌────────────┐  ┌────────────────────┐     │
    │  │  Scoring    │  │  RAG Pipeline      │    │
    │  │  Engine     │  │  (retrieve + gen)  │    │
    │  └────────────┘  └────────────────────┘     │
    └──────┬──────────────────┬───────────────────┘
           │                  │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────────────┐
    │  Data Layer │   │  Vector DB  │   │  LLM API     │
    │  (CSV+JSON) │   │  (ChromaDB) │   │  (OpenAI/    │
    │             │   │             │   │   Claude)    │
    └─────────────┘   └─────────────┘   └──────────────┘
```

### Tech Stack (All Free Tier)

| Component | Tool | Why |
|---|---|---|
| UI | **Streamlit** | Fastest path to interactive prototype; free hosting on Streamlit Cloud |
| LLM | **OpenAI GPT-4o-mini** or **Claude 3.5 Sonnet** (API) | Strong instruction following, good at structured output |
| Embeddings | **sentence-transformers** (all-MiniLM-L6-v2) | Free, local, fast, good enough for ~50 KB chunks |
| Vector Store | **ChromaDB** (in-memory) | Zero config, pip install, works for prototype scale |
| Data Processing | **Pandas** | Standard, robust CSV handling |
| Deployment | **Streamlit Community Cloud** | Free, one-click deploy from GitHub |

### How Data is Ingested

1. **Market CSV** → `pd.read_csv()` → DataFrame with columns: `provider_name, npi, specialty, institution, est_annual_patients, cancer_types, current_vendor, territory`
2. **CRM Notes** → JSON file with provider NPI as key → raw text notes per provider
3. **Product KB** → Markdown files split into chunks (by heading + 300-token windows) → embedded with sentence-transformers → stored in ChromaDB collection

### Grounding Strategy (Anti-Hallucination)

1. **Source tagging:** Every KB chunk stored with metadata (source file, section, page). Generated text includes inline citations.
2. **Constrained generation:** LLM system prompt explicitly says: "Only use information from the provided context. If the context doesn't contain relevant data, say 'I don't have verified data on this — recommend checking with Medical Affairs.'"
3. **Fact extraction separation:** CRM note extraction uses structured output (JSON mode) with defined schema — LLM can't inject fabricated fields.
4. **No open-ended generation:** The meeting script has a rigid template. The LLM fills slots, it doesn't freeform.

---

## 4. PROTOTYPE PLAN (MVP — Build in 3–4 Days)

### What I'm Actually Building

A working Streamlit app that:
- Loads mock data (10 providers, 6 Tempus products, CRM notes)
- Shows a ranked provider dashboard
- Lets you click a provider → generates objection handler + meeting script in real-time
- Cites sources for every claim

### Exact Stack

```
Python 3.11+
├── streamlit (UI)
├── openai or anthropic (LLM API)
├── chromadb (vector store)
├── sentence-transformers (embeddings)
├── pandas (data processing)
└── python-dotenv (API key management)
```

### Mock Data to Create

**1. Market Intelligence CSV (`market_data.csv`)**

10 providers across 3 institutions:
- Mix of oncology subspecialties (lung, breast, colorectal, GI, hematologic)
- Varying patient volumes (50–500+ annually)
- Mix of current vendors (Foundation Medicine, Guardant, Caris, none)

**2. CRM Notes (`crm_notes.json`)**

Per-provider notes including:
- Specific objections (turnaround time, cost, panel breadth, switching cost)
- Interest signals ("asked about liquid biopsy," "has a BRCA-heavy population")
- Relationship stage (cold, warm, active customer)

**3. Product Knowledge Base (`tempus_products.md`)**

Covering real Tempus products:
- xT CDx: 648-gene tissue panel, FDA-approved CDx, tumor+normal matched, 10–14 day TAT
- xR: Whole-transcriptome RNA sequencing, catches fusions DNA misses
- xF/xF+: 105/523-gene liquid biopsy panels, auto-reflex from xT
- xG/xG+: 40/77-gene hereditary panels (CancerNext), 14–21 day TAT
- xE: 19,000+ gene whole exome panel
- xM: MRD monitoring (tumor-naive and tumor-informed)

### UI Layout

```
┌─────────────────────────────────────────────────┐
│  🔬 TEMPUS SALES COPILOT                        │
│                                                  │
│  Territory: [dropdown]   Filter: [cancer type]   │
├──────────────────────┬──────────────────────────┤
│  PRIORITY RANKINGS   │  PROVIDER BRIEFING        │
│                      │                           │
│  1. Dr. Chen ★★★★★  │  Dr. Sarah Chen           │
│     Breast, 320 pts  │  Memorial Hospital        │
│     Score: 0.92      │  Breast Oncology          │
│                      │                           │
│  2. Dr. Patel ★★★★  │  ── Why Call Now ──        │
│     Lung, 280 pts    │  High-volume breast pract  │
│     Score: 0.87      │  with no current Tempus    │
│                      │  testing. BRCA+ population  │
│  3. Dr. Kim ★★★★    │  is strong xG+ candidate.  │
│     CRC, 190 pts     │                           │
│     Score: 0.81      │  ── Objection Handler ──   │
│                      │  [Generated response with  │
│  4. Dr. Rodriguez ★★★│   source citations]        │
│     GI, 150 pts      │                           │
│     Score: 0.74      │  ── Meeting Script ──      │
│                      │  [30-sec elevator pitch]   │
│  ...                 │                           │
└──────────────────────┴──────────────────────────┘
```

---

## 5. EVALUATION

### Success Metrics

| Metric | Current State | Target | How to Measure |
|---|---|---|---|
| **Prep time per meeting** | 2–4 hours | < 15 minutes | Time-tracking in pilot |
| **Meetings per week** | 6–8 | 12–15 | CRM meeting logs |
| **Objection resolution rate** | Anecdotal | Track win/loss vs. objection type | CRM outcome tags |
| **New provider conversion** | ~12% pipeline close rate | 18%+ | Salesforce pipeline |
| **Rep adoption** | N/A | 80%+ weekly active usage | App analytics |
| **Content accuracy** | N/A | 95%+ factual grounding | Manual audit of 50 outputs |

### How to Test with Users

**Phase 1: Desk validation (Week 1)**
- Show 3 senior reps the prototype
- Ask: "For this provider, would you actually say this? What would you change?"
- Measure: % of generated content reps would use as-is vs. needs editing

**Phase 2: Parallel pilot (Weeks 2–4)**
- 5 reps use Copilot for half their accounts, manual prep for other half
- Compare: prep time, meeting quality (self-reported), conversion rates

**Phase 3: Outcome tracking (Month 2+)**
- Track pipeline velocity for Copilot-prepared vs. non-Copilot meetings
- Measure: time-to-close, average deal size, objection-to-resolution ratio

### How to Validate Output Correctness

1. **Automated checks:** Every generated response runs through a source-verification step — claims must trace back to a KB chunk. Flag unsourced claims.
2. **Human audit:** Medical Affairs reviews a random sample of 50 generated responses per month for clinical accuracy.
3. **Feedback loop:** Reps can thumbs-up/thumbs-down each output. Downvoted outputs get reviewed and used to refine prompts.

---

## 6. SLIDE DECK (8 Slides)

### Slide 1: Title
**Tempus Sales Copilot**
*From data to doorstep in 5 minutes*

Subtitle: Turning territory data into personalized meeting prep — automatically.

### Slide 2: The Problem
**Reps have the data. They don't have the time.**

- 2–4 hours of prep for every 15-minute meeting
- 3 disconnected data sources: CRM, market data, product knowledge
- Junior reps miss connections that cost deals
- Result: fewer meetings, generic pitches, lost revenue

### Slide 3: The Insight
**This isn't a search problem. It's a synthesis problem.**

- The data exists — it's scattered across Salesforce, spreadsheets, and product docs
- What reps need isn't more data. They need: Who to call. What to say. How to handle pushback.
- AI doesn't replace the rep — it gives every rep the preparation of a 10-year veteran

### Slide 4: The Solution
**An AI-powered briefing engine for Tempus sales**

Three outputs, one tool:
1. **Priority Rankings** — Who to call this week, scored by opportunity × fit
2. **Objection Handler** — Pre-drafted responses to known concerns, grounded in real Tempus data
3. **Meeting Script** — 30-second pitch tailored to each doctor's specialty and interests

### Slide 5: How It Works
**Input → Synthesize → Brief**

[System flow diagram]

- Market data + CRM notes + product KB feed into a scoring engine (rankings) and a RAG pipeline (content generation)
- Traditional code handles scoring (auditable, fast)
- LLM handles synthesis and personalization (where AI adds real value)
- Every claim cites its source — no hallucinations

### Slide 6: Demo / Sample Outputs
**What the rep sees**

[Screenshot of prototype]

- Left panel: Ranked provider list with priority scores
- Right panel: Per-provider briefing card
  - "Why call now" context
  - Objection handler with source citations
  - 30-second meeting script

### Slide 7: Evaluation & Impact
**Proving it works**

- Desk validation: 3 senior reps reviewed outputs → [X]% usable as-is
- Target: prep time from 2–4 hours → < 15 minutes
- Target: +50% more meetings per week
- Target: 95%+ output accuracy (audited by Medical Affairs)
- Built-in feedback loop: reps rate every output

### Slide 8: Why This Matters for Tempus
**Every minute saved is a meeting earned**

- Tempus delivered 212,000+ NGS tests in Q2 2025 alone — with 26% oncology volume growth
- Every new meeting a rep takes is a potential new ordering physician
- At scale: if 100 reps each gain 4 extra meetings/week = 400 additional touchpoints/week
- This compounds: more meetings → more conversions → more patients getting precision medicine

---

## 7. DIFFERENTIATION

### Why This is NOT Just a Chatbot

A chatbot waits for questions. The Copilot proactively tells you:
- "Call Dr. Patel this week — her NSCLC volume is up and we can now address her turnaround concern with our auto-reflex feature"
- It doesn't require the rep to know what to ask. It surfaces the insight.

### Why This is Better Than Current Workflows

| Current Workflow | Copilot |
|---|---|
| Open Salesforce, read notes | Structured extraction done for you |
| Open Excel, filter territory data | Scored and ranked automatically |
| Open product docs, find relevant panel | Best-fit product matched to provider |
| Write talking points from scratch | Meeting script pre-generated |
| **Time: 2–4 hours** | **Time: 2 minutes** |

### What Makes This a Real Product, Not a Demo

1. **Deterministic ranking** — not vibes-based LLM output. The scoring formula is tunable by sales leadership.
2. **Source-grounded responses** — every claim traces to a specific document chunk. No hallucinations.
3. **Fits existing workflow** — outputs are designed to be copy-pasted into Salesforce or read on mobile before walking into the meeting.
4. **Feedback loop** — rep ratings improve the system over time.

---

## 8. "WOW" FEATURES (Realistic but Impressive)

### 1. Competitive Intelligence Layer
When a provider currently uses Foundation Medicine or Guardant, the Copilot auto-generates a **head-to-head comparison** highlighting where Tempus wins (e.g., xT CDx's 648 genes + tumor-normal matching vs. FoundationOne CDx's tumor-only approach, which can produce germline false positives). Grounded in public data and Tempus's published advantages.

### 2. "Trigger Event" Alerts
The system flags providers when something changes:
- New FDA drug approval that requires a companion diagnostic Tempus offers
- Provider's patient volume crossed a threshold
- It's been 30+ days since last contact with a warm lead
- A known objection now has a new counter-argument (e.g., new turnaround time data)

This turns the Copilot from a passive prep tool into an **active deal-finding engine**.

### 3. Territory Strategy Mode
Instead of per-provider briefings, the Copilot can generate a **weekly territory plan**: "Here are your top 10 calls this week, in suggested order, with a brief for each." This is the view a sales manager would want to review in a 1:1. It turns individual meeting prep into territory-wide strategy.

---

## APPENDIX: Mock Data Specifications

### Market Data CSV Schema

```csv
provider_id,provider_name,npi,specialty,subspecialty,institution,city,state,est_annual_patients,primary_cancer_types,current_testing_vendor,current_panels,territory,last_contact_date
```

### CRM Notes JSON Schema

```json
{
  "NPI_12345": {
    "provider_name": "Dr. Sarah Chen",
    "notes": [
      {
        "date": "2025-11-15",
        "author": "Rep: Mike Torres",
        "text": "Met with Dr. Chen at ASCO regional. She's interested in our breast panel but concerned about insurance coverage for her community hospital patients. Asked specifically about financial assistance program. Very engaged — follow up in 2 weeks."
      },
      {
        "date": "2025-12-02",
        "author": "Rep: Mike Torres",
        "text": "Phone call. Dr. Chen says she's been using FoundationOne but frustrated with turnaround delays. Open to evaluating Tempus. Wants to see a comparison of xT CDx vs F1CDx for breast cancer specifically."
      }
    ]
  }
}
```

### Product KB Structure

```
tempus_products/
├── xt_cdx.md          # 648-gene tissue panel
├── xr.md              # RNA sequencing
├── xf_liquid.md       # Liquid biopsy
├── xg_hereditary.md   # Hereditary testing
├── xe_exome.md        # Whole exome
├── xm_mrd.md          # MRD monitoring
├── competitive.md     # Head-to-head comparisons
└── evidence.md        # Key clinical evidence / stats
```
