# Tempus Sales Copilot

An AI-powered meeting preparation tool for Tempus oncology sales reps. Synthesizes market data, CRM notes, and product knowledge into actionable outputs.

**Built for the Tempus AI — GenAI Product Builder case study.**

---

## Slide Deck

[View the presentation on Google Slides](https://docs.google.com/presentation/d/1juwuy3q4PJFQ6_FgPxBYubpWmXOdifdX/)

---

## How to Access the Prototype

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- pip (included with Python)

### Setup and Run

```bash
# 1. Clone the repo
git clone https://github.com/bud/tempus-sales-copilot.git
cd tempus-sales-copilot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python -m streamlit run app.py
```

The app opens automatically at **http://localhost:8501** in your browser.

No API key is needed — the app runs fully in **demo mode** with pre-computed data for all 10 providers.

> **Optional:** To enable live LLM generation, copy `.env.example` to `.env` and add an OpenAI or Anthropic API key.

---

## What It Does

Sales reps manage 150+ accounts and spend 2-4 hours preparing for a single meeting. The Copilot reduces this to under 2 minutes by producing three outputs:

| Output | Description |
|--------|-------------|
| **Ranked provider list** | 10 providers scored by patient volume, product fit, recency, objection resolvability, and sentiment |
| **Objection handler** | Grounded responses to known concerns (e.g., turnaround time, cost), citing specific Tempus data points |
| **Meeting script** | 30-second elevator pitch personalized to each doctor's specialty, interests, and pain points |

---

## Data Sources

| Source | Format | File |
|--------|--------|------|
| Market Intelligence | CSV | `data/market_data.csv` — 10 oncologists with specialty, patient volume, current vendor |
| Product Knowledge Base | Markdown | `data/tempus_products.md` — Tempus test capabilities pulled from tempus.com |
| CRM Notes | JSON | `data/crm_notes.json` — interaction notes for 10 physicians |

---

## Architecture

```
app.py              ← Streamlit UI (two-panel layout)
scoring.py          ← Deterministic scoring engine
rag.py              ← RAG pipeline (embed → retrieve → generate)
data/
  market_data.csv   ← Provider market intelligence
  crm_notes.json    ← CRM interaction logs
  tempus_products.md← Product knowledge base
```

**Design principle:** Scoring is deterministic code (auditable, tunable). The LLM handles only synthesis tasks where fluency adds real value.

### Scoring Formula

```
SCORE = 0.35 x volume + 0.25 x product_fit + 0.20 x recency
      + 0.15 x objection_resolvability + 0.05 x sentiment
      + 0.15 bonus (existing Tempus customer)
      + 0.10 bonus (greenfield — no current vendor)
      Capped at 1.0
```

### RAG Pipeline

1. Product KB markdown split on `##` headings into 600-char sub-chunks
2. Chunks embedded with `all-MiniLM-L6-v2` (local, free)
3. Cosine similarity retrieval (top-3 chunks per query)
4. LLM generates response grounded in retrieved chunks

---

## Tech Stack

All tools are free tier or open source:

| Component | Tool |
|-----------|------|
| UI | Streamlit |
| LLM | OpenAI GPT-4o-mini or Claude Haiku (optional) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector search | numpy cosine similarity |
| Data | pandas |

---

## Assumptions

- Mock data represents a Midwest-1 territory as of January 2026
- Provider IDs (P001-P010) are consistent across CSV, JSON, and scoring engine
- In demo mode, objections/interests/sentiment are pre-labeled; with an API key, these are extracted by the LLM from raw CRM text
- Dr. Thompson (P005) is modeled as an existing Tempus customer to demonstrate upsell scoring

---

## What I'd Build With More Time

1. **Live Salesforce sync** — pull CRM notes via SFDC API instead of JSON files
2. **Trigger alert system** — flag providers when FDA approvals or 30-day silence thresholds hit
3. **Territory strategy view** — weekly top-10 call plan with suggested visit order
4. **Rep feedback loop** — thumbs up/down on outputs feeds into prompt refinement
5. **Cloud deployment** — one-click deploy via Streamlit Community Cloud
