# Manim Coder (Local LLM → Code → Refine → Video)

## Quick start

```powershell
# In a clean venv with Python 3.10
pip install -r requirements.txt

# Ensure tools
manim -v
ffmpeg -version

# Ollama running locally with your chosen model
# Example sanity check (optional)
# ollama run qwen2.5:14b-instruct-q4_K_M "hello"
```

Render any topic:

```powershell
python run.py --topic "wave interference patterns"
```

The agent will:

1. Plan the visuals (beats).
2. Generate one `MainScene` with Manim CE 0.19 API.
3. Static-lint & patch bad kwargs (`numbers_to_show`, `x_axis_label`, `unit_size`), rewrite `get_graph` → `plot`, enforce Text if LaTeX is broken.
4. Quick render (low quality). On error, parse logs → Refiner.
5. HQ render. Optional ffmpeg transcode → yuv420p + +faststart for maximum compatibility.

Troubleshooting:
- LaTeX errors: Update MiKTeX via MiKTeX Console or rely on Text fallback.
- Ensure `manim` and `ffmpeg` are on PATH.
