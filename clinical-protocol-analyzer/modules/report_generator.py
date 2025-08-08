from __future__ import annotations
from typing import Dict, Any, List
import json
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

def to_markdown(entities: Dict[str, Any], mcp_mode: str, mcp_commands: List[str], mcp_blob: str, ctgov_items: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Clinical Protocol Analysis\n")
    lines.append(f"**Condition:** {entities.get('condition')}  ")
    lines.append(f"**Intervention:** {entities.get('intervention')}  ")
    lines.append(f"**Aliases:** {', '.join(entities.get('aliases', [])) or '—'}  ")
    lines.append(f"**BiMCP Mode Used:** {mcp_mode}\n")

    lines.append("## MCP Commands")
    for c in mcp_commands:
        lines.append(f"- `{c}`")

    lines.append("\n## BiMCP Output (truncated)")
    lines.append("```\n" + (mcp_blob[:4000] if mcp_blob else "") + "\n```\n")

    lines.append("## ClinicalTrials.gov Matches (sample)")
    for it in ctgov_items[:20]:
        lines.append(f"- **{it.get('nctId')}** — {it.get('briefTitle')}  | status={it.get('overallStatus')} | phase={it.get('phases')}")

    def block(title, obj):
        lines.append(f"\n## {title}")
        lines.append("```json\n" + json.dumps(obj, indent=2) + "\n```")

    block("Enrollment Forecast", analysis.get("forecast", {}))
    block("Enrollment Optimizations", analysis.get("optimizations", {}))
    block("Timeline", analysis.get("timeline", {}))
    block("Cost Effectiveness", analysis.get("cost", {}))
    block("Recommended Sites", analysis.get("sites", {}))

    return "\n".join(lines)

def md_to_pdf(md_text: str, pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    width, height = LETTER
    y = height - 50
    for line in md_text.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        # trim long lines for simple PDF rendering
        c.drawString(50, y, line[:120])
        y -= 14
    c.save()
