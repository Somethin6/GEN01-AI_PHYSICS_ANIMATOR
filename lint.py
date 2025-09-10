import re, json
from pathlib import Path

ALLOW = json.loads(Path("knowledge/api_allowlist.json").read_text(encoding="utf-8"))
RULES = None

def static_lint(code: str, env):
    global RULES
    if RULES is None:
        import yaml
        RULES = yaml.safe_load(Path("knowledge/manim_rulebook.yaml").read_text(encoding="utf-8"))

    report = {"blocked": False, "messages": []}
    # ban tokens outright (exact substring removal). For safety do repeated passes until stable.
    changed = True
    while changed:
        changed = False
        for tok in RULES["banned_tokens"]:
            if tok in code:
                code = code.replace(tok, "")
                report["blocked"] = True
                changed = True
                report["messages"].append(f"Removed banned token: {tok}")

    # rewrite common pitfalls (multiple passes for cascading patterns)
    for _ in range(2):
        for rr in RULES["rewrite_rules"]:
            new_code = re.sub(rr["pattern"], rr["replace"], code)
            if new_code != code:
                report["blocked"] = True
                report["messages"].append(f"Applied rewrite: {rr['pattern']} -> {rr['replace']}")
                code = new_code

    # sanity: ensure exactly one MainScene
    if code.count("class MainScene(") != 1:
        report["messages"].append("Ensure exactly one MainScene(Scene) class.")

    # heuristic: at least min_animations operations present
    min_anims = RULES.get("min_animations", 0)
    if min_anims:
        anim_tokens = [
            "Create(", "FadeIn(", "FadeOut(", "Write(", "Unwrite(",
            "Transform(", "ReplacementTransform(", "Indicate(", "Rotate(", "MoveAlongPath(", "MoveToTarget("
        ]
        count = sum(code.count(tok) for tok in anim_tokens)
        if count < min_anims:
            report["messages"].append(f"Low animation count ({count} < {min_anims}). Consider adding beats: title, axes, curve, tracker animate, highlight, outro.")
    return code, report
