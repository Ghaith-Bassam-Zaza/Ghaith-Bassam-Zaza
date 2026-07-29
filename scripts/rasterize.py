"""Render a generated SVG to PNG in its settled state (dev tool, not shipped).

Every graphic here starts hidden and animates in, so a plain rasteriser samples
t=0 and produces a blank image. This walks the tree, applies each <animate> and
<set> as if it had already run to completion, strips the timing, and renders
that. It is how you check tone and layout without a browser.

    python scripts/rasterize.py portrait.svg 460 dark
    python scripts/rasterize.py --all
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

import cairosvg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

BG = {"dark": "#0d1117", "light": "#ffffff"}


def settle(el: ET.Element) -> None:
    """Apply animations to their final value, depth first."""
    for child in list(el):
        settle(child)

    for c in list(el):
        if c.tag in (f"{{{SVG_NS}}}animate", f"{{{SVG_NS}}}set"):
            name, to = c.get("attributeName"), c.get("to")
            if name and to is not None:
                el.set(name, to)
            el.remove(c)
        elif c.tag == f"{{{SVG_NS}}}animateTransform":
            # Must be applied, not merely dropped: the element's own transform
            # attribute holds the *starting* offset, so stripping the animation
            # renders every element at the position it flies in from.
            to, kind = c.get("to"), c.get("type", "translate")
            if to is not None:
                el.set("transform", f"{kind}({to})")
            el.remove(c)
        elif c.tag == f"{{{SVG_NS}}}animateMotion":
            el.remove(c)


def theme_css(source: str, theme: str) -> str:
    """Promote the dark-theme block to top level when rendering dark."""
    if theme != "dark":
        return source
    start = source.find("@media(prefers-color-scheme:dark){")
    if start == -1:
        return source
    open_brace = source.index("{", start + len("@media(prefers-color-scheme:dark"))
    depth, i = 0, open_brace
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    inner = source[open_brace + 1 : i]
    return source[:start] + inner + source[i + 1 :]


def render(name: str, width: int, theme: str = "dark") -> str:
    path = os.path.join(ROOT, name)
    source = theme_css(open(path, encoding="utf-8").read(), theme)
    tree = ET.fromstring(source)
    settle(tree)
    out = os.path.join(ROOT, "_render", f"{os.path.splitext(name)[0]}.{theme}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cairosvg.svg2png(
        bytestring=ET.tostring(tree, encoding="utf-8"),
        write_to=out,
        output_width=width,
        background_color=BG[theme],
    )
    print(f"  {out}")
    return out


if __name__ == "__main__":
    if "--all" in sys.argv:
        from preview import PANELS

        for name, w in PANELS:
            if os.path.exists(os.path.join(ROOT, name)):
                for theme in ("dark", "light"):
                    render(name, w, theme)
    else:
        render(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "dark")
