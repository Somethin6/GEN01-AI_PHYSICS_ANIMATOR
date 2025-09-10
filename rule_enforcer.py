import ast, re
from typing import Dict, Any, List, Tuple

BANNED_KWARGS = {"numbers_to_show", "x_axis_label", "y_axis_label", "unit_size"}
BANNED_TOKENS = [
    ".points", "get_graph(", "FunctionGraph(", "numbers_to_show=", "x_axis_label=", "y_axis_label=", "unit_size="
]

def _remove_bad_kwargs(src: str) -> Tuple[str, List[str]]:
    messages: List[str] = []
    for kw in BANNED_KWARGS:
        pattern = rf"(Axes|NumberLine|NumberPlane)\([^\)]*?{kw}\s*=\s*[^,\)]+,?"
        def repl(m):
            messages.append(f"Removed invalid kwarg '{kw}' from {m.group(1)} constructor")
            txt = m.group(0)
            txt2 = re.sub(rf"\s*{kw}\s*=\s*[^,\)]+,?", "", txt)
            return txt2
        src = re.sub(pattern, repl, src)
    return src, messages

def _enforce_single_mainscene(tree: ast.AST) -> List[str]:
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MainScene":
            count += 1
    if count != 1:
        return [f"Expected exactly one MainScene class, found {count}"]
    return []

def enforce_rulebook(code: str, env: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    report: Dict[str, Any] = {"changed": False, "messages": []}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        report["messages"].append("SyntaxError during AST parse; skipping structural checks.")
        return code, report

    report["messages"].extend(_enforce_single_mainscene(tree))

    new_code, kw_msgs = _remove_bad_kwargs(code)
    if new_code != code:
        report["changed"] = True
        report["messages"].extend(kw_msgs)
        code = new_code

    for tok in BANNED_TOKENS:
        if tok in code:
            report["messages"].append(f"Detected banned token '{tok}' (static lint will remediate if needed)")

    if not env["tools"].get("latex_ok", False) and ("MathTex(" in code or "Tex(" in code):
        report["messages"].append("LaTeX unhealthy: MathTex/Tex will be auto-replaced with Text in patch stage.")

    return code, report
