from typing import Dict, Any
import json, re


class VisualsAI:
    def __init__(self, llm, retriever, rulebook: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook

    def run(self, topic: str, concept: Dict[str, Any], deriv: Dict[str, Any]) -> Dict[str, Any]:
        system = (
            "You map derivation steps to visuals. For each block, specify: intent, why-this-visual, "
            "which Manim primitive (Axes.plot/VectorField/StreamLines/ParametricFunction/Text), "
            "any trackers needed, camera moves, and transformation path (Write→Transform→Fade). "
            "Respect Manim CE 0.19 API constraints."
        )
        user = f"""Topic: {topic}
Derivation steps count: {len(deriv.get('steps', []))}
Return JSON: {{"blocks":[{{"intent":"…","manim":{{"primitive":"Axes.plot","params":{{}}}}, "camera":"…","transition_in":"…","transition_out":"…"}}…]}}"""
        txt = self.llm.chat(system, user, temperature=0.2, max_tokens=3000)
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {"blocks": []}
