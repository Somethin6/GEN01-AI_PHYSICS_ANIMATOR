from typing import Dict, Any
import json, re


class ConceptAI:
    def __init__(self, llm, retriever, rulebook: str):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook

    def run(self, topic: str, target_length_s: float) -> Dict[str, Any]:
        kb = self.retriever.search(topic, k=5)
        system = (
            "You are the Concept AI. Identify misconceptions, prior knowledge, curiosity gaps, "
            "and a minimal core concept inventory for the topic. Be precise and concise."
        )
        user = f"""Topic: {topic}
Target length (s): {target_length_s}
Relevant local notes (top hits): {kb}

Return JSON with keys: misconceptions[], hooks[], prerequisites[], golden_path[] (atoms of understanding, 5–9 items)."""
        txt = self.llm.chat(system, user, temperature=0.2, max_tokens=1200)
        m = re.search(r"\{.*\}", txt, re.S)
        data = (
            json.loads(m.group(0))
            if m
            else {"misconceptions": [], "hooks": [], "prerequisites": [], "golden_path": []}
        )
        return data
