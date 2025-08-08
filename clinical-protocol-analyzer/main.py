import argparse, yaml, json, os
from modules.logger import get_logger
from modules import parser as parser_mod
from modules.chunker import chunk_text
from modules.retriever import Retriever
from modules.llm import build_llm
from modules.extractor import extract_trial_entities
from modules.mcp_runner import generate_mcp_commands, run_mcp_auto, run_cli_commands, run_python_api
from modules.ctgov import query_studies, simplify_ctgov
from modules.analyzer import cro_analysis
from modules.report_generator import to_markdown, md_to_pdf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, help="Path to protocol PDF/DOCX/TXT")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
    log = get_logger(cfg["runtime"]["log_path"])

    # 1) Load protocol
    log.info(f"Loading protocol: {args.protocol}")
    raw = parser_mod.load_text(args.protocol)
    text = parser_mod.clean_text(raw)
    log.info(f"Protocol length: {len(text):,} chars")

    # 2) Chunk & build index
    size = cfg["vector_store"]["chunk_size"]
    overlap = cfg["vector_store"]["chunk_overlap"]
    chunks = chunk_text(text, size=size, overlap=overlap)
    log.info(f"Chunks: {len(chunks)}")

    retriever = Retriever.build(
        chunks,
        index_path=cfg["vector_store"]["path"],
        emb_model=cfg["embeddings"]["model"],
        batch_size=cfg["embeddings"]["batch_size"],
        device=cfg["embeddings"]["device"],
    )

    # 3) Build LLM
    llm = build_llm(cfg)

    # 4) Extract entities
    entities = extract_trial_entities(llm, chunks, strict=cfg["runtime"]["strict_grounding"])
    log.info(f"Entities: {entities}")

    # 5) Build commands
    cmds = generate_mcp_commands(
        template=cfg["mcp"]["command_template"],
        condition=entities.get("condition", "Unknown"),
        intervention=entities.get("intervention", "Unknown"),
        aliases=entities.get("aliases", []),
        variants=cfg["mcp"]["variants"]
    )

    # 6) Execute BiMCP with automatic fallback
    mcp_mode_used = "mock"
    if cfg["mcp"].get("auto_fallback", True):
        blob, used = run_mcp_auto(cmds, entities.get("condition", ""), entities.get("intervention", ""), prefer=cfg["mcp"].get("prefer", "cli"))
        mcp_blob = blob
        mcp_mode_used = used
    else:
        # manual: try CLI or Python as configured; else mock
        if cfg["mcp"].get("prefer", "cli") == "cli":
            blob, ok = run_cli_commands(cmds)
            mcp_blob = blob if ok else "ERROR: CLI failed"
            mcp_mode_used = "cli" if ok else "mock"
        else:
            blob, ok = run_python_api(entities.get("condition", ""), entities.get("intervention", ""))
            mcp_blob = blob if ok else "ERROR: Python API failed"
            mcp_mode_used = "python" if ok else "mock"

    with open("data/mcp_output.txt", "w", encoding="utf-8") as f:
        f.write(mcp_blob)

    # 7) ClinicalTrials.gov
    ct_items = []
    if cfg.get("ctgov", {}).get("enabled", True):
        try:
            ct_json = query_studies(
                entities.get("condition", ""),
                entities.get("intervention", ""),
                limit=cfg["ctgov"]["max_records"],
                timeout=cfg["ctgov"]["timeout"]
            )
            ct_items = simplify_ctgov(ct_json)
        except Exception as e:
            log.warning("CTGov query failed: %s", e)
        with open("data/ctgov_matches.jsonl", "w", encoding="utf-8") as f:
            for it in ct_items:
                f.write(json.dumps(it) + "\n")

    # 8) Analyze
    analysis = cro_analysis(
        llm=llm,
        protocol_chunks=chunks,
        mcp_blob=mcp_blob,
        ctgov_items=ct_items,
        k=cfg["runtime"]["max_retrieved_chunks"],
        strict=cfg["runtime"]["strict_grounding"]
    )

    # 9) Report
    md = to_markdown(entities, mcp_mode_used, cmds, mcp_blob, ct_items, analysis)
    with open(cfg["reporting"]["output_markdown"], "w", encoding="utf-8") as f:
        f.write(md)
    md_to_pdf(md, cfg["reporting"]["output_pdf"])

    log.info("Done. Report saved to %s and %s", cfg["reporting"]["output_markdown"], cfg["reporting"]["output_pdf"])

if __name__ == "__main__":
    main()
