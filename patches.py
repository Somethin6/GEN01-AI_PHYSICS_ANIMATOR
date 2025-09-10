import re

def auto_patch(code: str, env):
    changed = False
    msgs = []

    # If LaTeX unhealthy OR forced: replace MathTex/Tex with Text safely
    force_no_latex = env.get("state", {}).get("force_no_latex", False)
    if (not env["tools"]["latex_ok"]) or force_no_latex:
        if "MathTex(" in code:
            code = re.sub(r"MathTex\(", "Text(", code)
            changed = True
            msgs.append("LaTeX disabled → replaced MathTex with Text.")
        if "Tex(" in code:
            code = re.sub(r"Tex\(", "Text(", code)
            changed = True
            msgs.append("LaTeX disabled → replaced Tex with Text.")
        # flip any hard-coded latex_ok flags to False
        code_new = re.sub(r"latex_ok\s*=\s*True", "latex_ok = False", code)
        if code_new != code:
            code = code_new
            changed = True
            msgs.append("Forced latex_ok=False due to prior LaTeX error.")

    # Ensure always_redraw returns a fresh mobject (no .points mutation)
    if ".points" in code:
        code = code.replace(".points", ".__POINTS_FORBIDDEN__")
        changed = True
        msgs.append("Blocked direct .points mutation (use always_redraw with new mobject/become).")

    # Remove unsupported animate chaining of .wiggle() replacing with Indicate animation comment
    if ".wiggle(" in code:
        code = re.sub(r"\.wiggle\(\)", "", code)
        changed = True
        msgs.append("Removed unsupported .wiggle() chain; refiner should use Indicate(...) instead.")

    # Inject latex_ok stub & global retrieval if missing
    if "latex_ok = globals().get(" not in code:
        if "from manim import *" in code:
            insertion = "# Runtime env flag injected if not provided\nlatex_ok = globals().get(\"latex_ok\", %s)\n" % ("True" if env["tools"]["latex_ok"] and not env.get("state", {}).get("force_no_latex") else "False")
            code = code.replace("from manim import *", "from manim import *\n" + insertion)
            changed = True
            msgs.append("Inserted latex_ok runtime flag stub.")

    # Ensure import numpy if referenced
    if "np." in code and "import numpy as np" not in code:
        code = code.replace("from manim import *", "from manim import *\nimport numpy as np")
        changed = True
        msgs.append("Added 'import numpy as np'.")

    return code, {"changed": changed, "messages": msgs}
