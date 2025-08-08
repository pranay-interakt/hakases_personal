import argparse, json, os, glob

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol_dir", required=True)
    ap.add_argument("--mcp_file", required=True)
    ap.add_argument("--ctgov_file", required=True)
    ap.add_argument("--report_file", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Collect protocol texts (if any .txt/.md are available post-OCR or manual export)
    protos = []
    for p in glob.glob(os.path.join(args.protocol_dir, "*.txt")) + glob.glob(os.path.join(args.protocol_dir, "*.md")):
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            protos.append(f.read())

    mcp_blob = open(args.mcp_file, "r", encoding="utf-8", errors="ignore").read()
    ctgov_items = [json.loads(line) for line in open(args.ctgov_file, "r", encoding="utf-8", errors="ignore") if line.strip()]
    report = open(args.report_file, "r", encoding="utf-8", errors="ignore").read()

    # Summarize CTGov
    ct_summaries = []
    for it in ctgov_items[:200]:
        ct_summaries.append(f"NCT {it.get('nctId')} | {it.get('briefTitle')} | {it.get('overallStatus')} | {it.get('phases')}")

    prompt = (
        "You are a CRO analyst. Given the protocol excerpts, MCP output, and CTGov matches, produce enrollment forecast, optimization, timeline, cost and site suggestions."
        "\nMCP_OUTPUT:\n" + mcp_blob[:8000] + "\nCTGOV:\n" + "\n".join(ct_summaries[:100])
    )
    completion = report

    records = [{"prompt": prompt, "completion": completion}]

    # Optional: weak supervision by adding raw protocol snippets
    for i, pt in enumerate(protos):
        records.append({
            "prompt": "Summarize critical eligibility and operational constraints helpful for feasibility and enrollment planning.",
            "completion": pt[:4000]
        })

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"Wrote {len(records)} records to {args.out}")

if __name__ == "__main__":
    main()
