import re

def extract_python_code(text: str) -> str:
    """
    Extract Python code from an LLM response that may contain Markdown, prose,
    and fenced code blocks. Preference order:
    1) The first ```python fenced block.
    2) The first triple-backticked block of any language.
    3) Heuristic: from the first occurrence of 'from manim import' or 'class MainScene' to the end.
    As a last resort, return the original text.
    Also strips any lingering fences.
    """
    if not text:
        return text

    # 1) ```python fenced block
    m = re.search(r"```python\s*\n(.*?)(?:\n)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        code = m.group(1)
        return _strip_fences(code)

    # 2) any fenced block
    m = re.search(r"```\s*\n(.*?)(?:\n)```", text, flags=re.DOTALL)
    if m:
        code = m.group(1)
        return _strip_fences(code)

    # 3) heuristic from 'from manim import' or 'class MainScene'
    idx = -1
    for key in ["from manim import", "import manim", "class MainScene", "class  MainScene"]:
        idx = text.find(key)
        if idx != -1:
            break
    if idx != -1:
        return _strip_fences(text[idx:])

    return _strip_fences(text)

def _strip_fences(s: str) -> str:
    # remove stray backtick fences and leading/trailing whitespace
    s = re.sub(r"^\s*```[a-zA-Z0-9_-]*\s*$", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*```\s*$", "", s, flags=re.MULTILINE)
    return s.strip()
