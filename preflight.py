import yaml, shutil, subprocess, os, sys, re
from pathlib import Path
from rich import print

def _has(cmd):
    return shutil.which(cmd) is not None

def _latex_healthy():
    """Attempt robust LaTeX health check via manim checkhealth first, fallback to latex --version."""
    # Try manim checkhealth for authoritative status
    try:
        ch = subprocess.run(["manim", "checkhealth"], capture_output=True, text=True, timeout=15)
        if ch.returncode == 0:
            # Parse for LaTeX OK marker
            if re.search(r"LaTeX\s*:\s*OK", ch.stdout, re.IGNORECASE):
                return True
            # If explicitly shows failure, return False
            if re.search(r"LaTeX\s*:\s*NOT\s*OK", ch.stdout, re.IGNORECASE):
                return False
        # Fallback: raw latex binary presence
    except Exception:
        pass
    try:
        out = subprocess.run(["latex", "--version"], capture_output=True, text=True, timeout=5)
        return out.returncode == 0
    except Exception:
        return False

def preflight_check(cfg_path: str):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Detect tools
    has_ffmpeg = _has("ffmpeg")
    # Prefer Python import check (works inside venv)
    try:
        import manim  # type: ignore
        has_manim = True
    except Exception:
        has_manim = _has("manim")
    latex_ok   = _latex_healthy()

    # Windows-friendly: check for local bundled ffmpeg in workspace (../ffmpeg/bin/ffmpeg.exe)
    ffmpeg_cmd = "ffmpeg"
    local_ffmpeg = Path.cwd() / "ffmpeg" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_ffmpeg.exists():
        has_ffmpeg = True
        ffmpeg_cmd = str(local_ffmpeg)

    if not has_manim:
        raise SystemExit("Manim not found. Install dependencies in this environment (pip install -r requirements.txt).")
    if cfg["latex"]["require_healthy"] and not latex_ok:
        raise SystemExit("LaTeX is required by config but not healthy. Open MiKTeX Console and update or switch config.")

    env = {
        "cfg": cfg,
        "tools": {
            "ffmpeg": has_ffmpeg,
            "ffmpeg_cmd": ffmpeg_cmd,
            "latex_ok": latex_ok
        }
    }
    return env
