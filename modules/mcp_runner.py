import subprocess, shutil, textwrap, random, re
def is_cli_available(executable_hint: str) -> bool:
    exe_name = (executable_hint or "biomcp").split(" ")[0]
    return shutil.which(exe_name) is not None
def _unique(items):
    seen=set(); out=[]
    for x in items:
        if x and x not in seen: out.append(x); seen.add(x)
    return out
def build_trial_variants(entities):
    cond = entities.get("condition","") or ""
    cond_clean = entities.get("condition_clean","") or cond
    aliases = entities.get("aliases", []) or []
    abbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", cond)
    conds = _unique([cond_clean] + abbrs + aliases + ([cond] if cond != cond_clean else []))
    intr = entities.get("intervention","") or ""
    intr_clean = entities.get("intervention_clean","") or intr
    iabbrs = re.findall(r"\(([A-Za-z0-9\-]+)\)", intr)
    intrs = _unique([intr_clean] + iabbrs + ([intr] if intr != intr_clean else []))
    pairs = []
    for c in conds[:2 or 1]:
        pairs.append((c, intrs[0] if intrs else intr_clean or intr))
    if len(conds) > 1 and len(intrs) > 1:
        pairs.append((conds[0], intrs[1]))
    if not pairs:
        pairs = [(cond_clean or cond, intr_clean or intr)]
    return pairs[:3]
def generate_four_biomcp_cmds(template_trial, condition, intervention, entities):
    pairs = build_trial_variants(entities)
    cmds = [template_trial.format(condition=c, intervention=i) for (c,i) in pairs]
    kw = f"{entities.get('condition_clean', condition)}, {entities.get('intervention_clean', intervention)}".strip().strip(",")
    cmds.append(f'biomcp article search --keyword "{kw}"')
    return cmds
def run_cli_commands(cmds):
    outputs, ok = [], True
    for c in cmds:
        try:
            out = subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT, text=True, timeout=600)
            outputs.append(f">>> {c}\n{out}".strip())
        except subprocess.CalledProcessError as e:
            ok = False; outputs.append(f">>> {c}\nERROR: {e.output}".strip())
    return ("\n\n".join(outputs), ok)
def run_mock(cmds):
    blocks = []
    for c in cmds:
        if "article search" in c:
            blocks.append(textwrap.dedent(f"""
                >>> {c}
                ARTICLES:
                1. Mock Article A (2024) — enrollment tactics...
                2. Mock Article B (2023) — screen-failure mitigation...
            """).strip())
        else:
            blocks.append(textwrap.dedent(f"""
                >>> {c}
                RESULT_COUNT: {random.randint(5, 25)}
                TOP_SITES: ["MD Anderson","Mayo Clinic","MSK","Stanford","UCSF"]
                AVG_ENROLLMENT_RATE_PM: {round(random.uniform(0.5, 6.0), 2)}
                SCREEN_FAIL_RATE: {round(random.uniform(0.05, 0.35), 2)}
                REGIONS: ["US","EU","APAC"]
                HIST_TRIALS_MATCHED: {random.randint(8, 60)}
            """).strip())
    return "\n\n".join(blocks)
def run_biomcp_four(cmds, prefer="cli"):
    if prefer == "cli" and is_cli_available("biomcp"):
        blob, ok = run_cli_commands(cmds)
        if ok: return blob, "cli"
    return run_mock(cmds), "mock"
