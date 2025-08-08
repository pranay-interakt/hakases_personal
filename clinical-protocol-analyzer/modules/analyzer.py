from __future__ import annotations
from typing import List, Dict, Any
import re, json
from .llm import ask_with_grounding, LLMBase

def _json_from_text(text: str, fallback: dict) -> dict:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return fallback
    try:
        return json.loads(m.group(0))
    except Exception:
        return fallback

def cro_analysis(llm: LLMBase, protocol_chunks: List[dict], mcp_blob: str, ctgov_items: List[Dict[str, Any]], k: int = 20, strict: bool = True) -> Dict[str, Any]:
    # Pick relevant protocol chunks
    keywords = ["inclusion", "exclusion", "eligibility", "endpoint", "visit", "site selection", "feasibility", "timeline", "schedule", "recruit", "enrollment", "budget", "cost"]
    preferred = [c for c in protocol_chunks if any(w in c["text"].lower() for w in keywords)]
    contexts = [c["text"][:3000] for c in (preferred[:k] if preferred else protocol_chunks[:k])]

    ct_brief = []
    for it in ctgov_items[:30]:
        ct_brief.append(f"NCT {it.get('nctId')}: {it.get('briefTitle')} | status={it.get('overallStatus')} | phase={it.get('phases')}")
    ct_context = "CTGOV_MATCHES:\n" + "\n".join(ct_brief)

    # Enrollment forecast
    q1 = (
        "Using SOURCES (protocol excerpts) + MCP_OUTPUT + CTGOV_MATCHES, produce a structured enrollment forecast. "
        "Return JSON keys: total_sites, startup_lag_weeks, avg_enrollment_rate_pm, screen_fail_rate, "
        "projected_months_to_full_enrollment, regional_split (object region->site_count), assumptions (array), risks (array).\n\n"
        f"MCP_OUTPUT:\n{mcp_blob[:8000]}\n\n{ct_context}"
    )
    r1 = ask_with_grounding(llm, q1, contexts, strict=strict)
    forecast = _json_from_text(r1, fallback={})

    # Optimizations
    q2 = (
        "Based on inclusion/exclusion and operational constraints, list concrete adjustments to improve recruitment "
        "without compromising data integrity. Return JSON 'recommendations': [ {change, rationale, expected_impact, risk} ]."
    )
    r2 = ask_with_grounding(llm, q2, contexts, strict=strict)
    optim = _json_from_text(r2, fallback={})

    # Timeline
    q3 = (
        "Draft a realistic study timeline with milestones: First Site Activated, 25% Enrolled, 50% Enrolled, Last Patient In, "
        "Database Lock, CSR. Return JSON 'timeline': [ {milestone, eta_weeks_from_now, assumptions} ]."
    )
    r3 = ask_with_grounding(llm, q3, contexts, strict=strict)
    timeline = _json_from_text(r3, fallback={})

    # Cost effectiveness
    q4 = (
        "Identify cost-saving opportunities (monitoring frequency, central vs local labs, ePRO, remote SDV, "
        "decentralized visits, site bundle rates, courier/logistics, IWRS/EDC config). Return JSON 'savings': [ {area, change, est_saving_pct, caveats} ]."
    )
    r4 = ask_with_grounding(llm, q4, contexts, strict=strict)
    cost = _json_from_text(r4, fallback={})

    # Site recommendations
    q5 = (
        "From MCP_OUTPUT and CTGOV_MATCHES, infer top-performing site profiles and regions for this indication/intervention. "
        "Return JSON 'sites': [ {site_name_or_profile, region, rationale, expected_rate_pm} ].\n\n"
        f"MCP_OUTPUT:\n{mcp_blob[:6000]}\n\n{ct_context}"
    )
    r5 = ask_with_grounding(llm, q5, contexts, strict=strict)
    sites = _json_from_text(r5, fallback={})

    return {
        "forecast": forecast,
        "optimizations": optim,
        "timeline": timeline,
        "cost": cost,
        "sites": sites,
        "ctgov_count": len(ctgov_items),
    }
