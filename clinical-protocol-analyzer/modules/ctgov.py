from __future__ import annotations
from typing import Dict, Any, List
import requests, json
from tenacity import retry, stop_after_attempt, wait_fixed

API = "https://clinicaltrials.gov/api/v2/studies"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def query_studies(condition: str, intervention: str, limit: int = 100, timeout: int = 30) -> Dict[str, Any]:
    params = {
        "format": "json",
        "query.cond": condition,
        "query.intr": intervention,
        "pageSize": min(100, limit),
    }
    r = requests.get(API, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

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
