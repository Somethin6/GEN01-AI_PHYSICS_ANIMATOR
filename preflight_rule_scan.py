import re
from typing import Dict, Any

ANIM_TOKENS = [
    "Create(", "FadeIn(", "FadeOut(", "Write(", "Unwrite(", "Transform(",
    "ReplacementTransform(", "Indicate(", "Rotate(", "MoveAlongPath(", "MoveToTarget(", ".animate"
]
BANNED = ["get_graph(", "FunctionGraph(", "numbers_to_show=", "x_axis_label=", "y_axis_label=", "unit_size=", ".points"]

def preflight_rule_scan(code: str, env: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    for tok in BANNED:
        if tok in code:
            issues.append(f"BANNED token present: {tok}")
    # animation richness heuristic
    anim_count = sum(code.count(t) for t in ANIM_TOKENS)
    target = env.get("cfg", {}).get("agent", {}).get("min_animations", 6)
    if anim_count < target:
        issues.append(f"Animation richness low ({anim_count} < {target}) – add more distinct plays/animations.")
    # ensure single MainScene
    if code.count("class MainScene(") != 1:
        issues.append("Expected exactly one 'class MainScene(Scene)'.")
    # LaTeX advisory
    if ("MathTex(" in code or "Tex(" in code) and not env["tools"].get("latex_ok", False):
        issues.append("LaTeX unhealthy – replace MathTex/Tex with Text (auto-patch will handle).")
    return {"issues": issues, "animation_count": anim_count}