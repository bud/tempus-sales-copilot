import { useState, useEffect, useMemo } from "react";

const PROVIDERS = [
  { id:"P001", name:"Dr. Sarah Chen", specialty:"Medical Oncology", subspecialty:"Breast Cancer", institution:"Memorial Regional Medical Center", patients:320, cancerTypes:["breast","ovarian"], currentVendor:"Foundation Medicine", lastContact:"2025-12-02", stage:"warm" },
  { id:"P002", name:"Dr. Raj Patel", specialty:"Medical Oncology", subspecialty:"Thoracic/Lung", institution:"Lakeview Cancer Institute", patients:280, cancerTypes:["NSCLC","SCLC"], currentVendor:"Guardant Health", lastContact:"2025-10-18", stage:"warm" },
  { id:"P003", name:"Dr. Emily Kim", specialty:"Medical Oncology", subspecialty:"GI/Colorectal", institution:"Northwest Community Hospital", patients:190, cancerTypes:["colorectal","pancreatic"], currentVendor:"None", lastContact:"2025-09-05", stage:"cold" },
  { id:"P004", name:"Dr. Carlos Rodriguez", specialty:"Medical Oncology", subspecialty:"GI/Hepatobiliary", institution:"Rush University Medical Center", patients:150, cancerTypes:["pancreatic","cholangiocarcinoma","gastric"], currentVendor:"Caris Life Sciences", lastContact:"2025-11-20", stage:"warm" },
  { id:"P005", name:"Dr. Aisha Thompson", specialty:"Hematology-Oncology", subspecialty:"Hematologic Malignancies", institution:"University of Chicago Medicine", patients:210, cancerTypes:["AML","MDS","lymphoma"], currentVendor:"Foundation Medicine", lastContact:"2025-12-10", stage:"active" },
  { id:"P006", name:"Dr. James O'Brien", specialty:"Medical Oncology", subspecialty:"Breast Cancer", institution:"Advocate Christ Medical Center", patients:180, cancerTypes:["breast","ovarian"], currentVendor:"None", lastContact:"2025-08-12", stage:"cold" },
  { id:"P007", name:"Dr. Mei-Lin Zhao", specialty:"Medical Oncology", subspecialty:"Thoracic/Lung", institution:"Northwestern Memorial Hospital", patients:420, cancerTypes:["NSCLC","mesothelioma"], currentVendor:"Tempus", lastContact:"2025-12-15", stage:"active" },
  { id:"P008", name:"Dr. David Nakamura", specialty:"Surgical Oncology", subspecialty:"Urologic", institution:"Edward-Elmhurst Health", patients:95, cancerTypes:["prostate","renal","bladder"], currentVendor:"None", lastContact:"2025-07-22", stage:"cold" },
  { id:"P009", name:"Dr. Lisa Petrov", specialty:"Medical Oncology", subspecialty:"Neuro-Oncology", institution:"Loyola University Medical Center", patients:75, cancerTypes:["glioblastoma","brain"], currentVendor:"Foundation Medicine", lastContact:"2025-11-01", stage:"warm" },
  { id:"P010", name:"Dr. Marcus Williams", specialty:"Medical Oncology", subspecialty:"GI/Colorectal", institution:"NorthShore University HealthSystem", patients:230, cancerTypes:["colorectal","gastric","esophageal"], currentVendor:"Guardant Health", lastContact:"2025-10-30", stage:"warm" },
];

const CRM_NOTES = {
  P001: { objections:["Turnaround time with current vendor (3+ weeks)","Insurance coverage concerns for community hospital patients"], interests:["Hereditary testing for BRCA population","xT CDx vs F1CDx comparison for breast","Bundled hereditary + somatic testing","Case studies for tumor board"], sentiment:"positive", summary:"High-volume breast oncologist frustrated with Foundation Medicine turnaround. Actively evaluating alternatives. Interested in combined somatic + hereditary testing." },
  P002: { objections:["Turnaround time — patients need to start treatment quickly","Specimen handling/shipping logistics for tissue"], interests:["xT + xF combo approach","Auto-reflex workflow","ALK and ROS1 fusion detection rates vs FISH"], sentiment:"positive", summary:"Large lung practice using Guardant for liquid only — no tissue-based NGS provider. Major gap. Interested in comprehensive tissue + liquid strategy." },
  P003: { objections:["Skeptical about clinical utility beyond current IHC/MSI testing","Doesn't see value in broader panels"], interests:[], sentiment:"neutral", summary:"GI oncologist relying solely on hospital pathology. Needs education on how comprehensive profiling changes treatment decisions for CRC/pancreatic patients." },
  P004: { objections:["Satisfied with current Caris platform","Switching costs"], interests:["RNA sequencing for fusion detection","FGFR2 fusions in cholangiocarcinoma","Lunch-and-learn for tumor board"], sentiment:"warming", summary:"Currently on Caris but recognizes RNA sequencing gap. Had cholangio cases where DNA-only panels missed suspected fusions. Scheduling tumor board presentation." },
  P005: { objections:[], interests:["xM MRD monitoring for AML patients","Clinical trial matching for exhausted-options patients","Expanding Tempus volume across heme + solid tumor"], sentiment:"very positive", summary:"Existing customer, very satisfied. Growth opportunity — could double volume with MRD monitoring and expanded heme testing." },
  P006: { objections:["Cost concerns for patient population","Very busy, hard to reach"], interests:[], sentiment:"neutral", summary:"Breast oncologist using only Oncotype DX and limited IHC. Needs education on broader panel value for metastatic breast. Nurse navigator Maria may be better entry point." },
  P007: { objections:[], interests:["xF liquid biopsy for resistance monitoring (osimertinib patients)","PD-L1 IHC add-on","Departmental presentation on liquid biopsy","T790M resistance mutation detection rates","Warm intro to new colleague Dr. Park"], sentiment:"very positive", summary:"Champion account at Northwestern. Consistent xT CDx orderer. Expansion opportunity with xF for treatment monitoring and onboarding new colleague." },
  P008: { objections:["Doesn't order genomic testing directly","Lower direct testing volume"], interests:["Hereditary testing for BRCA-related prostate cancer families"], sentiment:"neutral", summary:"Surgical oncologist — referral pathway, not direct orderer. Could influence medical oncology partner Dr. Singh. Interest in hereditary prostate testing." },
  P009: { objections:["Wants concordance data vs current methylation-specific PCR"], interests:["MGMT promoter methylation analysis (xR add-on)","IDH1/2 mutation detection sensitivity","MSL consultation"], sentiment:"positive", summary:"Neuro-oncologist whose key pain point is F1CDx lacking MGMT methylation. Tempus xR with MGMT add-on is a strong differentiator. Needs validation data." },
  P010: { objections:["Focused on clinical evidence and workflow integration"], interests:["xT CDx companion diagnostic for CRC","MSI testing methodology (genome-wide vs 5-marker)","PurIST for pancreatic referrals","EHR integration"], sentiment:"positive", summary:"Large GI practice on Guardant for liquid only. Strong fit for xT CDx with FDA-approved CRC companion diagnostic. Evidence-driven buyer." },
};

const PRODUCT_MATCH = {
  breast: { primary:"xT CDx", secondary:["xG/xG+","xF"], reason:"648-gene panel catches PIK3CA, ESR1, BRCA mutations; hereditary testing for BRCA families; liquid biopsy for resistance monitoring" },
  ovarian: { primary:"xT CDx", secondary:["xG/xG+"], reason:"Comprehensive profiling for HRD status, BRCA1/2; hereditary panel for family risk" },
  NSCLC: { primary:"xT CDx + xR", secondary:["xF/xF+"], reason:"DNA + RNA catches ALK/ROS1/RET/NTRK fusions; liquid biopsy for resistance monitoring" },
  SCLC: { primary:"xT CDx", secondary:["xF"], reason:"Comprehensive profiling for emerging targeted therapy options" },
  colorectal: { primary:"xT CDx", secondary:["xF"], reason:"FDA-approved CDx for CRC; genome-wide MSI; KRAS/NRAS/BRAF profiling" },
  pancreatic: { primary:"xT CDx + xR", secondary:["xF"], reason:"PurIST algorithmic diagnostic for PDAC; RNA for rare fusions; comprehensive profiling" },
  cholangiocarcinoma: { primary:"xR + xT CDx", secondary:["xF"], reason:"RNA sequencing critical for FGFR2 fusion detection; DNA for IDH1/2 and other targets" },
  gastric: { primary:"xT CDx", secondary:["xF"], reason:"HER2 assessment, MSI status, comprehensive biomarker profiling" },
  AML: { primary:"xT", secondary:["xM"], reason:"Comprehensive heme profiling; MRD monitoring for post-treatment tracking" },
  MDS: { primary:"xT", secondary:["xM"], reason:"Genomic profiling for risk stratification and treatment selection" },
  lymphoma: { primary:"xT", secondary:[], reason:"Hematologic testing for mutation profiling and treatment guidance" },
  glioblastoma: { primary:"xR + xT CDx", secondary:[], reason:"MGMT methylation (xR add-on) critical for treatment decisions; IDH1/2 mutation detection" },
  brain: { primary:"xR + xT CDx", secondary:[], reason:"RNA for fusion detection and MGMT; DNA for comprehensive profiling" },
  prostate: { primary:"xT CDx", secondary:["xG/xG+"], reason:"BRCA1/2 for PARP inhibitor eligibility; hereditary testing for family risk" },
  renal: { primary:"xT CDx", secondary:["xG/xG+"], reason:"Comprehensive profiling; hereditary testing for VHL and other syndromes" },
  bladder: { primary:"xT CDx", secondary:["xF"], reason:"FGFR alterations, TMB for immunotherapy; liquid biopsy for monitoring" },
  mesothelioma: { primary:"xT CDx + xR", secondary:[], reason:"Comprehensive profiling for emerging treatments; RNA for fusions" },
  esophageal: { primary:"xT CDx", secondary:["xF"], reason:"HER2, MSI, PD-L1 biomarker profiling for treatment selection" },
};

const OBJECTION_HANDLERS = {
  "Turnaround time": { response: "I understand timing is critical for your patients. Tempus xT CDx results are typically delivered within 10–14 calendar days of specimen receipt. Plus, our auto-conversion feature means if tissue is insufficient, we automatically reflex to xF liquid biopsy — your patient never waits for a reorder. That's often faster end-to-end than resubmitting to another lab.", source: "Tempus Patient Resources — turnaround time; xT/xR product page — auto-conversion" },
  "Insurance coverage": { response: "Tempus offers a transparent financial assistance program for all U.S. patients, regardless of insurance status. Patients get an immediate out-of-pocket cost determination upon applying at access.tempus.com. We work directly with insurance companies on reimbursement so your team doesn't carry that burden.", source: "Tempus Financial Assistance Program; Patient Resources page" },
  "Cost concerns": { response: "We understand cost is a real consideration for your patients. Tempus provides financial assistance to all U.S. patients regardless of insurance status, with immediate out-of-pocket cost decisions. For uninsured patients, we have a self-pay option. The goal is ensuring cost is never a barrier to accessing precision medicine.", source: "Tempus Financial Assistance Program; tempus.com/patients" },
  "Skeptical about clinical utility": { response: "I appreciate that perspective — let me share some data. In a validation study of the xT panel, 88.6% of clinical samples contained at least one biologically relevant alteration that could inform treatment decisions. For CRC specifically, xT CDx is FDA-approved as a companion diagnostic, and our genome-wide MSI analysis using 239 loci is more comprehensive than traditional 5-marker testing. These aren't just more results — they're results that change treatment decisions.", source: "Nat Biotechnol 2019 xT validation study; FDA xT CDx approval; MSI methodology documentation" },
  "Satisfied with current vendor": { response: "That's great that you're already leveraging genomic testing. What we hear from physicians who've made the switch is that the value isn't just in the panel — it's in the platform. Tempus combines tissue, liquid biopsy, RNA sequencing, hereditary testing, and MRD monitoring under one roof. That means one ordering workflow, one portal, and comprehensive results that connect across test types.", source: "Tempus product portfolio; Tempus Hub platform" },
  "Specimen handling logistics": { response: "We've streamlined the process significantly. You can order through Tempus Hub online, via paper requisition, or directly from your EHR. For tissue, we coordinate with your hospital's pathology department to obtain the specimen. For liquid biopsy, it's a simple blood draw in two Streck tubes shipped via the included FedEx label. Our support team at 800.739.4137 handles any logistics questions.", source: "Tempus ordering workflow; xF collection requirements; Customer Support" },
  "Switching costs": { response: "We make the transition straightforward. Tempus Hub provides a streamlined ordering process — online, paper, or EHR-integrated. We handle pathology coordination for tissue retrieval, and our team supports onboarding from day one. Many practices run both vendors in parallel initially, then consolidate once they see the results.", source: "Tempus Hub; onboarding process" },
  "Concordance/validation data": { response: "Absolutely — we have extensive validation data. The xT assay was clinically validated on 1,074 clinical samples across diverse cancer types, with results published in Nature Biotechnology. The xT CDx specifically was validated against externally validated orthogonal methods for both variant detection and MSI status. I can connect you with our Medical Science Liaison to walk through the specific concordance data relevant to your practice.", source: "Nat Biotechnol 2019; FDA xT CDx label; NCBI GTR Tempus xT documentation" },
  "EHR integration": { response: "Tempus supports direct ordering from your EHR system — no separate portal required if that's your preference. Results can also be accessed through Tempus Hub and Tempus One, our AI-enabled clinical assistant. We work with your IT team to set up the integration that fits your workflow.", source: "Tempus Hub; Tempus One; EHR ordering documentation" },
};

function daysSince(dateStr) {
  const d = new Date(dateStr);
  const now = new Date("2026-01-15");
  return Math.floor((now - d) / (1000*60*60*24));
}

function computeScore(p) {
  const maxPts = 420;
  const volScore = Math.min(p.patients / maxPts, 1);
  const fitTypes = p.cancerTypes.filter(t => PRODUCT_MATCH[t]);
  const fitScore = fitTypes.length > 0 ? Math.min(fitTypes.length / 2, 1) : 0.2;
  const days = daysSince(p.lastContact);
  const recencyScore = Math.max(0, 1 - (days / 180));
  const notes = CRM_NOTES[p.id];
  const objResolvable = notes.objections.length > 0 ? 0.8 : 0.3;
  const sentimentMap = { "very positive": 1, "positive": 0.8, "warming": 0.65, "neutral": 0.4 };
  const warmth = sentimentMap[notes.sentiment] || 0.4;
  const isExistingCustomer = p.currentVendor === "Tempus" ? 0.3 : 0;
  const noVendor = p.currentVendor === "None" ? 0.15 : 0;
  const raw = 0.30*volScore + 0.25*fitScore + 0.15*recencyScore + 0.15*objResolvable + 0.10*warmth + isExistingCustomer + noVendor;
  return Math.min(raw, 1);
}

function getMatchedProduct(cancerTypes) {
  const primary = new Set();
  const secondary = new Set();
  const reasons = [];
  cancerTypes.forEach(t => {
    const m = PRODUCT_MATCH[t];
    if (m) {
      primary.add(m.primary);
      m.secondary.forEach(s => secondary.add(s));
      reasons.push(m.reason);
    }
  });
  return { primary: [...primary].join(" + "), secondary: [...secondary], reasons };
}

function generateScript(p) {
  const notes = CRM_NOTES[p.id];
  const match = getMatchedProduct(p.cancerTypes);
  const interest = notes.interests[0];
  const types = p.cancerTypes.join("/").toUpperCase();
  if (p.currentVendor === "Tempus") {
    return `Dr. ${p.name.split(" ").pop()}, thank you for your continued partnership — your team's use of xT CDx has been setting a strong standard for comprehensive profiling. I wanted to follow up on your interest in ${interest || "expanding testing capabilities"}. ${match.reasons[0] ? `With your ${types} patient volume, ${match.reasons[0].split(";")[0]}.` : ""} I'd love to discuss how we can deepen our support for your practice.`;
  }
  if (p.currentVendor === "None") {
    return `Dr. ${p.name.split(" ").pop()}, with your ${p.patients}+ ${types} patients annually, I believe there's a significant opportunity to improve treatment selection with comprehensive genomic profiling. Tempus ${match.primary} provides ${match.reasons[0] ? match.reasons[0].split(";")[0] : "actionable molecular insights"} — all through a single platform with a streamlined ordering process. I'd welcome 15 minutes to show you how other ${p.subspecialty.toLowerCase()} practices are using these results to guide clinical decisions.`;
  }
  return `Dr. ${p.name.split(" ").pop()}, I know you're currently using ${p.currentVendor} for your ${types} patients. ${interest ? `You mentioned interest in ${interest.toLowerCase()} —` : "What I'd like to share is"} Tempus ${match.primary} offers ${match.reasons[0] ? match.reasons[0].split(";")[0] : "comprehensive molecular profiling"}. ${notes.objections[0] ? `Regarding your concern about ${notes.objections[0].toLowerCase().split("—")[0].split("(")[0].trim()}, ${OBJECTION_HANDLERS[Object.keys(OBJECTION_HANDLERS).find(k => notes.objections[0].toLowerCase().includes(k.toLowerCase()))]?.response.split(".")[0] || "we have strong data to address that"}.` : ""} Can we schedule 15 minutes to walk through the specifics?`;
}

function matchObjToHandler(objection) {
  const key = Object.keys(OBJECTION_HANDLERS).find(k => objection.toLowerCase().includes(k.toLowerCase()));
  return key ? { key, ...OBJECTION_HANDLERS[key] } : null;
}

const stageColors = { active:"var(--color-text-success)", warm:"var(--color-text-info)", cold:"var(--color-text-secondary)" };
const stageLabels = { active:"Active", warm:"Warm", cold:"Cold" };

export default function TempusCopilot() {
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState("all");
  const [generating, setGenerating] = useState(false);
  const [generatedScript, setGeneratedScript] = useState("");

  const scored = useMemo(() => {
    return PROVIDERS.map(p => ({ ...p, score: computeScore(p) })).sort((a,b) => b.score - a.score);
  }, []);

  const filtered = filter === "all" ? scored : scored.filter(p => p.stage === filter);

  const handleSelect = (p) => {
    setSelected(p);
    setGenerating(true);
    setGeneratedScript("");
    setTimeout(() => {
      setGeneratedScript(generateScript(p));
      setGenerating(false);
    }, 800);
  };

  const sp = selected ? CRM_NOTES[selected.id] : null;
  const matchedProduct = selected ? getMatchedProduct(selected.cancerTypes) : null;

  return (
    <div style={{ fontFamily:"var(--font-sans)", color:"var(--color-text-primary)", maxWidth:960, margin:"0 auto" }}>
      <div style={{ padding:"1.5rem 0 1rem", borderBottom:"0.5px solid var(--color-border-tertiary)", marginBottom:"1.25rem", display:"flex", alignItems:"center", gap:12 }}>
        <div style={{ width:36, height:36, borderRadius:"var(--border-radius-md)", background:"var(--color-background-info)", display:"flex", alignItems:"center", justifyContent:"center" }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2L3 6v8l7 4 7-4V6l-7-4z" stroke="var(--color-text-info)" strokeWidth="1.5" fill="none"/><circle cx="10" cy="10" r="2.5" fill="var(--color-text-info)"/></svg>
        </div>
        <div>
          <div style={{ fontSize:18, fontWeight:500 }}>Tempus sales copilot</div>
          <div style={{ fontSize:13, color:"var(--color-text-secondary)" }}>Midwest-1 territory — Mike Torres</div>
        </div>
        <div style={{ marginLeft:"auto", display:"flex", gap:6 }}>
          {["all","active","warm","cold"].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              fontSize:12, padding:"4px 12px", borderRadius:"var(--border-radius-md)",
              background: filter===f ? "var(--color-background-info)" : "transparent",
              color: filter===f ? "var(--color-text-info)" : "var(--color-text-secondary)",
              border: filter===f ? "0.5px solid var(--color-border-info)" : "0.5px solid var(--color-border-tertiary)",
              cursor:"pointer", textTransform:"capitalize"
            }}>{f}</button>
          ))}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns: selected ? "minmax(0,1fr) minmax(0,1.5fr)" : "1fr", gap:16 }}>
        <div>
          <div style={{ fontSize:12, color:"var(--color-text-secondary)", marginBottom:8, fontWeight:500 }}>Priority rankings ({filtered.length} providers)</div>
          <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
            {filtered.map((p, i) => (
              <div key={p.id} onClick={() => handleSelect(p)} style={{
                padding:"10px 12px", borderRadius:"var(--border-radius-md)", cursor:"pointer",
                border: selected?.id===p.id ? "1.5px solid var(--color-border-info)" : "0.5px solid var(--color-border-tertiary)",
                background: selected?.id===p.id ? "var(--color-background-info)" : "var(--color-background-primary)",
                transition:"all 0.15s"
              }}>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ width:24, height:24, borderRadius:"50%", background:"var(--color-background-secondary)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, fontWeight:500, color:"var(--color-text-secondary)", flexShrink:0 }}>{i+1}</div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                      <span style={{ fontSize:14, fontWeight:500, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{p.name}</span>
                      <span style={{ fontSize:10, color:stageColors[p.stage], flexShrink:0 }}>{stageLabels[p.stage]}</span>
                    </div>
                    <div style={{ fontSize:12, color:"var(--color-text-secondary)", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
                      {p.subspecialty} — {p.patients} pts/yr
                    </div>
                  </div>
                  <div style={{ fontSize:13, fontWeight:500, color:"var(--color-text-info)", flexShrink:0 }}>{(p.score*100).toFixed(0)}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:12, padding:10, borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)", fontSize:11, color:"var(--color-text-secondary)" }}>
            Score = 0.30×volume + 0.25×product fit + 0.15×recency + 0.15×objection resolvability + 0.10×sentiment + bonuses
          </div>
        </div>

        {selected && sp && (
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            <div style={{ padding:"14px 16px", borderRadius:"var(--border-radius-lg)", border:"0.5px solid var(--color-border-tertiary)", background:"var(--color-background-primary)" }}>
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:12 }}>
                <div style={{ width:40, height:40, borderRadius:"50%", background:"var(--color-background-info)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:500, fontSize:14, color:"var(--color-text-info)" }}>
                  {selected.name.split(" ").map(n=>n[0]).join("").slice(1)}
                </div>
                <div>
                  <div style={{ fontSize:16, fontWeight:500 }}>{selected.name}</div>
                  <div style={{ fontSize:13, color:"var(--color-text-secondary)" }}>{selected.institution}</div>
                </div>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8, marginBottom:12 }}>
                {[
                  { label:"Patients/yr", value:selected.patients },
                  { label:"Focus", value:selected.subspecialty },
                  { label:"Current vendor", value:selected.currentVendor },
                ].map(m => (
                  <div key={m.label} style={{ padding:"8px 10px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)" }}>
                    <div style={{ fontSize:11, color:"var(--color-text-secondary)" }}>{m.label}</div>
                    <div style={{ fontSize:13, fontWeight:500, marginTop:2 }}>{m.value}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:12, color:"var(--color-text-secondary)", padding:"8px 10px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)", lineHeight:1.5 }}>
                <span style={{ fontWeight:500, color:"var(--color-text-primary)" }}>Why now: </span>{sp.summary}
              </div>
            </div>

            <div style={{ padding:"14px 16px", borderRadius:"var(--border-radius-lg)", border:"0.5px solid var(--color-border-tertiary)", background:"var(--color-background-primary)" }}>
              <div style={{ fontSize:13, fontWeight:500, marginBottom:8 }}>Best-fit product</div>
              <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:8 }}>
                <span style={{ fontSize:12, padding:"3px 10px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-info)", color:"var(--color-text-info)", fontWeight:500 }}>{matchedProduct.primary}</span>
                {matchedProduct.secondary.map(s => (
                  <span key={s} style={{ fontSize:12, padding:"3px 10px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)", color:"var(--color-text-secondary)" }}>{s}</span>
                ))}
              </div>
              <div style={{ fontSize:12, color:"var(--color-text-secondary)", lineHeight:1.5 }}>
                {matchedProduct.reasons[0]}
              </div>
            </div>

            {sp.objections.length > 0 && (
              <div style={{ padding:"14px 16px", borderRadius:"var(--border-radius-lg)", border:"0.5px solid var(--color-border-tertiary)", background:"var(--color-background-primary)" }}>
                <div style={{ fontSize:13, fontWeight:500, marginBottom:10, display:"flex", alignItems:"center", gap:6 }}>
                  <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6" fill="none" stroke="var(--color-text-warning)" strokeWidth="1.2"/><path d="M7 4v3.5M7 9v.5" stroke="var(--color-text-warning)" strokeWidth="1.2" strokeLinecap="round"/></svg>
                  Objection handler
                </div>
                {sp.objections.map((obj, i) => {
                  const handler = matchObjToHandler(obj);
                  return (
                    <div key={i} style={{ marginBottom: i < sp.objections.length-1 ? 12 : 0 }}>
                      <div style={{ fontSize:12, fontWeight:500, color:"var(--color-text-warning)", marginBottom:4 }}>"{obj}"</div>
                      {handler ? (
                        <>
                          <div style={{ fontSize:12, lineHeight:1.6, color:"var(--color-text-primary)", padding:"8px 10px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)", borderLeft:"2px solid var(--color-border-info)" }}>
                            {handler.response}
                          </div>
                          <div style={{ fontSize:10, color:"var(--color-text-secondary)", marginTop:4, fontStyle:"italic" }}>Source: {handler.source}</div>
                        </>
                      ) : (
                        <div style={{ fontSize:12, color:"var(--color-text-secondary)", fontStyle:"italic" }}>No verified data available — recommend consulting Medical Affairs.</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            <div style={{ padding:"14px 16px", borderRadius:"var(--border-radius-lg)", border:"0.5px solid var(--color-border-tertiary)", background:"var(--color-background-primary)" }}>
              <div style={{ fontSize:13, fontWeight:500, marginBottom:8, display:"flex", alignItems:"center", gap:6 }}>
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="2" y="3" width="10" height="8" rx="1.5" fill="none" stroke="var(--color-text-info)" strokeWidth="1.2"/><path d="M2 5.5L7 8.5 12 5.5" fill="none" stroke="var(--color-text-info)" strokeWidth="1.2"/></svg>
                30-second meeting script
              </div>
              {generating ? (
                <div style={{ fontSize:12, color:"var(--color-text-secondary)", padding:"12px 0" }}>Generating personalized script...</div>
              ) : (
                <div style={{ fontSize:13, lineHeight:1.7, color:"var(--color-text-primary)", padding:"10px 12px", borderRadius:"var(--border-radius-md)", background:"var(--color-background-secondary)", fontStyle:"italic" }}>
                  "{generatedScript}"
                </div>
              )}
            </div>

            {sp.interests.length > 0 && (
              <div style={{ padding:"14px 16px", borderRadius:"var(--border-radius-lg)", border:"0.5px solid var(--color-border-tertiary)", background:"var(--color-background-primary)" }}>
                <div style={{ fontSize:13, fontWeight:500, marginBottom:8 }}>Talking points from CRM</div>
                <div style={{ display:"flex", flexDirection:"column", gap:4 }}>
                  {sp.interests.map((interest, i) => (
                    <div key={i} style={{ fontSize:12, color:"var(--color-text-secondary)", display:"flex", gap:6, lineHeight:1.5 }}>
                      <span style={{ color:"var(--color-text-info)", flexShrink:0 }}>+</span>
                      {interest}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!selected && (
          <div style={{ display:"flex", alignItems:"center", justifyContent:"center", padding:"3rem", color:"var(--color-text-secondary)", fontSize:14 }}>
            Select a provider to view their briefing
          </div>
        )}
      </div>
    </div>
  );
}
