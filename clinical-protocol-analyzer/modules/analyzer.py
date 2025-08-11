# modules/analyzer.py
from __future__ import annotations
from typing import List, Dict, Any
import re, json
from .llm import ask_with_grounding, LLMBase

def _mk_context(protocol_chunks: List[dict], k: int) -> List[str]:
    # Prefer chunks with CRO-relevant keywords
    kw = [
        "inclusion", "exclusion", "eligibility", "endpoint", "visit",
        "schedule", "site selection", "feasibility", "recruit", "enrollment",
        "budget", "cost", "monitoring", "SDV", "decentralized", "logistics",
        "randomization", "statistical", "adverse event", "compliance",
        "protocol deviation", "database lock"
    ]
    preferred = [c for c in protocol_chunks if any(w in c["text"].lower() for w in kw)]
    if not preferred:
        preferred = protocol_chunks
    return [c["text"][:3000] for c in preferred[:k]]

def _mk_ctgov_context(ctgov_items: List[Dict[str, Any]], maxn: int = 30) -> str:
    lines = []
    for it in ctgov_items[:maxn]:
        tag = it.get("nctId")
        title = it.get("briefTitle")
        status = it.get("overallStatus")
        phase = it.get("phases")
        lines.append(f"[CTGov {tag}] {title} | status={status} | phase={phase}")
    return "\n".join(lines)

def cro_analyze(
    llm: LLMBase,
    protocol_chunks: List[dict],
    mcp_blob: str,
    ctgov_items: List[Dict[str, Any]],
    k: int = 20,
    strict: bool = True
) -> str:
    """
    Produces a deep, CRO-grade, fully-narrative analysis with:
    - Forecasts
    - Optimizations
    - Risk mitigation
    - Cost & operational levers
    - Final integrated summary
    """
    prot_ctx = _mk_context(protocol_chunks, k)
    ct_ctx = _mk_ctgov_context(ctgov_items)

    question = f"""
Produce a CRO-grade, detailed, *narrative* analysis for the uploaded protocol with the following sections.
Each section must be at least one substantial paragraph, with a side heading and explicit citations.
Include concrete numbers, benchmarks, and operational reasoning.

Sections to produce:

## Enrollment Forecast
Quantify total sites, startup lag, enrollment rate per site per month, screen failure rate, and months to full enrollment.
Cite [BiMCP] for rates/regions and [CTGov NCTxxxxxx] for precedent; cite [Prot:idx] for protocol constraints.
Include sensitivity analysis showing best-case, base-case, and worst-case scenarios.

## Enrollment Optimizations
Specific, actionable inclusion/exclusion or operational adjustments.
For each: describe the change, the rationale, expected impact (quantified if possible), operational tradeoffs, and potential regulatory impact.
Cite [Prot], [BiMCP], [CTGov].

## Timeline
Detailed milestone forecast: FPI, 25%/50%/LPI, DB Lock, CSR.
Include operational assumptions and dependencies.
Contrast with historical benchmarks from [BiMCP]/[CTGov].

## Cost Effectiveness
Concrete cost levers: monitoring cadence, remote SDV, central labs, ePRO, DCT visits, courier/logistics, IWRS/EDC config.
Estimate savings ranges, implementation complexity, and caveats.
Cite [Prot] and external precedents [BiMCP]/[CTGov].

## Site Selection & Facilities
Recommend optimal regions and site profiles with expected enrollment rate and rationale.
Address regulatory timelines, patient pool, and competitive trial landscape.
Cite [BiMCP] and [CTGov].

## Risk Mitigation
Identify major operational and regulatory risks and propose mitigations.
Include risk likelihood, impact score, and residual risk post-mitigation.

## Final Integrated Analysis
Synthesize findings across all sections into a strategic recommendation for the sponsor.
Summarize feasibility, efficiency, and projected probability of meeting primary endpoints on time and budget.

If any data is missing, do NOT leave a section empty; instead:
- Write the paragraph and state exactly which data fields are missing to finalize the estimate.

Use these inputs in addition to the protocol excerpts:
- BiMCP output (may include prior trials/sites/rates):
[MCP]
{mcp_blob[:7000]}

- ClinicalTrials.gov precedents (abbrev listing):
{ct_ctx}

Format strictly in Markdown with H2 headings per section and inline citations like [BiMCP], [CTGov NCT05938036], [Prot:0].
Avoid bullet-only lists; write full paragraphs with specific numbers when possible.
"""
    return ask_with_grounding(llm, question, prot_ctx, strict=strict)
