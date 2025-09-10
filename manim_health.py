import subprocess, re


def check_manim_health():
    try:
        out = subprocess.check_output(["manim", "--version"], text=True)
        m = re.search(r"Manim Community v([0-9]+\.[0-9]+)", out)
        ver = m.group(1) if m else "unknown"
    except Exception:
        ver = "unknown"

    latex_ok = False
    for exe in ("latex", "pdflatex", "xelatex", "lualatex"):
        try:
            subprocess.check_output([exe, "--version"], stderr=subprocess.STDOUT)
            latex_ok = True
            break
        except Exception:
            continue
    return latex_ok, ver
