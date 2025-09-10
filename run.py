import argparse, json, sys, subprocess, shutil, os, time
from pathlib import Path
from rich import print, box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

from engine.preflight import preflight_check
from engine.plan import build_plan
from engine.gen import generate_code
from engine.lint import static_lint
from engine.patches import auto_patch
from engine.render import try_render
from engine.extract_errors import parse_manim_error
from engine.refine import refine_code
from engine.ffmpeg import transcode_if_needed
from engine.extract_code import extract_python_code
from engine.rule_enforcer import enforce_rulebook
from engine.preflight_rule_scan import preflight_rule_scan  # optional deep scan

console = Console()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="Prompt/topic to animate with Manim")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    # 0) Preflight environment
    env = preflight_check(args.config)
    env.setdefault("state", {})
    cfg = env["cfg"]
    console.print(Panel.fit(f"[bold cyan]Manim Coder[/] → topic: [yellow]{args.topic}[/]"))

    # 1) Build Plan (optional high-level breakdown of beats and assets)
    plan = build_plan(args.topic, env)
    console.print(Panel.fit("[bold]Plan[/]\n" + json.dumps(plan, indent=2)))

    # 2) Iterative loop: prompt -> code -> lint/patch -> render -> analyze -> refine (ReAct/Reflexion/Self-Refine inspired)
    best_code = None
    best_log = None
    for round_idx in range(1, cfg["agent"]["max_rounds"] + 1):
        console.rule(f"[bold magenta]Round {round_idx}[/]")

        # A) Generate/refine candidate scene code with streaming feedback
        from llm.provider import LLM
        llm = LLM(**cfg["llm"])  # type: ignore
        if best_code is None:
            sysmsg_path = Path("prompts/coder_system.md")
            kb_path = Path("prompts/knowledge_base.md")
            sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8") + "\n\n" + kb_path.read_text(encoding="utf-8")}
            user = {"role": "user", "content": f"Create a dynamic Manim CE 0.19 scene for: {args.topic}.\nFollow the rulebook strictly."}
            console.print("[dim]LLM: generating scene (live)…[/]")
            acc = ""
            for tok in llm.chat_stream([sysmsg, user]):
                acc += tok
                for ch in tok:
                    sys.stdout.write(ch)
                    sys.stdout.flush()
            print()  # newline after stream
            code = extract_python_code(acc)
        else:
            sysmsg_path = Path("prompts/refiner_system.md")
            kb_path = Path("prompts/knowledge_base.md")
            sysmsg = {"role": "system", "content": sysmsg_path.read_text(encoding="utf-8") + "\n\n" + kb_path.read_text(encoding="utf-8")}
            user = {"role": "user", "content": f"Fix this Manim file based on the error summary.\n\n<ERRORS>\n{best_log}\n</ERRORS>\n\n<CODE>\n{best_code}\n</CODE>"}
            console.print("[dim]LLM: refining scene based on errors (live)…[/]")
            acc = ""
            for tok in llm.chat_stream([sysmsg, user]):
                acc += tok
                for ch in tok:
                    sys.stdout.write(ch)
                    sys.stdout.flush()
            print()
            code = extract_python_code(acc)

        # B0) Strict rule enforcement (AST + banned kwargs) before static lint
        code, rule_report = enforce_rulebook(code, env)
        if rule_report.get("changed") or rule_report.get("messages"):
            console.print(Panel.fit("[blue]Rule Enforcement[/]\n" + "\n".join(rule_report.get("messages", []))))

        # B0.5) Deep preflight rule scan (advisory)
        scan = preflight_rule_scan(code, env)
        if scan["issues"]:
            console.print(Panel.fit("[cyan]Preflight Scan[/]\n" + "\n".join(scan["issues"])))

        # B1) Static lints (block/replace API footguns before we even run)
        code, lint_report = static_lint(code, env)
        if lint_report["blocked"]:
            console.print(Panel.fit("[yellow]Static guard blocked risky patterns and applied fixes.[/]\n" + json.dumps(lint_report, indent=2)))

        # C) Autopatches (version-compat shims & fallbacks: Text over MathTex if LaTeX not healthy, etc.)
        code, patch_report = auto_patch(code, env)
        if patch_report["changed"]:
            console.print(Panel.fit("[cyan]Auto-patches applied.[/]\n" + json.dumps(patch_report, indent=2)))

        # D) Try rendering (low quality first for speed)
        console.print("[dim]Rendering (quick)...[/]")
        ok, paths, log = try_render(code, env, quick=True)
        if not ok:
            # Parse error log and feed back to refiner next round
            err = parse_manim_error(log)
            # detect LaTeX failure to force future Text fallback
            if ("latex" in err["summary"].lower()) or ("latex" in log.lower()):
                env["state"]["force_no_latex"] = True
            best_code, best_log = code, err
            console.print(Panel.fit("[red]Render failed. Feeding errors back to the LLM refiner.[/]\n" + err["summary"]))
            continue

        # E) Final render (HQ) + ffmpeg transcode
        console.print("[green]Low-quality render succeeded. Producing final HQ video...[/]")
        ok2, paths2, log2 = try_render(code, env, quick=False)
        if not ok2:
            err2 = parse_manim_error(log2)
            if ("latex" in err2["summary"].lower()) or ("latex" in log2.lower()):
                env["state"]["force_no_latex"] = True
            best_code, best_log = code, err2
            console.print(Panel.fit("[yellow]HQ render failed. Returning to refiner...[/]\n" + err2["summary"]))
            continue

        final_mp4 = paths2["video"]
        if env["cfg"]["ffmpeg"]["enable"]:
            final_mp4 = transcode_if_needed(final_mp4, env)

        console.print(Panel.fit(f"[bold green]DONE[/] → {final_mp4}"))
        return 0

    # If loop exhausted
    console.print(Panel.fit("[red]Failed to converge within max rounds.[/]\nSee last error in logs."))
    return 1

if __name__ == "__main__":
    sys.exit(main())
