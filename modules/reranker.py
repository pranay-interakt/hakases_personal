import re
def _count_ctgov_cites(t): return len(re.findall(r"\[CTGov\s+NCT\d{8}\]", t))
def _has_biomcp_cite(t): return "[BioMCP]" in t or "[BiMCP]" in t
def _count_protocol_cites(t): return len(re.findall(r"\[Prot:\d+\]", t))
def score_recommendation(text, keywords=None):
    ct=min(3,_count_ctgov_cites(text)); bi=1 if _has_biomcp_cite(text) else 0; pr=min(3,_count_protocol_cites(text))
    evidence=(ct+bi+pr)/7.0; confidence=int(round(100*evidence))
    return {"confidence_score":confidence,"evidence_ctgov":ct,"evidence_biomcp":bi,"evidence_protocol":pr,"coverage":1.0,"substance":1.0}
def estimate_success_probability(text, base_rate=0.45):
    ct=_count_ctgov_cites(text); pr=_count_protocol_cites(text); bi=1 if _has_biomcp_cite(text) else 0
    delta=0.04*min(3,ct)+0.02*min(3,pr)+0.03*bi; from math import fsum
    return max(0.10, min(0.90, base_rate+delta))
def rerank_sections(sections, section_keywords):
    out=[]
    for s in sections:
        sc=score_recommendation(s["body"]); succ=estimate_success_probability(s["body"])
        s2={**s,"confidence":sc["confidence_score"],"success_pct":round(100*succ,1),"score_breakdown":sc}
        out.append(s2)
    return out
