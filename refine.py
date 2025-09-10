from llm.provider import LLM
from pathlib import Path
import json

def _load(path):
    return Path(path).read_text(encoding="utf-8")

def refine_code(prev_code: str, error_summary: dict, plan: dict, env) -> str:
    cfg = env["cfg"]
    llm = LLM(**cfg["llm"])  # type: ignore
    sysmsg = {"role": "system", "content": _load("prompts/refiner_system.md") + "\n\n" + _load("prompts/knowledge_base.md")}
    user_content = (
        "Refine this Manim CE 0.19 scene using error summary + immutable Planner 2.0 JSON.\n"
        f"<PLAN>\n{json.dumps(plan)}\n</PLAN>\n"
        f"<ERRORS>\n{error_summary}\n</ERRORS>\n"
        f"<CODE>\n{prev_code}\n</CODE>"
    )
    user = {"role": "user", "content": user_content}
    return llm.chat([sysmsg, user])
