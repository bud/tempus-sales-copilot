"""RAG pipeline for Tempus Sales Copilot.

Architecture:
  1. Load product KB markdown → split into section chunks
  2. Embed chunks with sentence-transformers (all-MiniLM-L6-v2)
  3. retrieve(query) → cosine similarity top-k chunks
  4. generate_objection_handler() / generate_meeting_script() → LLM call or demo fallback
"""
from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Demo-mode mock meeting scripts (ported from JSX prototype)
# ---------------------------------------------------------------------------
_DEMO_SCRIPTS: dict[str, str] = {
    "P001": "Dr. Chen, I know you've been frustrated with Foundation Medicine's turnaround times — Tempus xT CDx delivers results in 10–14 days, and our auto-reflex to liquid biopsy means no reorders if tissue is insufficient. With your BRCA patient population, I'd also love to show you how bundled somatic + hereditary testing through one platform can simplify your workflow. Can we find 15 minutes this week?",
    "P002": "Dr. Patel, your NSCLC practice already has excellent liquid biopsy coverage through Guardant — but tissue-based RNA sequencing is the gap. Tempus xT CDx + xR catches ALK, ROS1, and RET fusions that DNA-only panels miss, with results in 10–14 days. If tissue is ever insufficient, we auto-reflex to liquid biopsy, so your patients never wait on a reorder. Can we walk through the auto-reflex workflow?",
    "P003": "Dr. Kim, for your CRC patients, Tempus xT CDx is FDA-approved as a companion diagnostic and uses genome-wide MSI analysis across 239 loci — far more comprehensive than traditional 5-marker testing, which can miss 15–20% of MSI-H cases. In a validation study, 88.6% of samples had at least one actionable alteration. I'd love to share a CRC case study showing how comprehensive profiling changed the treatment plan. Would a 20-minute lunch work?",
    "P004": "Dr. Rodriguez, you've had cholangiocarcinoma cases where Caris came back with no actionable findings — but clinical suspicion said FGFR fusion. Tempus xR whole-transcriptome RNA sequencing is purpose-built for exactly this: detecting FGFR2 fusions that DNA-only panels miss. I'd like to bring our Medical Science Liaison to your tumor board in January to walk through the published data. Does that timing still work?",
    "P005": "Dr. Thompson, your xT CDx adoption for solid tumors has been outstanding. The next logical step is xM MRD monitoring for your AML patients post-induction — enabling earlier intervention decisions based on molecular evidence rather than waiting for imaging. We also have clinical trial matching through our TIME Trial program that could help your patients who've exhausted standard options. When can we connect to discuss the MRD workflow?",
    "P006": "Dr. O'Brien, for your metastatic breast patients, Tempus xT CDx provides the comprehensive PIK3CA, ESR1, and BRCA profiling that Oncotype DX doesn't cover — and our financial assistance program ensures out-of-pocket cost decisions immediately for your patient population. I'd love to connect with your nurse navigator Maria to make this as easy as possible for your team. Would that work as a starting point?",
    "P007": "Dr. Zhao, your xT CDx program is exceptional — and the natural next step is xF liquid biopsy for your osimertinib patients to track T790M resistance mutations as they emerge. Serial liquid biopsy lets you catch resistance before it's clinically apparent. I also have T790M detection rate data comparing xF to tissue rebiopsy that I think you'll find compelling. When's a good time for a quick review?",
    "P008": "Dr. Nakamura, with the growing evidence for PARP inhibitor eligibility in BRCA-mutated prostate cancer, hereditary testing is becoming standard of care for the families in your practice. Tempus xG+ covers 77 hereditary cancer genes with free genetic counseling through Genome Medical, and cascade testing for at-risk relatives. Could you introduce me to Dr. Singh so we can make sure your patients aren't missing PARP eligibility workups?",
    "P009": "Dr. Petrov, the most significant gap with FoundationOne CDx for your GBM patients is MGMT promoter methylation — which drives your temozolomide decisions. Tempus xR includes MGMT methylation as an add-on, plus comprehensive IDH1/2 detection. I can share our concordance data with methylation-specific PCR. Would you be open to a call with our MSL to walk through the analytical validation?",
    "P010": "Dr. Williams, Tempus xT CDx is FDA-approved as a companion diagnostic for your CRC patients, and our genome-wide MSI testing with 239 loci outperforms traditional 5-marker IHC — catching MSI-H cases your current workflow might miss. For your EHR integration concern, we support direct ordering from your system, no separate portal required. Can I set up a 20-minute demo of the ordering workflow?",
}


class RAGPipeline:
    """RAG pipeline: embed product KB, retrieve relevant chunks, generate responses."""

    def __init__(self, kb_path: str = "data/tempus_products.md", demo_mode: bool = False) -> None:
        self.demo_mode = demo_mode
        self.chunks: list[dict[str, str]] = []
        self._embeddings: Any = None  # numpy array
        self._model: Any = None

        self._load_and_chunk_kb(kb_path)

        if not demo_mode:
            self._build_index()

    # ------------------------------------------------------------------
    # KB loading and chunking
    # ------------------------------------------------------------------

    def _load_and_chunk_kb(self, kb_path: str) -> None:
        """Split markdown into section chunks with metadata."""
        path = Path(kb_path)
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")
        # Split on ## headings
        sections = re.split(r"\n(?=## )", text)
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().splitlines()
            title = lines[0].lstrip("#").strip() if lines else "General"
            body = "\n".join(lines[1:]).strip()
            if len(body) < 20:
                continue
            # Further split long sections into ~400-char sub-chunks
            sub_chunks = self._split_text(body, max_chars=600)
            for i, chunk in enumerate(sub_chunks):
                self.chunks.append({
                    "id": f"{title}_{i}",
                    "title": title,
                    "text": chunk,
                    "source": f"tempus_products.md — {title}",
                })

    @staticmethod
    def _split_text(text: str, max_chars: int = 600) -> list[str]:
        """Split text at paragraph boundaries up to max_chars."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) + 2 > max_chars and current:
                chunks.append(current.strip())
                current = para
            else:
                current = (current + "\n\n" + para).strip()
        if current:
            chunks.append(current.strip())
        return chunks or [text]

    # ------------------------------------------------------------------
    # Vector index
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        """Build sentence-transformer embeddings for all chunks."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            texts = [c["text"] for c in self.chunks]
            self._embeddings = self._model.encode(texts, normalize_embeddings=True)
        except ImportError:
            # Fall back to demo mode if sentence-transformers not installed
            self.demo_mode = True

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, str]]:
        """Return top-k most relevant KB chunks for the query."""
        if self.demo_mode or self._model is None or self._embeddings is None:
            return self._keyword_retrieve(query, k)
        import numpy as np
        q_emb = self._model.encode([query], normalize_embeddings=True)
        scores = (self._embeddings @ q_emb.T).flatten()
        top_idx = scores.argsort()[::-1][:k]
        return [self.chunks[i] for i in top_idx]

    def _keyword_retrieve(self, query: str, k: int = 3) -> list[dict[str, str]]:
        """Fallback: keyword-based retrieval."""
        query_lower = query.lower()
        keywords = [w for w in re.split(r"\W+", query_lower) if len(w) > 3]
        scored = []
        for chunk in self.chunks:
            text_lower = chunk["text"].lower()
            score = sum(text_lower.count(kw) for kw in keywords)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k] if _ > 0] or self.chunks[:k]

    # ------------------------------------------------------------------
    # LLM calls
    # ------------------------------------------------------------------

    def _call_llm(self, system: str, user: str) -> str:
        """Call LLM API. Returns generated text or raises on failure."""
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        if anthropic_key:
            return self._call_anthropic(system, user, anthropic_key)
        if openai_key:
            return self._call_openai(system, user, openai_key)
        raise RuntimeError("No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

    def _call_openai(self, system: str, user: str, api_key: str) -> str:
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()

    def _call_anthropic(self, system: str, user: str, api_key: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()

    # ------------------------------------------------------------------
    # Public generation API
    # ------------------------------------------------------------------

    def generate_objection_handler(
        self, provider_id: str, objection: str, provider_context: str = ""
    ) -> dict[str, str]:
        """Generate a grounded objection response. Returns {response, sources, mode}."""
        from scoring import find_handler_key, OBJECTION_HANDLERS

        # Always try demo handler first as baseline
        handler_key = find_handler_key(objection)
        demo_handler = OBJECTION_HANDLERS.get(handler_key, {}) if handler_key else {}

        if self.demo_mode:
            if demo_handler:
                return {
                    "response": demo_handler["response"],
                    "sources": demo_handler["source"],
                    "mode": "demo",
                }
            return {
                "response": "No verified data available — recommend consulting Medical Affairs for this specific concern.",
                "sources": "N/A",
                "mode": "demo",
            }

        # RAG + LLM path
        chunks = self.retrieve(objection, k=3)
        context_text = "\n\n---\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )
        sources = "; ".join(c["source"] for c in chunks)

        system = (
            "You are a Tempus oncology sales expert. Using ONLY the provided knowledge base excerpts, "
            "write a concise, confident 2–3 sentence response to the sales objection. "
            "Cite specific data points (turnaround times, approval status, study results). "
            "If the context doesn't contain relevant data, say exactly: "
            "'No verified data available — recommend consulting Medical Affairs.' "
            "Do NOT invent statistics or claims not in the context."
        )
        user = (
            f"Objection: {objection}\n\n"
            f"Provider context: {provider_context}\n\n"
            f"Knowledge base context:\n{context_text}\n\n"
            "Write the response:"
        )

        try:
            response = self._call_llm(system, user)
            return {"response": response, "sources": sources, "mode": "llm"}
        except Exception as e:
            # Graceful fallback to demo handler
            if demo_handler:
                return {"response": demo_handler["response"], "sources": demo_handler["source"], "mode": "fallback"}
            return {
                "response": "No verified data available — recommend consulting Medical Affairs.",
                "sources": "N/A",
                "mode": "error",
            }

    def generate_meeting_script(self, provider_data: dict[str, Any]) -> dict[str, str]:
        """Generate a personalized 30-second meeting script. Returns {script, mode}."""
        pid = provider_data.get("provider_id", "")

        if self.demo_mode:
            script = _DEMO_SCRIPTS.get(pid, _fallback_script(provider_data))
            return {"script": script, "mode": "demo"}

        # Build context for LLM
        cancer_types = provider_data.get("cancer_types", [])
        chunks = self.retrieve(
            f"{' '.join(cancer_types)} oncology genomic testing treatment", k=3
        )
        context_text = "\n\n---\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )

        system = (
            "You are writing a 30-second meeting script for a Tempus oncology sales rep. "
            "Rules: 3–4 sentences max. Must name the specific Tempus product. Must reference the "
            "doctor's patient population or specialty. Must address one known interest or pain point. "
            "End with a specific call to action. Sound natural and confident, not scripted. "
            "Use ONLY information from the provided context — no invented statistics."
        )

        interests = provider_data.get("interests", [])
        objections = provider_data.get("objections", [])
        user = (
            f"Doctor: {provider_data.get('name', 'Doctor')}\n"
            f"Specialty: {provider_data.get('subspecialty', '')}\n"
            f"Cancer types: {', '.join(cancer_types)}\n"
            f"Patient volume: {provider_data.get('patients', '')} patients/year\n"
            f"Current vendor: {provider_data.get('current_vendor', 'None')}\n"
            f"Known interests: {'; '.join(interests[:2]) if interests else 'None noted'}\n"
            f"Known concerns: {'; '.join(objections[:1]) if objections else 'None noted'}\n"
            f"Best-fit product: {provider_data.get('matched_product', 'xT CDx')}\n\n"
            f"Relevant product knowledge:\n{context_text}\n\n"
            "Write the 30-second script (spoken word, first person as the rep):"
        )

        try:
            script = self._call_llm(system, user)
            return {"script": script, "mode": "llm"}
        except Exception:
            return {"script": _DEMO_SCRIPTS.get(pid, _fallback_script(provider_data)), "mode": "fallback"}

    def extract_crm_structure(self, notes_text: str) -> dict[str, Any]:
        """Use LLM to extract structured fields from raw CRM note text."""
        if self.demo_mode:
            return {}  # demo mode uses pre-labeled data from scoring.py

        system = (
            "Extract structured information from the CRM notes. "
            "Return valid JSON only with these fields:\n"
            '{\n'
            '  "objections": ["list of specific objections or concerns raised"],\n'
            '  "interests": ["list of topics the doctor expressed interest in"],\n'
            '  "sentiment": "one of: very positive, positive, warming, neutral",\n'
            '  "summary": "1–2 sentence summary of the opportunity and current status"\n'
            "}\n"
            "Use ONLY information present in the notes. Do not invent or infer beyond what's written."
        )
        user = f"CRM Notes:\n{notes_text}\n\nReturn JSON:"

        try:
            raw = self._call_llm(system, user)
            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception:
            return {}


def _fallback_script(provider_data: dict[str, Any]) -> str:
    """Generate a basic fallback script when neither demo data nor LLM is available."""
    name = provider_data.get("name", "Doctor")
    last_name = name.split()[-1] if name else "Doctor"
    product = provider_data.get("matched_product", "xT CDx")
    subspecialty = provider_data.get("subspecialty", "oncology")
    patients = provider_data.get("patients", "")
    vendor = provider_data.get("current_vendor", "None")

    if vendor.lower() == "tempus":
        return (
            f"Dr. {last_name}, thank you for your continued partnership — your team's use of "
            f"Tempus is setting a strong standard for comprehensive profiling. I'd love to discuss "
            f"how we can deepen our support for your {subspecialty.lower()} practice."
        )
    if vendor.lower() in ("none", ""):
        return (
            f"Dr. {last_name}, with your {patients}+ {subspecialty.lower()} patients annually, "
            f"there's a significant opportunity to improve treatment selection with Tempus {product}. "
            f"I'd welcome 15 minutes to show you how other practices in your space are using these "
            f"results to guide clinical decisions."
        )
    return (
        f"Dr. {last_name}, I know you're currently using {vendor} for your {subspecialty.lower()} patients. "
        f"Tempus {product} offers capabilities that complement — and in several areas exceed — what "
        f"you're getting today. Can we schedule 15 minutes to walk through the specifics?"
    )
