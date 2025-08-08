# Clinical Protocol Analyzer (BiMCP + CTGov + RAG) — Cross‑Platform

End‑to‑end pipeline to ingest huge clinical trial protocols (500–1500 pages), extract condition & intervention,
generate and execute **BiMCP** trial searches, pull **ClinicalTrials.gov v2** data, run a free local LLM (Llama 3 via **Ollama** or **llama.cpp**),
and produce CRO‑grade analysis (enrollment forecast, optimizations, timeline, cost, site recs).

## Quickstart (Windows / macOS / Linux)

```bash
# 1) Create a venv
python -m venv .venv
# Windows PowerShell:
. .venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) (Option A) Use Ollama as your local LLM
#    Install from https://ollama.com (Windows/macOS/Linux)
#    Then pull a model:
ollama pull llama3:8b

# 3) (Option B) Use llama.cpp
#    Put your GGUF at models/ and set the path in config.yaml

# 4) Place your protocol
cp /path/to/protocol.pdf data/protocol.pdf  # (Windows PowerShell: copy .\some.pdf .\data\protocol.pdf)

# 5) Run
python main.py --protocol data/protocol.pdf
```

Outputs:
- `output/analysis_report.md` and `.pdf`
- `data/mcp_output.txt` (BiMCP results)
- `data/ctgov_matches.jsonl` (CTGov studies)

### MCP Modes (Automatic Fallback)
- Default: `mcp.auto_fallback: true`
- It will try: **CLI → Python API → Mock**
- CLI command is configured at `mcp.executable` (default `biomcp`)
- Python API requires `pip install biomcp-python` (already in requirements)

### PyTorch for Fine‑Tuning
Install PyTorch per your platform **before** running `finetune/train_lora.py`:
- Windows/macOS/Linux (CPU): `pip install torch`
- CUDA (NVIDIA): follow https://pytorch.org/get-started/locally/ for the correct wheel.

## Fine‑Tuning (LoRA)
```bash
# Prepare dataset from your run + CTGov
python finetune/prepare_dataset.py   --protocol_dir data/   --mcp_file data/mcp_output.txt   --ctgov_file data/ctgov_matches.jsonl   --report_file output/analysis_report.md   --out finetune/dataset.jsonl

# Train LoRA (ensure torch installed)
python finetune/train_lora.py --config finetune/config_finetune.yaml
```

> Strict grounding is enabled by default: missing evidence → `Unknown` with gaps listed.
