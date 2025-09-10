from typing import Dict, Any
import textwrap

BANNED = [
    "numbers_to_show=",
    "x_axis_label=",
    "y_axis_label=",
    ".points",
    "get_graph(",
    "FunctionGraph(",
    ".wiggle(",
]


class CoderAI:
    def __init__(self, llm, retriever, rulebook: str, latex_ok: bool, media_dir: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook
        self.latex_ok = latex_ok
        self.media_dir = media_dir

    def _guard(self, code: str) -> str:
        for b in BANNED:
            if b in code:
                code = code.replace(b, "")
        return code

    def run(self, scene_json: Dict[str, Any]) -> str:
        latex_ok = scene_json["meta"].get("latex_ok", False)
        beats = scene_json["scenes"][0]["beats"]
        if len(beats) < 6:
            beats += beats[: (6 - len(beats))]

        header = textwrap.dedent(
            f"""
        from manim import *
        import numpy as np

        class MainScene(Scene):
            def construct(self):
                # Deterministic seed
                np.random.seed(42)
        """
        ).strip("\n")

        body_lines = []
        body_lines.append("                # Preflight axes (allocated lazily)")
        body_lines.append("                axes = None")

        used_axes = any(b["primitive"].startswith("Axes") for b in beats)
        if used_axes:
            body_lines.append(
                "                axes = Axes(x_range=[-5,5,1], y_range=[-3,3,1], tips=False)"
            )
            body_lines.append("                axes.add_coordinates()  # coordinate labels")

        for i, b in enumerate(beats):
            prim = b["primitive"]
            params = b.get("params", {})
            intent = (b.get("intent", "explain")).replace("\"", "'")
            body_lines.append(f"\n                # Beat {i}: {intent}")
            create = ""
            if prim == "Text":
                txt = params.get("text", "...").replace("\"", "'")
                body_lines.append(
                    f"                obj_{i} = Text('{txt}', font_size={params.get('font_size', 36)})"
                )
                create = f"Write(obj_{i})"
            elif prim == "Axes.plot":
                body_lines.append(
                    "                if axes is None:\n                    axes = Axes(x_range=[-5,5,1], y_range=[-3,3,1], tips=False)\n                    axes.add_coordinates()"
                )
                expr = params.get("expr", "np.sin(x)")
                body_lines.append(f"                f_{i} = lambda x: {expr}")
                body_lines.append(
                    f"                curve_{i} = always_redraw(lambda: axes.plot(f_{i}))"
                )
                create = f"Create(axes), Create(curve_{i})"
            elif prim == "VectorField":
                body_lines.append(
                    "                field_func = lambda pos: np.array([ -pos[1], pos[0], 0 ])"
                )
                body_lines.append(
                    f"                vf_{i} = ArrowVectorField(field_func, x_range=[-3,3,1], y_range=[-2,2,1])"
                )
                create = f"Create(vf_{i})"
            elif prim == "StreamLines":
                body_lines.append(
                    "                field_func = lambda pos: np.array([ -pos[1], pos[0], 0 ])"
                )
                body_lines.append(
                    f"                sl_{i} = StreamLines(field_func, x_range=[-3,3,1], y_range=[-2,2,1])"
                )
                body_lines.append(
                    f"                sl_{i}.start_animation(warm_up=False, flow_speed=1.0)"
                )
                create = f"Create(sl_{i})"
            elif prim == "ParametricFunction":
                body_lines.append("                t_tracker = ValueTracker(0.0)")
                body_lines.append(
                    f"                func_{i} = always_redraw(lambda: ParametricFunction(lambda t: np.array([{params.get('x','t')}, {params.get('y','np.sin(t)')}, 0]), t_range=[-3,3]))"
                )
                create = f"Create(func_{i})"
            else:
                body_lines.append(
                    f"                obj_{i} = Text('Unsupported primitive {prim}').scale(0.6)"
                )
                create = f"FadeIn(obj_{i})"

            body_lines.append(f"                self.play({create})")
            body_lines.append("                self.wait(0.2)")

            if prim.startswith("Axes"):
                body_lines.append(
                    f"                self.play(FadeOut(axes), run_time=0.2)"
                )
            else:
                body_lines.append(
                    f"                self.play(FadeOut(*self.mobjects), run_time=0.2)"
                )

        footer = "                self.wait(0.2)\n"

        code = header + "\n" + "\n".join(body_lines) + "\n" + footer
        return self._guard(code)
