import re

def parse_manim_error_summary(logs: str) -> dict:
    latex_err = bool(re.search(r"LaTeX compilation error|latex: major issue", logs, re.I))
    unexpected_kw = re.findall(r"TypeError: Mobject.__init__\(\).*unexpected keyword argument '([^']+)'", logs)
    wiggle_attr = "object has no attribute 'wiggle'" in logs
    return {
        "latex_error": latex_err,
        "unexpected_kwargs": unexpected_kw,
        "wiggle_method_misuse": wiggle_attr,
        "summary": _make_summary(latex_err, unexpected_kw, wiggle_attr)
    }

def _make_summary(latex_err, unk, wig):
    parts = []
    if latex_err:
        parts.append("LaTeX unhealthy → prefer Text() over MathTex().")
    if unk:
        parts.append(f"Unexpected kwargs: {', '.join(unk)} → remove and add numbers via add_coordinates()/add_numbers() after creation.")
    if wig:
        parts.append("Do not call .wiggle(); use self.play(Wiggle(mobject)).")
    return " | ".join(parts) or "See full log."
