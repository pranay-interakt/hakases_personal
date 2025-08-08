from __future__ import annotations
from typing import List, Tuple
import subprocess, shutil, textwrap, random

def is_cli_available(executable_hint: str) -> bool:
    exe_name = (executable_hint or "biomcp").split(" ")[0]
    return shutil.which(exe_name) is not None

def generate_mcp_commands(template: str, condition: str, intervention: str, aliases: List[str], variants: int = 3) -> List[str]:
    aliases = aliases or []
    phrases = [p for p in dict.fromkeys([condition] + aliases) if p and p != "Unknown"]
    cmds = []
    for i in range(min(variants, max(1, len(phrases)))):
        phr = phrases[i % len(phrases)]
        cmd = template.format(condition=phr, intervention=intervention)
        cmds.append(cmd)
    if not cmds:
        cmds = [template.format(condition="Unknown", intervention=intervention)]
    return cmds

def run_cli_commands(cmds: List[str]) -> Tuple[str, bool]:
    outputs = []
    ok = True
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
        from biomcp import Client  # pip install biomcp-python
    except Exception as e:
        return (f"ERROR: biomcp-python not installed or failed to import: {e}", False)
    try:
        client = Client()
        # NOTE: Adjust per the actual biomcp-python API if different
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
            TOP_SITES: ["MD Anderson", "Mayo Clinic", "Memorial Sloan Kettering", "Stanford", "UCSF"]
            AVG_ENROLLMENT_RATE_PM: {round(random.uniform(0.5, 6.0), 2)}
            SCREEN_FAIL_RATE: {round(random.uniform(0.05, 0.35), 2)}
            REGIONS: ["US", "EU", "APAC"]
            HIST_TRIALS_MATCHED: {random.randint(8, 60)}
            NOTES: "Synthetic mock output. Replace with real biomcp when available."
        """).strip())
    return "\n\n".join(blocks)

def run_mcp_auto(cmds: List[str], condition: str, intervention: str, prefer: str = "cli") -> Tuple[str, str]:
    """Return (blob, mode_used) where mode_used in {"cli", "python", "mock"}"""
    # Try preferred first
    order = ["cli", "python"] if prefer == "cli" else ["python", "cli"]
    for mode in order:
        if mode == "cli":
            if is_cli_available("biomcp"):
                blob, ok = run_cli_commands(cmds)
                if ok:
                    return (blob, "cli")
        elif mode == "python":
            blob, ok = run_python_api(condition, intervention)
            if ok:
                return (blob, "python")
    # Fallback to mock
    return (run_mock(cmds), "mock")
