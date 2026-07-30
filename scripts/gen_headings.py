"""Section headings as SVG images.

GitHub strips CSS from READMEs, so a heading written as markdown gets the
viewer's default font and nothing else. Drawing them as images is the only way
to put the page's own typeface on the page, which is the same reason the
reference profile does it.

    python scripts/gen_headings.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

W = 620
H = 30
BASE = 19

SECTIONS = [
    ("about", "about"),
    ("work", "work"),
    ("stack", "stack"),
    ("projects", "projects"),
    ("pipeline", "how i build"),
    ("stats", "stats"),
]


def build(text: str) -> str:
    C.reset_ids()
    parts = []

    # A small square that snaps in first. It gives the rule something to start
    # from, so the heading reads as one gesture rather than two. It also keeps a
    # slow pulse: the reveal plays at page load, so by the time a reader has
    # scrolled this far it is long finished, and a heading with a breathing
    # marker is the cheapest way to show the page is not a screenshot.
    parts.append(
        C.wave(
            f'<rect x="0" y="{BASE - 7}" width="0" height="8" class="hot-f">'
            f'<animate attributeName="width" from="0" to="8" begin="0.00s" '
            f'dur="0.22s" fill="freeze"/></rect>',
            phase=0.0,
            cycle=3.6,
            lo=0.30,
        )
    )

    label = C.text(18, BASE, text, size=11.5, cls="emp-f", weight=700, spacing=2.4)
    text_w = len(text) * (11.5 * C.ADVANCE_EM + 2.4)
    parts.append(C.wipe(label, 18, 0, text_w, H, 0.16, 0.10 + 0.032 * len(text)))

    rule_x = 18 + text_w + 12
    parts.append(
        C.draw_line(
            f"M{rule_x:.1f} {BASE - 4} H{W}", W - rule_x, 0.30, 0.75, "dim-s", 1.0
        )
    )

    body = "".join(parts)
    return C.svg(W, H, body, C.embed_font(C.glyphs_in_svg(body), "Bold"), title=text)


if __name__ == "__main__":
    for slug, text in SECTIONS:
        C.write(f"hd-{slug}.svg", build(text))
