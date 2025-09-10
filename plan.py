from llm.provider import LLM
import json, sys, time
from pathlib import Path

def _call(llm, sys_content: str, user_content: str) -> str:
    sysmsg = {"role": "system", "content": sys_content}
    user = {"role": "user", "content": user_content}
    chunks = []
    for tok in llm.chat_stream([sysmsg, user]):
        chunks.append(tok)
        # streaming to stdout for transparency
        for ch in tok:
            sys.stdout.write(ch)
            sys.stdout.flush()
    print()
    return "".join(chunks)

def _safe_json_extract(txt: str):
    # naive extraction of first {...}
    start = txt.find('{')
    end = txt.rfind('}')
    if start != -1 and end != -1 and end > start:
        snippet = txt[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None

def build_plan(topic: str, env):
    """Multi-agent planning producing JSON v2 skeleton.
    Steps: derivation -> narrative plan -> cinematic shot list (JSON v2). Falls back to minimal plan on failure.
    """
    cfg = env["cfg"]
    llm = LLM(**cfg["llm"])  # type: ignore

    # 1) Derivation
    sys.stdout.write("[Derivation] ")
    sys.stdout.flush()
    try:
        derivation = _call(
            llm,
            Path("prompts/derivation_system.md").read_text(encoding="utf-8"),
            f"Topic: {topic}. Produce derivation."
        )
    except Exception:
        derivation = "Concept Map: t (time)\nDerivation Steps: 1) Placeholder minimal derivation.\nViewer Bridge: sine wave visual."  # fallback

    # 2) Narrative Plan
    sys.stdout.write("[Narrative] ")
    sys.stdout.flush()
    try:
        narrative = _call(
            llm,
            Path("prompts/plan_of_attack_system.md").read_text(encoding="utf-8"),
            f"Using this derivation:\n{derivation}\nTarget duration 20s."
        )
    except Exception:
        narrative = "Hook: Why?; Elicitation: guess; Conflict: reveal; Resolution: concept; Transfer: other context."  # fallback

    # 3) Cinematic Planner JSON v2
    sys.stdout.write("[Planner] ")
    sys.stdout.flush()
    try:
        planner_raw = _call(
            llm,
            Path("prompts/planner_system.md").read_text(encoding="utf-8"),
            f"DERIVATION:\n{derivation}\nNARRATIVE:\n{narrative}\nProduce JSON v2 strictly. Target duration 20. topic={topic}"
        )
        planner_json = _safe_json_extract(planner_raw)
    except Exception:
        planner_raw = ""
        planner_json = None

    if not planner_json:
        # minimal fallback valid subset
        planner_json = {
            "topic": topic,
            "target_duration_s": 20,
            "global_style": {
                "resolution": "1920x1080",
                "fps": 60,
                "bg_color": "#0b0f1a",
                "palette": {
                    "primary_text": "#FFFFFF",
                    "secondary_text": "#B7C0CE",
                    "grid": "#2C3545",
                    "vars": {"f": "#FFB000"}
                },
                "latex_ok": bool(env["tools"].get("latex_ok", False))
            },
            "trackers": [{"name": "t", "value": 0.0}],
            "beats": [
                {
                    "id": "intro",
                    "t_start": 0.0,
                    "duration_s": 5.0,
                    "intent": "Hook",
                    "shots": [
                        {
                            "id": "intro-1",
                            "t_start": 0.0,
                            "duration_s": 5.0,
                            "visuals": {"type": "text", "content": topic, "font_size": 64},
                            "layout": {"region": "top_center", "collision_zones": [[0.1,0.7,0.9,0.95]]},
                            "contrast_check": True,
                            "animation": {"in": "Write", "out": "FadeOut"},
                            "transition_to_next": None,
                            "reading_time_s": 3.0
                        }
                    ]
                }
            ],
            "transitions": []
        }

    return {
        "topic": topic,
        "derivation": derivation,
        "narrative": narrative,
        "planner": planner_json
    }

