import subprocess, tempfile, os, shlex, sys
from pathlib import Path

def write_scene(code: str, dirpath: Path) -> Path:
    scene_path = dirpath / "scene.py"
    scene_path.write_text(code, encoding="utf-8")
    return scene_path

def manim_cmd(scene_path: Path, scene_class: str, quality: str, fps: int, outdir: Path):
    # Map to manim quality flags: -ql, -qm, -qh, -qk
    qmap = {"low": "l", "l": "l", "medium": "m", "m": "m", "high": "h", "h": "h", "k": "k", "ultra": "k"}
    qflag = qmap.get(str(quality).lower(), "m")
    return [
        sys.executable,
        "-m",
        "manim",
        f"-q{qflag}",
        "--fps", str(fps),
        "--media_dir", str(outdir),
        str(scene_path),
        scene_class,
    ]

def run_manim(cmd: list) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        ok = p.returncode == 0
        log = p.stdout + "\n" + p.stderr
        return ok, log
    except subprocess.TimeoutExpired as e:
        return False, "Timeout: " + str(e)

def run_manim_stream(cmd: list, on_text) -> tuple[bool, str]:
    """Run manim and stream combined stdout+stderr via callback on_text(str)."""
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        log_parts = []
        assert p.stdout is not None
        for line in p.stdout:
            log_parts.append(line)
            try:
                on_text(line)
            except Exception:
                pass
        p.wait(timeout=900)
        ok = p.returncode == 0
        return ok, "".join(log_parts)
    except subprocess.TimeoutExpired as e:
        return False, "Timeout: " + str(e)
