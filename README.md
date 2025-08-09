# Clinical Protocol Intel (Ollama Llama3)

1) Create venv & install
```
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

2) LLM backend (Ollama)
```
ollama pull llama3:8b
```

3) Run
```
python main.py --protocol data/protocol.pdf
```

Artifacts in `output/` + intermediate in `data/`.
