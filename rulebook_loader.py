from pathlib import Path


def load_rulebooks(root: Path):
    rb = ""
    rb_yaml = ""
    for p in [
        root / "knowledge/zero_tolerance_rulebook.md",
        root / "knowledge_base/zero_tolerance_rulebook.md",
        root / "prompts/knowledge_base.md",
    ]:
        if p.exists():
            rb += p.read_text(encoding="utf-8") + "\n\n"

    y = root / "knowledge/manim_rulebook.yaml"
    if y.exists():
        rb_yaml = y.read_text(encoding="utf-8")
    return rb, rb_yaml
