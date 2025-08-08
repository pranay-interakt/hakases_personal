from __future__ import annotations
from typing import Optional, Dict, Any, List

class LLMBase:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class OllamaLLM(LLMBase):
    def __init__(self, model: str, options: Optional[Dict[str, Any]] = None):
        from ollama import Client
        self.client = Client()
        self.model = model
        self.options = options or {}

    def generate(self, prompt: str) -> str:
        resp = self.client.generate(model=self.model, prompt=prompt, options=self.options)
        return resp.get("response", "")

class LlamaCppLLM(LLMBase):
    def __init__(self, model_path: str, n_ctx: int = 8192, n_threads: int = 8, temperature: float = 0.1, top_p: float = 0.9):
        from llama_cpp import Llama
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
        self.temperature = float(temperature)
        self.top_p = float(top_p)

    def generate(self, prompt: str) -> str:
        out = self.llm.create_completion(
            prompt=prompt,
            max_tokens=1536,
            temperature=self.temperature,
            top_p=self.top_p,
            stop=["</s>", "\n\n"]
        )
        return out["choices"][0]["text"] if out.get("choices") else ""

def build_llm(cfg: dict) -> LLMBase:
    backend = cfg["llm"]["backend"]
    if backend == "ollama":
        model = cfg["llm"]["ollama"]["model"]
        options = cfg["llm"]["ollama"].get("options", {})
        return OllamaLLM(model=model, options=options)
    elif backend == "llama_cpp":
        lc = cfg["llm"]["llama_cpp"]
        return LlamaCppLLM(model_path=lc["model_path"], n_ctx=lc["n_ctx"], n_threads=lc["n_threads"], temperature=lc["temperature"], top_p=lc["top_p"])
    else:
        raise ValueError(f"Unsupported LLM backend: {backend}")

def ask_with_grounding(llm: LLMBase, question: str, contexts: List[str], strict: bool = True, sys_rules: str = "") -> str:
    context_block = "\n\n---\n".join([f"Source[{i}]:\n{c}" for i, c in enumerate(contexts)])
    rules = sys_rules or (
        "You are a CRO protocol analyst. Use only the provided sources. "
        "If a detail is missing from sources, say 'Unknown' and list what would be needed. "
        "Cite Source[index] inline like [S:index] when asserting facts."
    )
    prompt = f"""{rules}

QUESTION:
{question}

SOURCES:
{context_block}

INSTRUCTIONS:
- Do NOT invent facts.
- Only answer using information explicitly present in SOURCES.
- When relevant, include short citations like [S:0], [S:3].
- Prefer concise, structured outputs.

ANSWER:"""
    return llm.generate(prompt)
