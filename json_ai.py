from typing import Dict, Any


class JSONSynthAI:
    def __init__(self, llm, retriever, rulebook: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook

    def run(self, topic: str, deep_plan: Dict[str, Any], latex_ok: bool) -> Dict[str, Any]:
        beats = []
        for item in deep_plan["timeline"]:
            beats.append(
                {
                    "start": item["t_start"],
                    "end": item["t_end"],
                    "transition_in": item["transition_in"],
                    "transition_out": item["transition_out"],
                    "camera": item["camera"],
                    "primitive": item["manim"]["primitive"],
                    "params": item["manim"].get("params", {}),
                    "intent": item["intent"],
                }
            )
        return {
            "meta": {"topic": topic, "latex_ok": bool(latex_ok)},
            "scenes": [{"name": "MainScene", "beats": beats}],
        }
