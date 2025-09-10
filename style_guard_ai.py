import re, math


def _luminance(rgb):  # rgb 0..255
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (chan(rgb[0]), chan(rgb[1]), chan(rgb[2]))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(hex1, hex2):
    def h2rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    L1 = _luminance(h2rgb(hex1))
    L2 = _luminance(h2rgb(hex2))
    L1, L2 = max(L1, L2), min(L1, L2)
    return (L1 + 0.05) / (L2 + 0.05)


BREWER = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#666666",
]


class StyleGuard:
    def rewrite(self, code: str) -> str:
        if "Text(" in code and "color=" not in code:
            code = code.replace("Text(", f"Text(color='{BREWER[0]}', ")
        return code
