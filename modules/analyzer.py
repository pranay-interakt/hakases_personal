from .advanced_analyzer import SECTIONS
from .reranker import rerank_sections
def _ctgov_listing(ctgov_items):
    lines = []
    for it in ctgov_items:
        tag = it.get("nctId") or "NCT???????"; title = it.get("briefTitle") or "Untitled"
        status = it.get("overallStatus") or "Unknown"; phase = it.get("phases") or "NA"
        lines.append(f"[CTGov {tag}] {title} | status={status} | phase={phase}")
    return "\n".join(lines)
def cro_analysis_longform(llm, protocol_chunks, mcp_blob, ctgov_top10, pubmed_top10, k=24):
    ctlist = _ctgov_listing(ctgov_top10)
    raw_sections = []
    for spec in SECTIONS:
        body = spec["fn"](llm, protocol_chunks, mcp_blob, ctlist)
        raw_sections.append({"title": spec["title"], "body": body})
    ranked = rerank_sections(raw_sections, {})
    lines = ["# CRO Optimization Analysis (Grounded to BioMCP, CTGov, PubMed)\n"]
    for sec in ranked:
        lines.append(f"## {sec['title']}  \n")
        lines.append(f"*Confidence:* **{sec['confidence']}** / 100  |  *Success likelihood (est.):* **{sec['success_pct']}%**\n")
        lines.append(sec["body"].strip() + "\n")
    return "\n".join(lines)
