from tenacity import retry, stop_after_attempt, wait_fixed
import requests, re
API = "https://clinicaltrials.gov/api/v2/studies"
def _unique(items):
    out=[]; seen=set()
    for x in items:
        if x and x not in seen: out.append(x); seen.add(x)
    return out
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _query_once(condition, intervention, limit=100, timeout=30):
    params = {"format":"json","query.cond":condition,"query.intr":intervention,"pageSize":min(100,limit)}
    r = requests.get(API, params=params, timeout=timeout); r.raise_for_status(); return r.json()
def query_studies_variants(entities, limit=100, timeout=30, max_pairs=6):
    cond = entities.get("condition",""); cle = entities.get("condition_clean", cond)
    intr = entities.get("intervention",""); ile = entities.get("intervention_clean", intr)
    conds = _unique([cle, cond])
    intrs = _unique([ile, intr])
    out=[]; n=0
    for c in conds:
        for i in intrs:
            if n>=max_pairs: break
            try: out.append(_query_once(c, i, limit=limit, timeout=timeout))
            except Exception: pass
            n+=1
        if n>=max_pairs: break
    return out
def simplify_ctgov(js):
    studies = js.get("studies", []); res=[]
    for s in studies:
        ps = s.get("protocolSection", {}); ident = ps.get("identificationModule", {})
        status = ps.get("statusModule", {}); design = ps.get("designModule", {})
        conds = ps.get("conditionsModule", {}); arms = ps.get("armsInterventionsModule", {})
        res.append({"nctId": ident.get("nctId"), "briefTitle": ident.get("briefTitle"),
                    "overallStatus": status.get("overallStatus"),
                    "startDate": (status.get("startDateStruct") or {}).get("date"),
                    "completionDate": (status.get("completionDateStruct") or {}).get("date"),
                    "studyType": design.get("studyType"),
                    "phases": design.get("phases"),
                    "conditions": conds.get("conditions"),
                    "interventions": arms.get("interventions")})
    return res
