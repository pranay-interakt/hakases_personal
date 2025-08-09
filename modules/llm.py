from typing import Any, Dict
import requests
class LLMBase: ...
class OllamaLLM(LLMBase):
    def __init__(self, model: str, options: Dict[str, Any]):
        self.model, self.options = model, options
    def generate(self, prompt: str) -> str:
        try:
            import ollama
            r = ollama.generate(model=self.model, prompt=prompt, options=self.options)
            return r.get("response","")
        except Exception:
            data = {"model": self.model, "prompt": prompt, "options": self.options}
            resp = requests.post("http://localhost:11434/api/generate", json=data, timeout=600)
            resp.raise_for_status()
            return resp.json().get("response","")
def build_llm(cfg): 
    o = cfg["llm"]["ollama"]; return OllamaLLM(o["model"], o["options"])
