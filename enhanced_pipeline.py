"""
Enhanced multi-stage pipeline with derivation → plan-of-attack → detailed planner → coder flow
"""
import json
import sys
from pathlib import Path
from rich import print
from rich.console import Console
from rich.panel import Panel

from llm.provider import LLM

console = Console()

def run_derivation_stage(topic: str, env) -> str:
    """Stage 1: Deep mathematical derivation"""
    console.print("[bold cyan]Stage 1: Derivation AI[/bold cyan]")
    
    llm = LLM(**env["cfg"]["llm"])
    sysmsg_path = Path("prompts/derivation_system.md")
    sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8")}
    user = {"role": "user", "content": f"Derive the mathematical foundations for: {topic}"}
    
    console.print("[dim]Generating mathematical derivation...[/]")
    response = llm.chat([sysmsg, user])
    
    # Save derivation for next stage
    derivation_path = Path("temp/derivation.md")
    derivation_path.parent.mkdir(exist_ok=True)
    derivation_path.write_text(response, encoding="utf-8")
    
    console.print(Panel.fit(f"[green]Derivation completed[/]\nSaved to: {derivation_path}"))
    return response

def run_plan_of_attack_stage(topic: str, derivation: str, env) -> str:
    """Stage 2: Veritasium-style narrative arc"""
    console.print("[bold cyan]Stage 2: Plan-of-Attack AI[/bold cyan]")
    
    llm = LLM(**env["cfg"]["llm"])
    sysmsg_path = Path("prompts/plan_of_attack_system.md")
    sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8")}
    
    user_content = f"""Topic: {topic}

Derivation Document:
{derivation}

Target Duration: {env["cfg"]["planning"]["target_duration_s"]} seconds

Create a Veritasium-style narrative arc that elicits and resolves misconceptions."""
    
    user = {"role": "user", "content": user_content}
    
    console.print("[dim]Creating narrative plan...[/]")
    response = llm.chat([sysmsg, user])
    
    # Save plan for next stage
    plan_path = Path("temp/plan_of_attack.md")
    plan_path.write_text(response, encoding="utf-8")
    
    console.print(Panel.fit(f"[green]Plan-of-Attack completed[/]\nSaved to: {plan_path}"))
    return response

def run_detailed_planner_stage(topic: str, derivation: str, plan_of_attack: str, env) -> dict:
    """Stage 3: Ultra-detailed shot-by-shot planner"""
    console.print("[bold cyan]Stage 3: Detailed Planner AI[/bold cyan]")
    
    llm = LLM(**env["cfg"]["llm"])
    sysmsg_path = Path("prompts/planner_system.md")
    sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8")}
    
    user_content = f"""Topic: {topic}

Derivation Document:
{derivation}

Plan-of-Attack:
{plan_of_attack}

LaTeX Status: {"healthy" if env["tools"]["latex_ok"] else "unhealthy - use Text only"}

Create a detailed JSON planner following schema v2 with collision zones, tracker mapping, and precise timing."""
    
    user = {"role": "user", "content": user_content}
    
    console.print("[dim]Generating detailed shot list...[/]")
    response = llm.chat([sysmsg, user])
    
    try:
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in planner response")
        
        json_str = response[json_start:json_end]
        planner_data = json.loads(json_str)
        
        # Validate against schema
        validate_planner_schema(planner_data)
        
        # Save detailed plan
        plan_path = Path("temp/detailed_plan.json")
        plan_path.write_text(json.dumps(planner_data, indent=2), encoding="utf-8")
        
        console.print(Panel.fit(f"[green]Detailed Plan completed[/]\nSaved to: {plan_path}"))
        return planner_data
        
    except (json.JSONDecodeError, ValueError) as e:
        console.print(Panel.fit(f"[red]Planner JSON Error[/]\n{str(e)}\n\nRaw response:\n{response}"))
        # Return minimal fallback plan
        return create_fallback_plan(topic, env)

def validate_planner_schema(data: dict):
    """Validate planner data against schema v2"""
    required_fields = ["topic", "target_duration_s", "global_style", "trackers", "beats", "transitions"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate collision zones don't overlap
    for beat in data.get("beats", []):
        for shot in beat.get("shots", []):
            zones = shot.get("layout", {}).get("collision_zones", [])
            for i, zone1 in enumerate(zones):
                for j, zone2 in enumerate(zones[i+1:], i+1):
                    if boxes_overlap(zone1, zone2):
                        raise ValueError(f"Collision zones overlap in shot {shot['id']}")

def boxes_overlap(box1, box2):
    """Check if two normalized bounding boxes overlap"""
    x1_left, y1_bottom, x1_right, y1_top = box1
    x2_left, y2_bottom, x2_right, y2_top = box2
    
    return not (x1_right <= x2_left or x2_right <= x1_left or 
                y1_top <= y2_bottom or y2_top <= y1_bottom)

def create_fallback_plan(topic: str, env) -> dict:
    """Create a minimal fallback plan if detailed planning fails"""
    duration = env["cfg"]["planning"]["target_duration_s"]
    return {
        "topic": topic,
        "target_duration_s": duration,
        "global_style": {
            "resolution": "1920x1080",
            "fps": 60,
            "bg_color": "#0b0f1a",
            "palette": {
                "primary_text": "#FFFFFF",
                "secondary_text": "#B7C0CE",
                "grid": "#2C3545",
                "vars": {"E": "#FFB000", "B": "#4EA5FF"}
            },
            "latex_ok": env["tools"]["latex_ok"]
        },
        "trackers": [{"name": "t", "value": 0.0}],
        "beats": [{
            "id": "main",
            "t_start": 0.0,
            "duration_s": duration,
            "intent": "Educational visualization",
            "question": f"How does {topic} work?",
            "shots": [{
                "id": "main-shot",
                "t_start": 0.0,
                "duration_s": duration,
                "visuals": {"type": "diagram", "content": topic},
                "layout": {
                    "region": "center",
                    "collision_zones": [[0.1, 0.1, 0.9, 0.9]]
                },
                "animation": {"in": "FadeIn", "out": "FadeOut"}
            }],
            "misconception_counter": "Standard educational approach"
        }],
        "transitions": []
    }

def run_enhanced_coder_stage(planner_data: dict, env) -> str:
    """Stage 4: Generate code from detailed plan"""
    console.print("[bold cyan]Stage 4: Enhanced Coder AI[/bold cyan]")
    
    llm = LLM(**env["cfg"]["llm"])
    sysmsg_path = Path("prompts/coder_system.md")
    kb_path = Path("knowledge/zero_tolerance_rulebook.md")
    
    sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8") + "\n\n" + kb_path.read_text(encoding="utf-8")}
    
    user_content = f"""Generate Manim CE 0.19 code from this detailed plan:

{json.dumps(planner_data, indent=2)}

CRITICAL REQUIREMENTS:
- Respect collision_zones by using arrange/next_to/to_edge with calculated buff
- Use ValueTracker + always_redraw for all dynamic elements
- LaTeX Status: {"healthy - use MathTex" if planner_data["global_style"]["latex_ok"] else "unhealthy - use Text only"}
- Implement ALL shots in the timeline with proper transitions
- Follow palette assignments strictly"""
    
    user = {"role": "user", "content": user_content}
    
    console.print("[dim]Generating collision-aware Manim code...[/]")
    response = llm.chat([sysmsg, user])
    
    # Extract Python code
    code_start = response.find('```python')
    code_end = response.find('```', code_start + 9)
    
    if code_start != -1 and code_end != -1:
        code = response[code_start + 9:code_end].strip()
    else:
        # Fallback: assume entire response is code
        code = response.strip()
    
    console.print(Panel.fit("[green]Enhanced code generation completed[/]"))
    return code

def run_enhanced_pipeline(topic: str, env) -> str:
    """Run the complete enhanced pipeline"""
    console.print(Panel.fit(f"[bold magenta]Enhanced Pipeline: {topic}[/bold magenta]"))
    
    # Create temp directory
    Path("temp").mkdir(exist_ok=True)
    
    # Stage 1: Derivation
    derivation = run_derivation_stage(topic, env)
    
    # Stage 2: Plan-of-Attack
    plan_of_attack = run_plan_of_attack_stage(topic, derivation, env)
    
    # Stage 3: Detailed Planner
    planner_data = run_detailed_planner_stage(topic, derivation, plan_of_attack, env)
    
    # Stage 4: Enhanced Coder
    code = run_enhanced_coder_stage(planner_data, env)
    
    console.print(Panel.fit("[bold green]Enhanced pipeline completed[/bold green]"))
    return code
