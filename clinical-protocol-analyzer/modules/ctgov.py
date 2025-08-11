# modules/ctgov.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import requests
from urllib.parse import quote_plus
from tenacity import retry, stop_after_attempt, wait_fixed
import re

API = "https://clinicaltrials.gov/api/v2/studies"

def _unique(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x and x not in seen:
            out.append(x); seen.add(x)
    return out

def _variants_from_entities(entities: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    cond = entities.get("condition","") or ""
    cond_clean = entities.get("condition_clean","") or cond
    aliases = entities.get("aliases", []) or []
    abbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", cond)
    conds = _unique([cond_clean] + abbrs + aliases + ([cond] if cond != cond_clean else []))

    intr = entities.get("intervention","") or ""
    intr_clean = entities.get("intervention_clean","") or intr
    iabbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", intr)
    intrs = _unique([intr_clean] + iabbrs + ([intr] if intr != intr_clean else []))
    return conds, intrs

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _query_once(condition: str, intervention: str, limit: int = 100, timeout: int = 30) -> Dict[str, Any]:
    params = {
        "format": "json",
        "query.cond": condition,
        "query.intr": intervention,
        "pageSize": min(100, limit),
    }
    r = requests.get(API, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def query_studies_variants(entities: Dict[str, Any], limit: int = 100, timeout: int = 30, max_pairs: int = 6) -> List[Dict[str, Any]]:
    conds, intrs = _variants_from_entities(entities)
    out, n = [], 0
    for c in conds:
        for i in intrs:
            if n >= max_pairs: break
            try:
                out.append(_query_once(c, i, limit=limit, timeout=timeout))
            except Exception:
                pass
            n += 1
        if n >= max_pairs: break
    return out

def simplify_ctgov(json_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    studies = json_obj.get("studies", [])
    simplified = []
    for s in studies:
        ps = s.get("protocolSection", {})
        ident = ps.get("identificationModule", {})
        status = ps.get("statusModule", {})
        design = ps.get("designModule", {})
        conds = ps.get("conditionsModule", {})
        arms = ps.get("armsInterventionsModule", {})
        simplified.append({
            "nctId": ident.get("nctId"),
            "briefTitle": ident.get("briefTitle"),
            "overallStatus": status.get("overallStatus"),
            "startDate": (status.get("startDateStruct") or {}).get("date"),
            "completionDate": (status.get("completionDateStruct") or {}).get("date"),
            "studyType": design.get("studyType"),
            "phases": design.get("phases"),
            "conditions": conds.get("conditions"),
            "interventions": arms.get("interventions"),
        })
    return simplified
