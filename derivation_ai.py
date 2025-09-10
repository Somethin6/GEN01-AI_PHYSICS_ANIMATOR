from typing import Dict, Any
import json, re


class DerivationAI:
    def __init__(self, llm, retriever, rulebook: str, latex_ok: bool):
        self.llm = llm
        self.retriever = retriever
        self.rulebook = rulebook
        self.latex_ok = latex_ok

    def run(self, topic: str, concept: Dict[str, Any]) -> Dict[str, Any]:
        hits = self.retriever.search(topic, k=6)
        system = (
            "You are the Derivation AI. Start from ground-zero axioms/definitions and derive step-by-step. "
            "Every algebraic manipulation must be justified. Provide BOTH LaTeX and Unicode for each step. "
            "No handwaving, no skips."
        )
        user = f"""Topic: {topic}
Golden path: {concept.get('golden_path', [])}
Local refs: {hits}
Return JSON: {{
  "topic": "...",
  "steps":[
    {{
      "statement_unicode":"…",
      "statement_latex":"…",
      "reasoning":"…",
      "assumptions":["…","…"],
      "links_to_next":"why this sets up the next step"
    }}…
  ]
}}"""
        txt = self.llm.chat(system, user, temperature=0.1, max_tokens=4096)
        m = re.search(r"\{.*\}", txt, re.S)
        data = json.loads(m.group(0)) if m else {"topic": topic, "steps": []}
        if not self.latex_ok:
            for s in data.get("steps", []):
                s["statement_latex"] = None
        return data
