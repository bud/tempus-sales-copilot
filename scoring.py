"""Deterministic scoring engine for Tempus Sales Copilot.

Formula (matches solution doc):
  SCORE = 0.35×volume + 0.25×fit + 0.20×recency + 0.15×objection_resolvability + 0.05×sentiment
  + 0.15 bonus for existing Tempus customer
  + 0.10 bonus for no current vendor (greenfield)
  Capped at 1.0.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# Reference date for recency calculation (demo mode)
REFERENCE_DATE = date(2026, 1, 15)
MAX_RECENCY_DAYS = 180

WEIGHTS = {
    "volume":    0.35,
    "fit":       0.25,
    "recency":   0.20,
    "objection": 0.15,
    "sentiment": 0.05,
}
EXISTING_CUSTOMER_BONUS = 0.15
NO_VENDOR_BONUS = 0.10

SENTIMENT_SCORES: dict[str, float] = {
    "very positive": 1.0,
    "positive":      0.8,
    "warming":       0.65,
    "neutral":       0.4,
}

PRODUCT_MATCH: dict[str, dict[str, Any]] = {
    "breast":           {"primary": "xT CDx",         "secondary": ["xG/xG+", "xF"],  "reason": "648-gene panel covers PIK3CA, ESR1, BRCA; hereditary testing for BRCA families; liquid biopsy for resistance monitoring"},
    "ovarian":          {"primary": "xT CDx",         "secondary": ["xG/xG+"],         "reason": "Comprehensive HRD/BRCA profiling; hereditary panel for family risk"},
    "NSCLC":            {"primary": "xT CDx + xR",   "secondary": ["xF/xF+"],         "reason": "DNA + RNA captures ALK/ROS1/RET/NTRK fusions; liquid biopsy for osimertinib resistance monitoring"},
    "SCLC":             {"primary": "xT CDx",         "secondary": ["xF"],             "reason": "Comprehensive profiling for emerging targeted therapy options"},
    "colorectal":       {"primary": "xT CDx",         "secondary": ["xF"],             "reason": "FDA-approved CDx for CRC; genome-wide MSI (239 loci vs 5-marker); KRAS/NRAS/BRAF profiling"},
    "pancreatic":       {"primary": "xT CDx + xR",   "secondary": ["xF"],             "reason": "PurIST algorithmic diagnostic for PDAC; RNA for rare fusions; comprehensive profiling"},
    "cholangiocarcinoma": {"primary": "xR + xT CDx", "secondary": ["xF"],             "reason": "RNA sequencing critical for FGFR2 fusion detection; DNA for IDH1/2 and other targets"},
    "gastric":          {"primary": "xT CDx",         "secondary": ["xF"],             "reason": "HER2 assessment, MSI status, comprehensive biomarker profiling"},
    "AML":              {"primary": "xT",             "secondary": ["xM"],             "reason": "Comprehensive heme profiling; MRD monitoring for post-treatment tracking"},
    "MDS":              {"primary": "xT",             "secondary": ["xM"],             "reason": "Genomic risk stratification; MRD monitoring for treatment response"},
    "lymphoma":         {"primary": "xT",             "secondary": [],                 "reason": "Hematologic mutation profiling for treatment guidance"},
    "glioblastoma":     {"primary": "xR + xT CDx",   "secondary": [],                 "reason": "MGMT methylation (xR add-on) critical for GBM treatment decisions; IDH1/2 mutation detection"},
    "brain":            {"primary": "xR + xT CDx",   "secondary": [],                 "reason": "RNA for fusion detection and MGMT methylation; DNA for comprehensive profiling"},
    "prostate":         {"primary": "xT CDx",         "secondary": ["xG/xG+"],         "reason": "BRCA1/2 for PARP inhibitor eligibility; hereditary testing for family risk"},
    "renal":            {"primary": "xT CDx",         "secondary": ["xG/xG+"],         "reason": "Comprehensive profiling; hereditary testing for VHL and other syndromes"},
    "bladder":          {"primary": "xT CDx",         "secondary": ["xF"],             "reason": "FGFR alterations, TMB for immunotherapy; liquid biopsy for monitoring"},
    "mesothelioma":     {"primary": "xT CDx + xR",   "secondary": [],                 "reason": "Comprehensive profiling for emerging treatments; RNA for fusions"},
    "esophageal":       {"primary": "xT CDx",         "secondary": ["xF"],             "reason": "HER2, MSI, PD-L1 biomarker profiling for treatment selection"},
}

OBJECTION_HANDLERS: dict[str, dict[str, str]] = {
    "Turnaround time": {
        "response": "I understand timing is critical for your patients. Tempus xT CDx results are typically delivered within 10–14 calendar days of specimen receipt. Plus, our auto-conversion feature means if tissue is insufficient, we automatically reflex to xF liquid biopsy — your patient never waits for a reorder. That's often faster end-to-end than resubmitting to another lab.",
        "source": "Tempus Patient Resources — turnaround time; xT product page — auto-conversion feature",
    },
    "Insurance coverage": {
        "response": "Tempus offers a transparent financial assistance program for all U.S. patients, regardless of insurance status. Patients get an immediate out-of-pocket cost determination upon applying at access.tempus.com. We work directly with insurance companies on reimbursement so your team doesn't carry that burden.",
        "source": "Tempus Financial Assistance Program; Patient Resources page",
    },
    "Cost concerns": {
        "response": "We understand cost is a real consideration for your patients. Tempus provides financial assistance to all U.S. patients regardless of insurance status, with immediate out-of-pocket cost decisions. For uninsured patients, we have a self-pay option. Cost is never a barrier to precision medicine access.",
        "source": "Tempus Financial Assistance Program; tempus.com/patients",
    },
    "Skeptical about clinical utility": {
        "response": "I appreciate that perspective. In a validation study of the xT panel, 88.6% of clinical samples contained at least one biologically relevant alteration informing treatment decisions. For CRC specifically, xT CDx is FDA-approved as a companion diagnostic, and our genome-wide MSI analysis using 239 loci is more comprehensive than traditional 5-marker PCR. These aren't just more results — they're results that change treatment decisions.",
        "source": "Nat Biotechnol 2019 xT validation study; FDA xT CDx approval; MSI methodology documentation",
    },
    "Satisfied with current vendor": {
        "response": "That's great that you're already leveraging genomic testing. What we hear from physicians who've made the switch is that the value isn't just in the panel — it's in the platform. Tempus combines tissue, liquid biopsy, RNA sequencing, hereditary testing, and MRD monitoring under one roof with one ordering workflow and one portal.",
        "source": "Tempus product portfolio; Tempus Hub platform",
    },
    "Switching costs": {
        "response": "We make the transition straightforward. Tempus Hub provides a streamlined ordering process — online, paper, or EHR-integrated. We handle pathology coordination for tissue retrieval, and our team supports onboarding from day one. Many practices run both vendors in parallel initially, then consolidate once they see the results.",
        "source": "Tempus Hub; onboarding process documentation",
    },
    "Specimen handling": {
        "response": "We've streamlined the process significantly. You can order through Tempus Hub online, via paper requisition, or directly from your EHR. For tissue, we coordinate with your hospital's pathology department. For liquid biopsy, it's a simple blood draw in two Streck tubes shipped via our included FedEx label. Our support team at 800.739.4137 handles any logistics questions.",
        "source": "Tempus ordering workflow; xF collection requirements; Customer Support",
    },
    "Concordance": {
        "response": "We have extensive validation data. The xT assay was clinically validated on 1,074 samples across diverse cancer types, published in Nature Biotechnology. The xT CDx was validated against externally validated orthogonal methods for variant detection and MSI status. I can connect you with our Medical Science Liaison to walk through the specific concordance data relevant to your practice.",
        "source": "Nat Biotechnol 2019; FDA xT CDx label; NCBI GTR Tempus xT documentation",
    },
    "EHR integration": {
        "response": "Tempus supports direct ordering from your EHR system — no separate portal required if that's your preference. Results are accessible through Tempus Hub and Tempus One, our AI-enabled clinical assistant. We work with your IT team to set up the integration that fits your workflow.",
        "source": "Tempus Hub; Tempus One; EHR ordering documentation",
    },
}


def find_handler_key(objection: str) -> str | None:
    """Return the matching handler key for an objection string, or None."""
    lower = objection.lower()
    for key in OBJECTION_HANDLERS:
        if key.lower() in lower:
            return key
    # Fuzzy fallback: check individual words
    for key in OBJECTION_HANDLERS:
        if any(word in lower for word in key.lower().split() if len(word) > 4):
            return key
    return None


def get_matched_products(cancer_types: list[str]) -> dict[str, Any]:
    """Return primary product, secondary products, and reasons for given cancer types."""
    primaries: set[str] = set()
    secondaries: set[str] = set()
    reasons: list[str] = []
    for cancer in cancer_types:
        m = PRODUCT_MATCH.get(cancer)
        if m:
            # Split compound primary strings (e.g. "xT CDx + xR") into individual tokens
            for token in m["primary"].split(" + "):
                primaries.add(token.strip())
            secondaries.update(m["secondary"])
            reasons.append(m["reason"])
    # Build secondary list excluding anything already in primaries
    secondary_set = set()
    for s in secondaries:
        for token in s.split(" + "):
            secondary_set.add(token.strip())
    return {
        "primary": " + ".join(sorted(primaries)) if primaries else "xT CDx",
        "secondary": sorted(secondary_set - primaries),
        "reasons": reasons,
    }


def _volume_score(patients: int, max_patients: int) -> float:
    return min(patients / max_patients, 1.0)


def _fit_score(cancer_types: list[str]) -> float:
    matched = [t for t in cancer_types if t in PRODUCT_MATCH]
    if not matched:
        return 0.2
    return min(len(matched) / 2.0, 1.0)


def _recency_score(last_contact_str: str) -> float:
    try:
        last_contact = date.fromisoformat(str(last_contact_str).strip())
        days = (REFERENCE_DATE - last_contact).days
        return max(0.0, 1.0 - days / MAX_RECENCY_DAYS)
    except Exception:
        return 0.0


def _objection_score(objections: list[str]) -> float:
    """Score based on whether known objections are resolvable."""
    if not objections:
        return 0.5  # No objections: neutral (not better or worse than having resolvable ones)
    resolvable = sum(1 for obj in objections if find_handler_key(obj) is not None)
    ratio = resolvable / len(objections)
    return 0.4 + 0.6 * ratio  # Range: 0.4 (all unresolvable) → 1.0 (all resolvable)


def compute_score(row: pd.Series, crm: dict[str, Any], max_patients: int) -> float:
    """Compute priority score for a single provider row."""
    notes = crm.get(row["provider_id"], {})
    objections = notes.get("objections", [])
    sentiment = notes.get("sentiment", "neutral")
    cancer_types = [t.strip() for t in str(row["primary_cancer_types"]).split(",")]

    vol = _volume_score(int(row["est_annual_patients"]), max_patients)
    fit = _fit_score(cancer_types)
    rec = _recency_score(row["last_contact_date"])
    obj = _objection_score(objections)
    warm = SENTIMENT_SCORES.get(sentiment, 0.4)

    raw = (
        WEIGHTS["volume"]    * vol
        + WEIGHTS["fit"]       * fit
        + WEIGHTS["recency"]   * rec
        + WEIGHTS["objection"] * obj
        + WEIGHTS["sentiment"] * warm
    )

    vendor = str(row.get("current_testing_vendor", "")).strip().lower()
    if vendor == "tempus":
        raw += EXISTING_CUSTOMER_BONUS
    elif vendor in ("none", "", "nan"):
        raw += NO_VENDOR_BONUS

    return round(min(raw, 1.0), 3)


def load_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load market CSV and CRM JSON, return aligned DataFrames."""
    providers_df = pd.read_csv(DATA_DIR / "market_data.csv")
    with open(DATA_DIR / "crm_notes.json", encoding="utf-8") as f:
        raw_crm = json.load(f)

    # Build simplified CRM dict keyed by provider_id
    crm: dict[str, Any] = {}
    for pid, data in raw_crm.items():
        notes_text = " ".join(n["text"] for n in data.get("notes", []))
        crm[pid] = {
            "notes_text": notes_text,
            "notes": data.get("notes", []),
            # Pre-structured fields (from JSX mock — used in demo mode)
            "objections":  _get_mock_objections(pid),
            "interests":   _get_mock_interests(pid),
            "sentiment":   _get_mock_sentiment(pid),
            "summary":     _get_mock_summary(pid),
        }

    return providers_df, crm


def score_and_rank(providers_df: pd.DataFrame, crm: dict[str, Any]) -> pd.DataFrame:
    """Return providers_df sorted by descending priority score."""
    max_pts = int(providers_df["est_annual_patients"].max())
    df = providers_df.copy()
    df["score"] = df.apply(lambda row: compute_score(row, crm, max_pts), axis=1)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


# ---------------------------------------------------------------------------
# Mock structured CRM data (ported from JSX prototype — used as demo fallback
# and as pre-labeled data for demo mode scoring)
# ---------------------------------------------------------------------------

_MOCK_OBJECTIONS: dict[str, list[str]] = {
    "P001": ["Turnaround time with current vendor (3+ weeks)", "Insurance coverage concerns for community hospital patients"],
    "P002": ["Turnaround time — patients need to start treatment quickly", "Specimen handling/shipping logistics for tissue"],
    "P003": ["Skeptical about clinical utility beyond current IHC/MSI testing", "Doesn't see value in broader panels"],
    "P004": ["Satisfied with current Caris platform", "Switching costs"],
    "P005": [],
    "P006": ["Cost concerns for patient population", "Very busy, hard to reach"],
    "P007": [],
    "P008": ["Doesn't order genomic testing directly", "Lower direct testing volume"],
    "P009": ["Wants concordance data vs current methylation-specific PCR"],
    "P010": ["Focused on clinical evidence and workflow integration"],
}

_MOCK_INTERESTS: dict[str, list[str]] = {
    "P001": ["Hereditary testing for BRCA population", "xT CDx vs F1CDx comparison for breast", "Bundled hereditary + somatic testing", "Case studies for tumor board"],
    "P002": ["xT + xF combo approach", "Auto-reflex workflow", "ALK and ROS1 fusion detection rates vs FISH"],
    "P003": [],
    "P004": ["RNA sequencing for fusion detection", "FGFR2 fusions in cholangiocarcinoma", "Lunch-and-learn for tumor board"],
    "P005": ["xM MRD monitoring for AML patients", "Clinical trial matching for exhausted-options patients", "Expanding Tempus volume across heme + solid tumor"],
    "P006": [],
    "P007": ["xF liquid biopsy for resistance monitoring (osimertinib patients)", "PD-L1 IHC add-on", "Departmental presentation on liquid biopsy", "T790M resistance mutation detection rates", "Warm intro to new colleague Dr. Park"],
    "P008": ["Hereditary testing for BRCA-related prostate cancer families"],
    "P009": ["MGMT promoter methylation analysis (xR add-on)", "IDH1/2 mutation detection sensitivity", "MSL consultation"],
    "P010": ["xT CDx companion diagnostic for CRC", "MSI testing methodology (genome-wide vs 5-marker)", "PurIST for pancreatic referrals", "EHR integration"],
}

_MOCK_SENTIMENT: dict[str, str] = {
    "P001": "positive", "P002": "positive", "P003": "neutral", "P004": "warming",
    "P005": "very positive", "P006": "neutral", "P007": "very positive",
    "P008": "neutral", "P009": "positive", "P010": "positive",
}

_MOCK_SUMMARIES: dict[str, str] = {
    "P001": "High-volume breast oncologist frustrated with Foundation Medicine turnaround. Actively evaluating alternatives. Interested in combined somatic + hereditary testing.",
    "P002": "Large lung practice using Guardant for liquid only — no tissue-based NGS provider. Major gap. Interested in comprehensive tissue + liquid strategy.",
    "P003": "GI oncologist relying solely on hospital pathology. Needs education on how comprehensive profiling changes treatment decisions for CRC/pancreatic patients.",
    "P004": "Currently on Caris but recognizes RNA sequencing gap. Had cholangio cases where DNA-only panels missed suspected fusions. Scheduling tumor board presentation.",
    "P005": "Existing customer, very satisfied. Growth opportunity — could double volume with MRD monitoring and expanded heme testing.",
    "P006": "Breast oncologist using only Oncotype DX and limited IHC. Needs education on broader panel value for metastatic breast. Nurse navigator Maria may be better entry point.",
    "P007": "Champion account at Northwestern. Consistent xT CDx orderer. Expansion opportunity with xF for treatment monitoring and onboarding new colleague.",
    "P008": "Surgical oncologist — referral pathway, not direct orderer. Could influence medical oncology partner Dr. Singh. Interest in hereditary prostate testing.",
    "P009": "Neuro-oncologist whose key pain point is F1CDx lacking MGMT methylation. Tempus xR with MGMT add-on is a strong differentiator. Needs validation data.",
    "P010": "Large GI practice on Guardant for liquid only. Strong fit for xT CDx with FDA-approved CRC companion diagnostic. Evidence-driven buyer.",
}


def _get_mock_objections(pid: str) -> list[str]:
    return _MOCK_OBJECTIONS.get(pid, [])

def _get_mock_interests(pid: str) -> list[str]:
    return _MOCK_INTERESTS.get(pid, [])

def _get_mock_sentiment(pid: str) -> str:
    return _MOCK_SENTIMENT.get(pid, "neutral")

def _get_mock_summary(pid: str) -> str:
    return _MOCK_SUMMARIES.get(pid, "")
