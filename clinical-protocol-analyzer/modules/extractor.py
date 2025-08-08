from __future__ import annotations
from typing import Dict, List
import re, json
from .llm import ask_with_grounding, LLMBase

def extract_trial_entities(llm: LLMBase, chunks: List[dict], strict: bool = True) -> Dict[str, str]:
    keys = ["indication", "disease", "condition", "intervention", "investigational product", "drug", "therapy", "biologic", "device"]
    candidates = [c for c in chunks if any(k in c["text"].lower() for k in keys)]
    contexts = [c["text"][:3000] for c in candidates[:20]]
    q = ("Extract the clinical CONDITION/INDICATION and INTERVENTION (drug/device/biologic/procedure) named in the protocol. "
         "Return strict JSON with keys: condition (string), intervention (string), aliases (array of strings for condition synonyms/abbreviations). "
         "Use 'Unknown' if not specified.")
    raw = ask_with_grounding(llm, q, contexts, strict=strict)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if not m:
        return {"condition": "Unknown", "intervention": "Unknown", "aliases": []}
    try:
        data = json.loads(m.group(0))
    except Exception:
        return {"condition": "Unknown", "intervention": "Unknown", "aliases": []}
    data.setdefault("aliases", [])
    if isinstance(data.get("aliases"), str):
        data["aliases"] = [data["aliases"]]
    for k in ["condition", "intervention"]:
        v = data.get(k, "") or "Unknown"
        data[k] = v.strip()
    return data
