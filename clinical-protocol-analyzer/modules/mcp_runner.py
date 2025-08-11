# modules/mcp_runner.py
from __future__ import annotations
from typing import List, Tuple, Dict
import subprocess, shutil, textwrap, random, re

def is_cli_available(executable_hint: str) -> bool:
    exe_name = (executable_hint or "biomcp").split(" ")[0]
    return shutil.which(exe_name) is not None

def _unique(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x and x not in seen:
            out.append(x); seen.add(x)
    return out

def build_query_variants(entities: Dict[str, str]) -> Tuple[List[str], str]:
    # Build smart condition variants: cleaned, abbreviation in (), aliases, base
    cond = entities.get("condition","") or ""
    cond_clean = entities.get("condition_clean","") or cond
    aliases = entities.get("aliases", []) or []
    # extract abbr from original e.g. "(ARDS)"
    abbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", cond)
    cond_variants = _unique([cond_clean] + abbrs + aliases + ([cond] if cond != cond_clean else []))

    intr = entities.get("intervention","") or ""
    intr_clean = entities.get("intervention_clean","") or intr
    # derive simple variants like "mAb" without parens
    intr_abbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", intr)
    intr_variants = _unique([intr_clean] + intr_abbrs + ([intr] if intr != intr_clean else []))
    return ([(c, i) for c in cond_variants for i in intr_variants], f"{cond_clean}|{intr_clean}")

def generate_mcp_commands(template: str, pairs: List[Tuple[str, str]], limit: int = 5) -> List[str]:
    cmds = []
    for (cond, intr) in pairs[:limit]:
        cmds.append(template.format(condition=cond, intervention=intr))
    return _unique(cmds)

def run_cli_commands(cmds: List[str]) -> Tuple[str, bool]:
    outputs, ok = [], True
    for c in cmds:
        try:
            out = subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT, text=True, timeout=600)
            outputs.append(f">>> {c}\n{out}".strip())
        except subprocess.CalledProcessError as e:
            ok = False
            outputs.append(f">>> {c}\nERROR: {e.output}".strip())
    return ("\n\n".join(outputs), ok)

def run_python_api(condition: str, intervention: str) -> Tuple[str, bool]:
    try:
        from biomcp import Client
    except Exception as e:
        return (f"ERROR: biomcp-python not installed or failed to import: {e}", False)
    try:
        client = Client()
        res = client.trial.search(condition=condition, intervention=intervention)
        return (str(res), True)
    except Exception as e:
        return (f"ERROR: biomcp-python call failed: {e}", False)

def run_mock(cmds: List[str]) -> str:
    blocks = []
    for c in cmds:
        blocks.append(textwrap.dedent(f"""
            >>> {c}
            RESULT_COUNT: {random.randint(5, 25)}
            TOP_SITES: ["MD Anderson","Mayo Clinic","Memorial Sloan Kettering","Stanford","UCSF"]
            AVG_ENROLLMENT_RATE_PM: {round(random.uniform(0.5, 6.0), 2)}
            SCREEN_FAIL_RATE: {round(random.uniform(0.05, 0.35), 2)}
            REGIONS: ["US","EU","APAC"]
            HIST_TRIALS_MATCHED: {random.randint(8, 60)}
            NOTES: "Synthetic mock."
        """).strip())
    return "\n\n".join(blocks)

def run_mcp_auto(cmds: List[str], canonical_cond: str, canonical_intr: str, prefer: str = "cli") -> Tuple[str, str]:
    order = ["cli","python"] if prefer == "cli" else ["python","cli"]
    for mode in order:
        if mode == "cli" and is_cli_available("biomcp"):
            blob, ok = run_cli_commands(cmds)
            if ok: return (blob, "cli")
        if mode == "python":
            blob, ok = run_python_api(canonical_cond, canonical_intr)
            if ok: return (blob, "python")
    return (run_mock(cmds), "mock")
