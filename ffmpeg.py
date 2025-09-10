import subprocess, shutil
from pathlib import Path

def transcode_if_needed(in_mp4: str, env) -> str:
    if not env["tools"]["ffmpeg"]:
        return in_mp4
    cfg = env["cfg"]["ffmpeg"]
    out_path = str(Path(in_mp4).with_suffix(".final.mp4"))

    ffmpeg_cmd = env["tools"].get("ffmpeg_cmd", "ffmpeg")
    args = [
        ffmpeg_cmd, "-y", "-i", in_mp4,
        "-vf", f"fps={env['cfg']['manim']['fps']},scale={env['cfg']['ffmpeg']['scale_width']}:-2:flags=lanczos",
        "-c:v", "libx264",
        "-preset", cfg["preset"],
        "-crf", str(cfg["crf"]),
        "-pix_fmt", cfg["pix_fmt"]
    ]
    if cfg["movflags_faststart"]:
        args += ["-movflags", "+faststart"]
    args += ["-c:a", "aac", "-b:a", "192k", out_path]

    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        return in_mp4
    return out_path
