"""Tempus Sales Copilot — Streamlit application.

Run:
    streamlit run app.py

Requires: pip install -r requirements.txt
API key optional — app works in demo mode without one.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scoring import (
    WEIGHTS,
    EXISTING_CUSTOMER_BONUS,
    NO_VENDOR_BONUS,
    get_matched_products,
    load_data,
    score_and_rank,
)
from rag import RAGPipeline

load_dotenv()

from contextlib import nullcontext

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tempus Sales Copilot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS — clean, minimal, healthcare-tech feel
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* Hide Streamlit default header/toolbar/footer */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* Global */
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1200px; }

/* Header */
.cop-header { display:flex; align-items:center; gap:12px; padding-bottom:1rem;
              border-bottom:1px solid #E5E7EB; margin-bottom:1.25rem; }
.cop-logo { width:38px; height:38px; border-radius:8px; background:#EFF6FF;
            display:flex; align-items:center; justify-content:center; font-size:20px; }
.cop-title { font-size:1.15rem; font-weight:600; color:#111827; }
.cop-subtitle { font-size:0.8rem; color:#6B7280; }
.cop-badge { margin-left:auto; padding:4px 10px; border-radius:20px;
             font-size:0.7rem; font-weight:500; }
.badge-demo { background:#FEF3C7; color:#92400E; border:1px solid #FDE68A; }
.badge-live { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }

/* Provider cards */
.provider-card { padding:10px 12px; border-radius:8px; cursor:pointer;
                 border:1px solid #E5E7EB; background:#FFFFFF;
                 transition:all 0.15s; margin-bottom:6px; }
.provider-card:hover { border-color:#93C5FD; background:#F0F9FF; }
.provider-card.selected { border:1.5px solid #3B82F6; background:#EFF6FF; }
.provider-rank { width:24px; height:24px; border-radius:50%; background:#F3F4F6;
                 display:inline-flex; align-items:center; justify-content:center;
                 font-size:11px; font-weight:600; color:#6B7280; flex-shrink:0; }
.provider-name { font-size:0.88rem; font-weight:500; color:#111827; }
.provider-meta { font-size:0.75rem; color:#6B7280; }
.provider-score { font-size:0.875rem; font-weight:600; color:#2563EB; }
.stage-active { color:#059669; font-size:0.7rem; font-weight:500; }
.stage-warm   { color:#2563EB; font-size:0.7rem; font-weight:500; }
.stage-cold   { color:#9CA3AF; font-size:0.7rem; font-weight:500; }

/* Briefing sections */
.brief-card { padding:14px 16px; border-radius:10px; border:1px solid #E5E7EB;
              background:#FFFFFF; margin-bottom:10px; }
.brief-card-title { font-size:0.82rem; font-weight:600; color:#374151; margin-bottom:8px; }
.stat-box { padding:8px 10px; border-radius:6px; background:#F9FAFB; }
.stat-label { font-size:0.7rem; color:#9CA3AF; }
.stat-value { font-size:0.82rem; font-weight:500; color:#111827; margin-top:2px; }
.summary-box { padding:8px 10px; border-radius:6px; background:#F9FAFB;
               font-size:0.8rem; color:#374151; line-height:1.5; }
.product-primary { display:inline-block; padding:3px 10px; border-radius:20px;
                   background:#EFF6FF; color:#1D4ED8; font-size:0.78rem; font-weight:500; }
.product-secondary { display:inline-block; padding:3px 10px; border-radius:20px;
                     background:#F3F4F6; color:#6B7280; font-size:0.78rem; }
.objection-text { font-size:0.78rem; font-weight:500; color:#B45309; margin-bottom:4px; }
.handler-box { padding:8px 10px; border-radius:6px; background:#F9FAFB;
               border-left:3px solid #3B82F6; font-size:0.8rem;
               color:#374151; line-height:1.55; }
.source-text { font-size:0.7rem; color:#9CA3AF; font-style:italic; margin-top:4px; }
.script-box { padding:10px 12px; border-radius:6px; background:#F9FAFB;
              font-size:0.82rem; color:#111827; line-height:1.7; font-style:italic; }
.interest-item { font-size:0.78rem; color:#4B5563; display:flex; gap:6px; margin-bottom:3px; }
.formula-note { padding:8px 10px; border-radius:6px; background:#F9FAFB;
                font-size:0.7rem; color:#9CA3AF; margin-top:8px; }
.no-vendor-badge { display:inline-block; padding:2px 7px; border-radius:12px;
                   background:#F0FDF4; color:#166534; font-size:0.7rem; border:1px solid #BBF7D0; }
.existing-badge { display:inline-block; padding:2px 7px; border-radius:12px;
                  background:#EFF6FF; color:#1E40AF; font-size:0.7rem; border:1px solid #BFDBFE; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading (cached — runs once)
# ---------------------------------------------------------------------------
DEMO_MODE = not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


@st.cache_resource(show_spinner="Loading data and building knowledge base index...")
def init_app() -> tuple[pd.DataFrame, dict[str, Any], RAGPipeline]:
    providers_df, crm_data = load_data()
    ranked_df = score_and_rank(providers_df, crm_data)
    rag = RAGPipeline(kb_path="data/tempus_products.md", demo_mode=DEMO_MODE)
    return ranked_df, crm_data, rag


ranked_df, crm_data, rag = init_app()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "selected_id" not in st.session_state:
    st.session_state.selected_id = ranked_df.iloc[0]["provider_id"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
mode_badge = (
    '<span class="cop-badge badge-demo">⚡ Demo mode — no API key</span>'
    if DEMO_MODE
    else '<span class="cop-badge badge-live">🟢 Live — LLM enabled</span>'
)
st.markdown(
    f"""
<div class="cop-header">
  <div class="cop-logo">🔬</div>
  <div>
    <div class="cop-title">Tempus Sales Copilot</div>
    <div class="cop-subtitle">Midwest-1 territory · Mike Torres · {len(ranked_df)} providers ranked</div>
  </div>
  {mode_badge}
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Stage filter
# ---------------------------------------------------------------------------
filter_col1, filter_col2, filter_col3, filter_col4, _ = st.columns([1, 1, 1, 1, 6])
stage_filter = "all"
with filter_col1:
    if st.button("All", use_container_width=True):
        st.session_state.stage_filter = "all"
with filter_col2:
    if st.button("Active", use_container_width=True):
        st.session_state.stage_filter = "active"
with filter_col3:
    if st.button("Warm", use_container_width=True):
        st.session_state.stage_filter = "warm"
with filter_col4:
    if st.button("Cold", use_container_width=True):
        st.session_state.stage_filter = "cold"

if "stage_filter" not in st.session_state:
    st.session_state.stage_filter = "all"

filtered_df = (
    ranked_df
    if st.session_state.stage_filter == "all"
    else ranked_df[ranked_df["relationship_stage"] == st.session_state.stage_filter]
)

# Re-rank display positions after filter
filtered_df = filtered_df.copy().reset_index(drop=True)

# ---------------------------------------------------------------------------
# Two-column layout
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([5, 7], gap="large")

# ---------------------------------------------------------------------------
# LEFT PANEL — Provider rankings
# ---------------------------------------------------------------------------
with left_col:
    st.markdown(
        f"<div style='font-size:0.78rem;color:#6B7280;font-weight:500;margin-bottom:8px;'>"
        f"Priority rankings — {len(filtered_df)} providers</div>",
        unsafe_allow_html=True,
    )

    for i, row in filtered_df.iterrows():
        pid = row["provider_id"]
        is_selected = pid == st.session_state.selected_id
        stage = row["relationship_stage"]
        stage_cls = f"stage-{stage}"
        stage_label = stage.capitalize()
        vendor = str(row.get("current_testing_vendor", "")).strip()
        score_pct = int(row["score"] * 100)

        # Score bar (as thin colored strip)
        bar_width = score_pct
        bar_color = "#3B82F6" if score_pct >= 70 else "#F59E0B" if score_pct >= 50 else "#9CA3AF"

        card_class = "provider-card selected" if is_selected else "provider-card"
        st.markdown(
            f"""
<div class="{card_class}" id="card-{pid}">
  <div style="display:flex;align-items:center;gap:8px;">
    <span class="provider-rank">{i+1}</span>
    <div style="flex:1;min-width:0;">
      <div style="display:flex;align-items:center;gap:6px;">
        <span class="provider-name">{row['provider_name']}</span>
        <span class="{stage_cls}">{stage_label}</span>
      </div>
      <div class="provider-meta">{row['subspecialty']} · {row['est_annual_patients']} pts/yr</div>
      <div style="margin-top:4px;height:2px;background:#F3F4F6;border-radius:2px;">
        <div style="width:{bar_width}%;height:2px;background:{bar_color};border-radius:2px;"></div>
      </div>
    </div>
    <span class="provider-score">{score_pct}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button(f"Select", key=f"btn_{pid}", use_container_width=True):
            st.session_state.selected_id = pid
            st.rerun()

    st.markdown(
        f"""
<div class="formula-note">
  Score = {WEIGHTS['volume']}×volume + {WEIGHTS['fit']}×product fit + {WEIGHTS['recency']}×recency
  + {WEIGHTS['objection']}×objection resolvability + {WEIGHTS['sentiment']}×sentiment
  + {EXISTING_CUSTOMER_BONUS} existing customer bonus | +{NO_VENDOR_BONUS} greenfield bonus
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# RIGHT PANEL — Provider briefing
# ---------------------------------------------------------------------------
with right_col:
    sel_row = ranked_df[ranked_df["provider_id"] == st.session_state.selected_id]
    if sel_row.empty:
        st.info("Select a provider from the list to view their briefing.")
        st.stop()

    sel = sel_row.iloc[0]
    pid = sel["provider_id"]
    crm = crm_data.get(pid, {})
    cancer_types = [t.strip() for t in str(sel["primary_cancer_types"]).split(",")]
    matched = get_matched_products(cancer_types)
    vendor = str(sel.get("current_testing_vendor", "")).strip()
    objections = crm.get("objections", [])
    interests = crm.get("interests", [])

    # ── Provider header ────────────────────────────────────────────────
    initials = "".join(p[0] for p in sel["provider_name"].split() if p)[1:3].upper()
    score_pct = int(sel["score"] * 100)

    st.markdown(
        f"""
<div class="brief-card">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
    <div style="width:44px;height:44px;border-radius:50%;background:#EFF6FF;
                display:flex;align-items:center;justify-content:center;
                font-weight:600;font-size:14px;color:#1D4ED8;flex-shrink:0;">{initials}</div>
    <div style="flex:1;">
      <div style="font-size:1rem;font-weight:600;color:#111827;">{sel['provider_name']}</div>
      <div style="font-size:0.8rem;color:#6B7280;">{sel['institution']} · {sel['city']}, {sel['state']}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.3rem;font-weight:700;color:#2563EB;">{score_pct}</div>
      <div style="font-size:0.68rem;color:#9CA3AF;">priority score</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;">
    <div class="stat-box"><div class="stat-label">Patients/yr</div><div class="stat-value">{sel['est_annual_patients']}</div></div>
    <div class="stat-box"><div class="stat-label">Focus</div><div class="stat-value">{sel['subspecialty']}</div></div>
    <div class="stat-box"><div class="stat-label">Current vendor</div><div class="stat-value">{vendor if vendor and vendor.lower() not in ('none', 'nan', '') else '—'}</div></div>
  </div>
  <div class="summary-box"><span style="font-weight:600;color:#111827;">Why now: </span>{crm.get('summary', '—')}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Best-fit product ───────────────────────────────────────────────
    secondary_html = " ".join(
        f'<span class="product-secondary">{s}</span>' for s in matched["secondary"]
    )
    reason_text = matched["reasons"][0] if matched["reasons"] else "Comprehensive genomic profiling"
    st.markdown(
        f"""
<div class="brief-card">
  <div class="brief-card-title">Best-fit product</div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">
    <span class="product-primary">{matched['primary']}</span>
    {secondary_html}
  </div>
  <div style="font-size:0.78rem;color:#6B7280;line-height:1.5;">{reason_text}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Objection handler ──────────────────────────────────────────────
    if objections:
        obj_items_html = ""
        for obj in objections:
            handler_result = rag.generate_objection_handler(
                pid, obj, provider_context=f"{sel['subspecialty']}, {sel['institution']}"
            )
            mode_note = (
                '<span style="font-size:0.65rem;color:#9CA3AF;margin-left:4px;">[demo]</span>'
                if handler_result["mode"] in ("demo", "fallback")
                else '<span style="font-size:0.65rem;color:#059669;margin-left:4px;">[AI]</span>'
            )
            obj_items_html += f"""
<div style="margin-bottom:12px;">
  <div class="objection-text">"{obj}"</div>
  <div class="handler-box">{handler_result['response']}</div>
  <div class="source-text">Source: {handler_result['sources']}</div>
</div>
"""
        st.markdown(
            f"""
<div class="brief-card">
  <div class="brief-card-title">⚠ Objection handler</div>
  {obj_items_html}
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Meeting script ─────────────────────────────────────────────────
    provider_context_for_script = {
        "provider_id": pid,
        "name": sel["provider_name"],
        "subspecialty": sel["subspecialty"],
        "cancer_types": cancer_types,
        "patients": sel["est_annual_patients"],
        "current_vendor": vendor,
        "matched_product": matched["primary"],
        "interests": interests,
        "objections": objections,
    }

    with st.spinner("Generating meeting script...") if not DEMO_MODE else nullcontext():
        script_result = rag.generate_meeting_script(provider_context_for_script)

    mode_label = (
        '<span style="font-size:0.65rem;color:#9CA3AF;"> [demo]</span>'
        if script_result["mode"] in ("demo", "fallback")
        else '<span style="font-size:0.65rem;color:#059669;"> [AI-generated]</span>'
    )
    st.markdown(
        f"""
<div class="brief-card">
  <div class="brief-card-title">💬 30-second meeting script{mode_label}</div>
  <div class="script-box">"{script_result['script']}"</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── CRM talking points ─────────────────────────────────────────────
    if interests:
        items_html = "".join(
            f'<div class="interest-item"><span style="color:#3B82F6;flex-shrink:0;">+</span>{interest}</div>'
            for interest in interests
        )
        st.markdown(
            f"""
<div class="brief-card">
  <div class="brief-card-title">📋 Talking points from CRM</div>
  {items_html}
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Competitive context (when on a competitor) ─────────────────────
    comp_notes = {
        "Foundation Medicine": "Tempus advantage: tumor-normal matched sequencing reduces false positives vs F1CDx tumor-only approach. Auto-reflex to xF when tissue is insufficient. Comprehensive portfolio (tissue + liquid + hereditary + MRD) under one roof.",
        "Guardant Health": "Tempus advantage: Guardant is liquid-only. Tempus offers complete tissue + liquid strategy (xT CDx + xF). FDA-approved CDx claims for CRC. Hereditary testing (xG/xG+) — Guardant has no germline offering.",
        "Caris Life Sciences": "Tempus advantage: dedicated whole-transcriptome RNA sequencing (xR) for fusion detection Caris misses. Tumor-normal matching for cleaner somatic calls. MRD monitoring (xM) for post-treatment tracking.",
    }
    if vendor in comp_notes:
        st.markdown(
            f"""
<div class="brief-card" style="border-left:3px solid #F59E0B;">
  <div class="brief-card-title">🎯 vs. {vendor}</div>
  <div style="font-size:0.78rem;color:#374151;line-height:1.55;">{comp_notes[vendor]}</div>
</div>
""",
            unsafe_allow_html=True,
        )


