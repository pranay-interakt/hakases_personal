from .llm import LLMBase
def _fallback_generate(llm: LLMBase, prompt: str) -> str:
    return getattr(llm, "generate")(prompt)
def _ctx(protocol_chunks, k=20):
    pref = protocol_chunks[:k]
    return [c["text"][:3000] for c in pref]
def _force_long_paragraph(llm, title, ask, mcp_blob, ctlist, prot_ctx):
    guidance = f"""Write a CRO-grade paragraph for **{title}** (min 200 words).
Ground in: [BioMCP], [CTGov NCTxxxxxx], [Prot:i]. Provide numbers when available.
BioMCP:
{mcp_blob[:4000]}
CTGov:
{ctlist}
PROTOCOL EXCERPTS:
""" + "\n\n---\n".join([f"Source[{i}]:\n{t}" for i,t in enumerate(prot_ctx)])
    prompt = guidance + f"""
Task: {ask}
Format: single long paragraph with inline citations.
Answer:"""
    return _fallback_generate(llm, prompt)
def sec_enrollment_forecast(llm, prot, mcp_blob, ctlist):
    return _force_long_paragraph(llm, "Enrollment Forecast", "Quantify sites, rates, screens, months to FPI/LPI.", mcp_blob, ctlist, _ctx(prot))
SECTIONS = [{"title":"Enrollment Forecast","fn":sec_enrollment_forecast}]
