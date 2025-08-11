# modules/advanced_analyzer.py
from __future__ import annotations
from typing import List, Dict, Any, Callable
from .llm import LLMBase
import re

def _fallback_generate(llm: LLMBase, prompt: str) -> str:
    if hasattr(llm, "generate"): return llm.generate(prompt)
    if hasattr(llm, "chat"): return llm.chat(prompt)
    if hasattr(llm, "ask"): return llm.ask(prompt)
    raise AttributeError(f"LLM {type(llm).__name__} missing generate/chat/ask")

def _ctx(protocol_chunks: List[dict], k: int) -> List[str]:
    # prefer CRO-critical sections
    kw = ["inclusion","exclusion","eligibility","endpoint","visit","schedule","site selection","feasibility","recruit","enrollment","budget","cost","monitoring","SDV","decentralized","randomization","statistics","power","sample size","drug supply","safety","DSMB","pharmacovigilance","logistics","labs","ePRO","eCOA","IWRS","EDC","diversity","regulatory"]
    pref = [c for c in protocol_chunks if any(w in c["text"].lower() for w in kw)]
    if not pref: pref = protocol_chunks
    return [c["text"][:3000] for c in pref[:k]]

def _force_long_paragraph(llm: LLMBase, title: str, ask: str, mcp_blob: str, ctgov_listing: str, prot_ctx: List[str]) -> str:
    """
    Single long paragraph, 200–400 words minimum, explicit citations.
    """
    guidance = f"""
Write a CRO-grade, detailed paragraph for **{title}** (minimum ~250 words).
Requirements:
- Base all claims on the provided sources. Use inline citations: [BiMCP] for BiMCP, [CTGov NCTxxxxxx] for registry trials, [Prot:i] for protocol excerpts.
- Include concrete numbers when present (rates/site/month, screen fail %, timelines, cost deltas).
- If evidence is missing, state exactly what is missing (e.g., 'Unknown: historical rate/region for ...').
- Close with a succinct recommendation sentence.

BiMCP OUTPUT (excerpts):
{mcp_blob[:7000]}

CTGOV PRECEDENTS (abbrev listing):
{ctgov_listing}

Now, use these protocol excerpts as primary grounding:
""" + "\n\n---\n".join([f"Source[{i}]:\n{t}" for i,t in enumerate(prot_ctx)])

    prompt = f"""{guidance}

Task:
{ask}

Format:
- Single paragraph (no bullets). 
- 6–10 sentences minimum. 
- Dense with specifics and citations.

Answer:"""
    return _fallback_generate(llm, prompt)

# ---------- Section Generators (25+) ----------
def sec_enrollment_forecast(llm, prot, mcp_blob, ctlist): 
    ask = ("Quantify total sites, startup lag, enrollment rate/site/month, screen fail %, and months to full enrollment; "
           "justify using BiMCP and CTGov precedents; cite protocol constraints that influence rates.")
    return _force_long_paragraph(llm, "Enrollment Forecast", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_enrollment_optimizations(llm, prot, mcp_blob, ctlist):
    ask = ("Provide operational and I/E adjustments that increase accrual without compromising integrity; "
           "include pre-screening flows, referral networks, lab threshold tweaks, and digital outreach; quantify expected uplift.")
    return _force_long_paragraph(llm, "Enrollment Optimizations", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_inclusion_exclusion_mods(llm, prot, mcp_blob, ctlist):
    ask = ("Recommend precise inclusion/exclusion edits linked to feasibility drivers; quantify likely accrual impact and safety tradeoffs.")
    return _force_long_paragraph(llm, "Inclusion/Exclusion Modifications", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_screen_fail_reduction(llm, prot, mcp_blob, ctlist):
    ask = ("Propose measures to reduce screen failure (central adjudication, run-in, lab re-tests) and estimate impact on randomization yield.")
    return _force_long_paragraph(llm, "Screen Failure Reduction", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_pre_screening_pipeline(llm, prot, mcp_blob, ctlist):
    ask = ("Design a central pre-screening pipeline with inclusion logic, ePRO capture, and referral handling; estimate throughput and hit rate.")
    return _force_long_paragraph(llm, "Central Pre‑Screening Pipeline", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_site_selection(llm, prot, mcp_blob, ctlist):
    ask = ("Recommend site profiles/regions based on historic performance; propose initial allocation by region and ramp curve.")
    return _force_long_paragraph(llm, "Site Selection & Regional Mix", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_startup_timeline(llm, prot, mcp_blob, ctlist):
    ask = ("Lay out realistic milestones (FPI, 25%/50%, LPI, DB lock, CSR) with assumptions and gating risks; map to operational levers.")
    return _force_long_paragraph(llm, "Startup & Timeline", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_monitoring_strategy(llm, prot, mcp_blob, ctlist):
    ask = ("Define on-site vs remote monitoring cadence with rationale and risk controls; include SDV strategy and cost impact.")
    return _force_long_paragraph(llm, "Monitoring & SDV Strategy", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_central_labs(llm, prot, mcp_blob, ctlist):
    ask = ("Recommend central vs local labs, logistics/turnaround, reflex testing; quantify quality and cost effects.")
    return _force_long_paragraph(llm, "Central Labs & Diagnostics", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_epro_ecoa(llm, prot, mcp_blob, ctlist):
    ask = ("Propose ePRO/eCOA plan including instrument schedule, reminders, compliance analytics; estimate data completeness gains.")
    return _force_long_paragraph(llm, "ePRO/eCOA Plan", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_dct_visits(llm, prot, mcp_blob, ctlist):
    ask = ("Define decentralized options (home nursing, tele-visits, mobile phlebotomy) and impact on retention/enrollment.")
    return _force_long_paragraph(llm, "Decentralized Visits (DCT)", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_iwrs_edc(llm, prot, mcp_blob, ctlist):
    ask = ("Optimize IWRS/EDC config (randomization blocks, kit buffers, edit checks) to reduce errors/stockouts/delays.")
    return _force_long_paragraph(llm, "IWRS/EDC Configuration", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_logistics_courier(llm, prot, mcp_blob, ctlist):
    ask = ("Plan courier/temperature lanes and weekend coverage to prevent visit cancellations; quantify avoided deviations.")
    return _force_long_paragraph(llm, "Logistics & Courier Strategy", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_drug_supply(llm, prot, mcp_blob, ctlist):
    ask = ("Design drug supply strategy (buffers, expiry, resupply rules) linked to ramp; compute risk to last-patient-in.")
    return _force_long_paragraph(llm, "Drug Supply & Resupply", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_safety_monitoring(llm, prot, mcp_blob, ctlist):
    ask = ("Detail safety monitoring schedule, lab triggers, SAE/AE flows; align with similar trials’ event rates.")
    return _force_long_paragraph(llm, "Safety Monitoring", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_dsmb_plan(llm, prot, mcp_blob, ctlist):
    ask = ("Define DSMB cadence, stopping boundaries, unblinding safeguards; align with precedent trials.")
    return _force_long_paragraph(llm, "DSMB Plan", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_risk_mitigation(llm, prot, mcp_blob, ctlist):
    ask = ("Enumerate top operational/statistical risks with mitigations tied to evidence; include backup vendors/sites.")
    return _force_long_paragraph(llm, "Risk Register & Mitigations", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_protocol_simplification(llm, prot, mcp_blob, ctlist):
    ask = ("Propose ways to simplify visits/procedures/forms while preserving endpoints; quantify staff time saved.")
    return _force_long_paragraph(llm, "Protocol Simplification", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_visit_schedule_opt(llm, prot, mcp_blob, ctlist):
    ask = ("Optimize visit windows/scheduling to reduce cancellations and burden; estimate retention improvement.")
    return _force_long_paragraph(llm, "Visit Schedule Optimization", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_endpoint_clarity(llm, prot, mcp_blob, ctlist):
    ask = ("Clarify endpoints/assessments to minimize ambiguity and deviations; cross-check with precedent measures.")
    return _force_long_paragraph(llm, "Endpoint Clarity", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_stat_power(llm, prot, mcp_blob, ctlist):
    ask = ("Discuss power assumptions based on historical variability and event rates; recommend adjustments.")
    return _force_long_paragraph(llm, "Statistical Power Assumptions", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_sample_size_recalc(llm, prot, mcp_blob, ctlist):
    ask = ("Outline blinded sample-size re-estimation options and triggers; align with precedent feasibility.")
    return _force_long_paragraph(llm, "Sample Size Re‑Estimation", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_rescue_sites(llm, prot, mcp_blob, ctlist):
    ask = ("Plan rescue sites activation criteria and rapid start-up playbook; estimate time saved to LPI.")
    return _force_long_paragraph(llm, "Rescue Sites Plan", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_kol_engagement(llm, prot, mcp_blob, ctlist):
    ask = ("Propose KOL engagement and steering to boost screening/referrals and protocol adherence.")
    return _force_long_paragraph(llm, "KOL Engagement", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_patient_advocacy(llm, prot, mcp_blob, ctlist):
    ask = ("Engage patient orgs for referral and retention; define materials and HIPAA-safe flows.")
    return _force_long_paragraph(llm, "Patient Advocacy & Outreach", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_diversity_inclusion(llm, prot, mcp_blob, ctlist):
    ask = ("Diversity plan with region/site tactics, community partners, and metrics; tie to similar trials’ demographics.")
    return _force_long_paragraph(llm, "Diversity & Inclusion Strategy", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_feasibility_budget(llm, prot, mcp_blob, ctlist):
    ask = ("Budget levers (bundled rates, pass-throughs), milestone-based payments; quantify % savings.")
    return _force_long_paragraph(llm, "Feasibility & Budgeting", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_contracting_startup(llm, prot, mcp_blob, ctlist):
    ask = ("Accelerate startup via parallel submissions, template CDAs/CTAs, safety letters; estimate weeks saved.")
    return _force_long_paragraph(llm, "Contracting & Start‑up Acceleration", ask, mcp_blob, ctlist, _ctx(prot, 20))

def sec_regulatory_strategy(llm, prot, mcp_blob, ctlist):
    ask = ("Regulatory engagement plan (scientific advice/pre-IND/type C), alignment with prior approvals; risk/benefit.")
    return _force_long_paragraph(llm, "Regulatory Strategy", ask, mcp_blob, ctlist, _ctx(prot, 20))

# registry of functions so you can add/remove easily
SECTIONS: List[Dict[str, Any]] = [
    {"title":"Enrollment Forecast", "fn": sec_enrollment_forecast},
    {"title":"Enrollment Optimizations", "fn": sec_enrollment_optimizations},
    {"title":"Inclusion/Exclusion Modifications", "fn": sec_inclusion_exclusion_mods},
    {"title":"Screen Failure Reduction", "fn": sec_screen_fail_reduction},
    {"title":"Central Pre‑Screening Pipeline", "fn": sec_pre_screening_pipeline},
    {"title":"Site Selection & Regional Mix", "fn": sec_site_selection},
    {"title":"Startup & Timeline", "fn": sec_startup_timeline},
    {"title":"Monitoring & SDV Strategy", "fn": sec_monitoring_strategy},
    {"title":"Central Labs & Diagnostics", "fn": sec_central_labs},
    {"title":"ePRO/eCOA Plan", "fn": sec_epro_ecoa},
    {"title":"Decentralized Visits (DCT)", "fn": sec_dct_visits},
    {"title":"IWRS/EDC Configuration", "fn": sec_iwrs_edc},
    {"title":"Logistics & Courier Strategy", "fn": sec_logistics_courier},
    {"title":"Drug Supply & Resupply", "fn": sec_drug_supply},
    {"title":"Safety Monitoring", "fn": sec_safety_monitoring},
    {"title":"DSMB Plan", "fn": sec_dsmb_plan},
    {"title":"Risk Register & Mitigations", "fn": sec_risk_mitigation},
    {"title":"Protocol Simplification", "fn": sec_protocol_simplification},
    {"title":"Visit Schedule Optimization", "fn": sec_visit_schedule_opt},
    {"title":"Endpoint Clarity", "fn": sec_endpoint_clarity},
    {"title":"Statistical Power Assumptions", "fn": sec_stat_power},
    {"title":"Sample Size Re‑Estimation", "fn": sec_sample_size_recalc},
    {"title":"Rescue Sites Plan", "fn": sec_rescue_sites},
    {"title":"KOL Engagement", "fn": sec_kol_engagement},
    {"title":"Patient Advocacy & Outreach", "fn": sec_patient_advocacy},
    {"title":"Diversity & Inclusion Strategy", "fn": sec_diversity_inclusion},
    {"title":"Feasibility & Budgeting", "fn": sec_feasibility_budget},
    {"title":"Contracting & Start‑up Acceleration", "fn": sec_contracting_startup},
    {"title":"Regulatory Strategy", "fn": sec_regulatory_strategy},
]
