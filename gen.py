from llm.provider import LLM
from pathlib import Path
import json

def _load(path):
    return Path(path).read_text(encoding="utf-8")

def generate_code(topic: str, plan: dict, env) -> str:
    """Generate initial code using Planner 2.0 plan context.
    (Not currently called directly in run loop, but kept consistent.)"""
    cfg = env["cfg"]
    llm = LLM(**cfg["llm"])  # type: ignore
    sysmsg = {"role": "system", "content": _load("prompts/coder_system.md") + "\n\n" + _load("prompts/knowledge_base.md")}
    user_content = (
        f"Create a dynamic Manim CE 0.19 scene for: {topic}.\n"
        f"<PLAN>\n{json.dumps(plan)}\n</PLAN>\n"
        "Follow the rulebook strictly; map each beat & microbeat to animations."
    )
    user = {"role": "user", "content": user_content}
    return llm.chat([sysmsg, user])
