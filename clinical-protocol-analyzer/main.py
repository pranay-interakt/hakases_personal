import argparse
import yaml
import json
import os
from modules.logger import get_logger
from modules import parser as parser_mod
from modules.chunker import chunk_text
from modules.retriever import Retriever
from modules.llm import build_llm
from modules.extractor import extract_trial_entities
from modules.mcp_runner import build_query_variants, generate_mcp_commands, run_mcp_auto
from modules.ctgov import query_studies_variants, simplify_ctgov
# Replaced old analyzer import:
from modules.advanced_analyzer import SECTIONS
from modules.report_generator import to_markdown, md_to_pdf


def ensure_dirs():
    for d in ["logs", "output", "data"]:
        os.makedirs(d, exist_ok=True)


def run_advanced_analysis(llm, protocol_chunks, mcp_blob, ctgov_items, k):
    narrative_sections = []
    for section in SECTIONS:
        title = section["title"]
        fn = section["fn"]
        narrative_sections.append(f"# {title}\n")
        output = fn(llm, protocol_chunks, mcp_blob, ctgov_items)
        narrative_sections.append(output)
        narrative_sections.append("\n\n")
    return "\n".join(narrative_sections)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, help="Path to protocol PDF/DOCX/TXT")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    ensure_dirs()
    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
    log = get_logger(cfg["runtime"]["log_path"])

    # 1) Load protocol
    log.info(f"Loading protocol: {args.protocol}")
    raw = parser_mod.load_text(args.protocol)
    text = parser_mod.clean_text(raw)
    log.info(f"Protocol length: {len(text):,} chars")

    # 2) Chunk & index
    size = cfg["vector_store"]["chunk_size"]
    overlap = cfg["vector_store"]["chunk_overlap"]
    chunks = chunk_text(text, size=size, overlap=overlap)
    log.info(f"Chunks: {len(chunks)}")
    Retriever.build(
        chunks,
        index_path=cfg["vector_store"]["path"],
        emb_model=cfg["embeddings"]["model"],
        batch_size=cfg["embeddings"]["batch_size"],
        device=cfg["embeddings"]["device"],
    )

    # 3) LLM
    llm = build_llm(cfg)

    # 4) Extract entities (with cleaned terms)
    entities = extract_trial_entities(llm, chunks, strict=cfg["runtime"]["strict_grounding"])
    log.info(f"Entities: {entities}")

    # 5) MCP variant search
    pairs, canon_pair_key = build_query_variants(entities)
    cmds = generate_mcp_commands(
        template=cfg["mcp"]["command_template"],
        pairs=pairs,
        limit=max(5, cfg["mcp"]["variants"]),
    )
    mcp_blob, mcp_mode_used = run_mcp_auto(
        cmds,
        canonical_cond=entities.get("condition_clean", entities.get("condition", "")),
        canonical_intr=entities.get("intervention_clean", entities.get("intervention", "")),
        prefer=cfg["mcp"].get("prefer", "cli"),
    )
    with open("data/mcp_output.txt", "w", encoding="utf-8") as f:
        f.write(mcp_blob)

    # 6) CTGov variant search
    ct_json_blobs = query_studies_variants(
        entities,
        limit=cfg["ctgov"]["max_records"],
        timeout=cfg["ctgov"]["timeout"],
        max_pairs=6,
    )
    ct_items = []
    for blob in ct_json_blobs:
        ct_items.extend(simplify_ctgov(blob))
    # dedupe by NCT
    seen = set()
    dedup = []
    for it in ct_items:
        nct = it.get("nctId")
        if nct and nct not in seen:
            dedup.append(it)
            seen.add(nct)
    ct_items = dedup
    with open("data/ctgov_matches.jsonl", "w", encoding="utf-8") as f:
        for it in ct_items:
            f.write(json.dumps(it) + "\n")

    # 7) CRO narrative analysis (Markdown) using advanced_analyzer
    narrative = run_advanced_analysis(
        llm=llm,
        protocol_chunks=chunks,
        mcp_blob=mcp_blob,
        ctgov_items=ct_items,
        k=cfg["runtime"]["max_retrieved_chunks"],
    )

    # 8) Write report + print to terminal
    md = to_markdown(narrative)
    with open(cfg["reporting"]["output_markdown"], "w", encoding="utf-8") as f:
        f.write(md)
    md_to_pdf(md, cfg["reporting"]["output_pdf"])

    # --- PRINT TO TERMINAL (as requested) ---
    print("\n" + "=" * 80)
    print("CRO ANALYSIS (Markdown):")
    print("=" * 80 + "\n")
    print(md)
    print("\n" + "=" * 80)
    print(f"Saved: {cfg['reporting']['output_markdown']}  |  {cfg['reporting']['output_pdf']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
