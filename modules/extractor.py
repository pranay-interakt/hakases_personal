import re, json
from .llm import LLMBase
def _fallback_generate(llm: LLMBase, prompt: str) -> str:
    return getattr(llm, "generate")(prompt)
def ask_with_grounding(llm, question, contexts, strict=True):
    ctx = "\n\n---\n".join([f"Source[{i}]:\n{c}" for i,c in enumerate(contexts)])
    prompt = f"""Use only provided sources. Cite [Prot:i].
QUESTION:
{question}
SOURCES:
{ctx}
Return strict JSON with keys: condition, intervention, aliases (array)."""
    return _fallback_generate(llm, prompt)
def clean_term(term: str) -> str:
    term = re.sub(r"\([^)]*\)", "", term or "")
    term = re.split(r"[/,;]", term)[0]
    term = re.sub(r"\s+", " ", term).strip()
    term = re.sub(r"^[\-\)\]\. ]+|[\-\)\]\. ]+$", "", term)
    return term
def extract_trial_entities(llm, chunks, strict=True):
    keys = ["indication","disease","condition","intervention","drug","device","biologic","therapy"]
    candidates = [c for c in chunks if any(k in c["text"].lower() for k in keys)]
    contexts = [c["text"][:3000] for c in candidates[:20]] or [chunks[0]["text"][:3000]]
    q = "Extract CONDITION/INDICATION and INTERVENTION. Return JSON: {\"condition\": str, \"intervention\": str, \"aliases\": [str]}."
    raw = ask_with_grounding(llm, q, contexts, strict=strict)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    base = {"condition":"Unknown","intervention":"Unknown","aliases":[],"condition_clean":"Unknown","intervention_clean":"Unknown"}
    if not m: return base
    try: data = json.loads(m.group(0))
    except Exception: return base
    if isinstance(data.get("aliases"), str): data["aliases"] = [data["aliases"]]
    data.setdefault("aliases", [])
    data["condition"] = (data.get("condition") or "Unknown").strip()
    data["intervention"] = (data.get("intervention") or "Unknown").strip()
    data["condition_clean"] = clean_term(data["condition"])
    data["intervention_clean"] = clean_term(data["intervention"])
    return data
