import argparse, yaml, json, os
from modules.logger import get_logger
from modules import parser as parser_mod
from modules.chunker import chunk_text
from modules.retriever import Retriever
from modules.llm import build_llm
from modules.extractor import extract_trial_entities
from modules.mcp_runner import generate_four_biomcp_cmds, run_biomcp_four
from modules.ctgov import query_studies_variants, simplify_ctgov
from modules.literature import pubmed_search, pubmed_summaries
from modules.similarity import Selector
from modules.analyzer import cro_analysis_longform
from modules.report_generator import to_markdown, md_to_pdf

def ensure_dirs():
    for d in ["logs","output","data"]:
        os.makedirs(d, exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, help="Path to protocol PDF/DOCX/TXT")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    ensure_dirs()
    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
    log = get_logger(cfg["runtime"]["log_path"])

    log.info(f"Loading protocol: {args.protocol}")
    raw = parser_mod.load_text(args.protocol)
    text = parser_mod.clean_text(raw)
    log.info(f"Protocol length: {len(text):,} chars")

    size = cfg["vector_store"]["chunk_size"]; overlap = cfg["vector_store"]["chunk_overlap"]
    chunks = chunk_text(text, size=size, overlap=overlap)
    log.info(f"Chunks: {len(chunks)}")
    Retriever.build(chunks, cfg["vector_store"]["path"], cfg["embeddings"]["model"], cfg["embeddings"]["batch_size"], cfg["embeddings"]["device"])

    llm = build_llm(cfg)

    entities = extract_trial_entities(llm, chunks, strict=cfg["runtime"]["strict_grounding"])
    log.info(f"Entities: {entities}")

    cmds = generate_four_biomcp_cmds(cfg["mcp"]["command_template"],
                                     entities.get("condition_clean", entities.get("condition","")),
                                     entities.get("intervention_clean", entities.get("intervention","")),
                                     entities)
    mcp_blob, mcp_mode_used = run_biomcp_four(cmds, prefer=cfg["mcp"].get("prefer","cli"))
    with open("data/mcp_output.txt", "w", encoding="utf-8") as f: f.write(mcp_blob)

    ct_json_blobs = query_studies_variants(entities, limit=cfg["ctgov"]["max_records"], timeout=cfg["ctgov"]["timeout"], max_pairs=6)
    ct_all = []
    for blob in ct_json_blobs: ct_all.extend(simplify_ctgov(blob))
    seen, dedup = set(), []
    for it in ct_all:
        nct = it.get("nctId")
        if nct and nct not in seen: dedup.append(it); seen.add(nct)

    selector = Selector(cfg["embeddings"]["model"])
    query = f"{entities.get('condition_clean','')} {entities.get('intervention_clean','')}"
    ranked_ct = selector.top_k(query, dedup, field="briefTitle", k=10)
    ct_top10 = [it for score, it in ranked_ct]
    with open("data/ctgov_top10.jsonl", "w", encoding="utf-8") as f:
        for it in ct_top10: f.write(json.dumps(it)+"\n")

    pmids = pubmed_search(entities.get("condition_clean",""), entities.get("intervention_clean",""), maxids=80)
    pms = pubmed_summaries(pmids)
    ranked_pm = selector.top_k(query, pms, field="title", k=10)
    pubmed_top10 = [it for score, it in ranked_pm]
    with open("data/pubmed_top10.jsonl", "w", encoding="utf-8") as f:
        for it in pubmed_top10: f.write(json.dumps(it)+"\n")

    narrative = cro_analysis_longform(llm, chunks, mcp_blob, ct_top10, pubmed_top10, k=cfg["runtime"]["max_retrieved_chunks"])

    with open(cfg["reporting"]["output_markdown"], "w", encoding="utf-8") as f:
        f.write(narrative)
    md_to_pdf(narrative, cfg["reporting"]["output_pdf"])

    print("\n" + "="*80)
    print("FULL CRO ANALYSIS (Markdown):")
    print("="*80 + "\n")
    print(narrative)
    print("\n" + "="*80)
    print(f"Saved: {cfg['reporting']['output_markdown']}  |  {cfg['reporting']['output_pdf']}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
