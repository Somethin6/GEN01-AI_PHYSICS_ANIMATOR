import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenderResult:
    ok: bool
    output_path: str | None
    log: str


def try_render(scene_path: Path, quick: bool = True, media_dir: str = "out_super") -> RenderResult:
    scene = "MainScene"
    quality = "-pql" if quick else "-pqh"
    cmd = [
        "manim",
        quality,
        "-o",
        "scene",
        "--media_dir",
        media_dir,
        str(scene_path),
        scene,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        mp4 = None
        for line in out.splitlines():
            if line.strip().endswith(".mp4"):
                mp4 = line.strip()
        return RenderResult(True, mp4, out)
    except subprocess.CalledProcessError as e:  # pragma: no cover
        return RenderResult(False, None, e.output or "")
