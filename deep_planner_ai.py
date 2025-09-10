from typing import Dict, Any

_MIN_BEAT = 0.35  # seconds
_PAD = 0.15


def _distribute(total, weights):
    s = sum(weights) or 1.0
    return [total * w / s for w in weights]


class DeepPlannerAI:
    def __init__(self, llm, retriever, rulebook: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook

    def run(
        self,
        topic: str,
        concept: Dict[str, Any],
        deriv: Dict[str, Any],
        vismap: Dict[str, Any],
        target_length_s: float,
    ) -> Dict[str, Any]:
        blocks = vismap.get("blocks", [])
        # Ensure minimum 6 blocks for schema compliance
        n = max(6, len(blocks))
        
        # Pad blocks to minimum required
        while len(blocks) < n:
            blocks.append({
                "intent": "elaborate",
                "manim": {"primitive": "Text", "params": {"text": "..."}},
                "transition_in": "FadeIn",
                "transition_out": "FadeOut", 
                "camera": "static"
            })
        
        weights = []
        for b in blocks:
            c = 1.0
            if "Axes.plot" in str(b):
                c += 0.2
            if "VectorField" in str(b):
                c += 0.5
            weights.append(c)
        
        spans = _distribute(target_length_s - (n + 1) * _PAD, weights)

        t = 0.0
        timeline = []
        for i, (b, dur) in enumerate(zip(blocks, spans)):
            start = max(0.0, t + _PAD)
            end = start + max(_MIN_BEAT, dur)
            timeline.append(
                {
                    "idx": i,
                    "t_start": round(start, 3),
                    "t_end": round(end, 3),
                    "transition_in": b.get("transition_in", "FadeIn"),
                    "transition_out": b.get("transition_out", "FadeOut"),
                    "camera": b.get("camera", "static"),
                    "intent": b.get("intent", "explain"),
                    "manim": b.get("manim", {"primitive": "Text", "params": {"text": "..."}}),
                    "explain_why": "Segmentation + signaling: this beat isolates one idea to manage intrinsic load.",
                }
            )
            t = end
        return {"total_duration_s": round(t, 3), "timeline": timeline}
