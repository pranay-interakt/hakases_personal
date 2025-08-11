# modules/extractor.py
import re, json
from typing import List, Dict
from .llm import LLMBase

def _fallback_generate(llm: LLMBase, prompt: str) -> str:
    # Works with either generate()/chat()/ask()
    if hasattr(llm, "generate"):
        return llm.generate(prompt)
    if hasattr(llm, "chat"):
        return llm.chat(prompt)
    if hasattr(llm, "ask"):
        return llm.ask(prompt)
    raise AttributeError(f"LLM {type(llm).__name__} has no generate/chat/ask")

def ask_with_grounding(llm: LLMBase, question: str, contexts: List[str], strict: bool = True) -> str:
    rules = (
        "You are a CRO protocol analyst. Use only the provided sources. "
        "If a detail is missing, say 'Unknown' and list what would be needed. "
        "Cite Source[index] inline like [Prot:index]."
    )
    ctx = "\n\n---\n".join([f"Source[{i}]:\n{c}" for i, c in enumerate(contexts)])
    prompt = f"""{rules}

QUESTION:
{question}

SOURCES:
{ctx}

INSTRUCTIONS:
- No fabrication.
- Use short inline citations like [Prot:0], [Prot:3].
- Return strict JSON with keys: condition, intervention, aliases (array).

ANSWER:"""
    return _fallback_generate(llm, prompt)

def clean_term(term: str) -> str:
    if not term:
        return term
    term = re.sub(r"\([^)]*\)", "", term)           # remove parentheticals
    term = re.split(r"[/,;]", term)[0]              # first segment
    term = re.sub(r"\s+", " ", term).strip()
    term = re.sub(r"^[\-\)\]\. ]+|[\-\)\]\. ]+$", "", term)  # trim stray punct
    return term

def extract_trial_entities(llm: LLMBase, chunks: List[dict], strict: bool = True) -> Dict[str, str]:
    keys = ["indication","disease","condition","intervention","investigational product","drug","therapy","biologic","device"]
    candidates = [c for c in chunks if any(k in c["text"].lower() for k in keys)]
    contexts = [c["text"][:3000] for c in candidates[:20]]

    q = ("Extract the clinical CONDITION/INDICATION and INTERVENTION (drug/device/biologic/procedure) named in the protocol. "
         "Return strict JSON: {\"condition\": str, \"intervention\": str, \"aliases\": [str,...]}. Use 'Unknown' if not specified.")
    raw = ask_with_grounding(llm, q, contexts, strict=strict)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    base = {"condition":"Unknown","intervention":"Unknown","aliases":[],"condition_clean":"Unknown","intervention_clean":"Unknown"}
    if not m:
        return base
    try:
        data = json.loads(m.group(0))
    except Exception:
        return base

    if isinstance(data.get("aliases"), str): data["aliases"] = [data["aliases"]]
    data.setdefault("aliases", [])
    data["condition"] = (data.get("condition") or "Unknown").strip()
    data["intervention"] = (data.get("intervention") or "Unknown").strip()
    data["condition_clean"] = clean_term(data["condition"])
    data["intervention_clean"] = clean_term(data["intervention"])
    return data
