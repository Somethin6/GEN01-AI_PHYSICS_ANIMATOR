import re


class RefinerAI:
    def __init__(self, llm, retriever, rulebook: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook

    def run(self, code: str, manim_log: str, latex_ok: bool) -> str:
        instr = []
        if "unexpected keyword argument 'numbers_to_show'" in manim_log:
            instr.append("Remove any numbers_to_show kwargs; call add_coordinates() instead.")
        if (
            "unexpected keyword argument 'x_axis_label'" in manim_log
            or "y_axis_label" in manim_log
        ):
            instr.append(
                "Remove x_axis_label/y_axis_label; use get_axis_labels after creation."
            )
        if "latex error" in manim_log.lower() or "LaTeX is broken" in manim_log:
            instr.append("Replace any MathTex/Tex with Text using Unicode math.")

        system = "You repair Manim CE 0.19 code. Only output corrected code. No commentary."
        user = f"""<ERRORS>
{manim_log[:4000]}
</ERRORS>
<INSTRUCTIONS>
{'; '.join(instr) or 'Keep CE-0.19 constraints; ensure >=6 meaningful animations; avoid deprecated APIs.'}
</INSTRUCTIONS>
<CODE>
{code}
</CODE>"""
        fixed = self.llm.chat(system, user, temperature=0.1, max_tokens=3500)
        m = re.search(r"```python(.*?)```", fixed, re.S)
        return m.group(1).strip() if m else fixed.strip()
