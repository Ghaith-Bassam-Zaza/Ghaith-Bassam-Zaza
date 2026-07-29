"""Validate every generated SVG before it ships.

    python scripts/check.py

These files are assembled from string fragments and then viewed inside an
<img>, where a browser will not tell you when something is wrong -- a broken
reference just renders as nothing, and a glyph missing from the subset renders
as a tofu box that silently breaks the character grid. So the checks are here
instead.
"""

from __future__ import annotations

import base64
import glob
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"


def embedded_glyphs(source: str) -> set[str] | None:
    """Every character the inlined font subsets can actually draw."""
    chars: set[str] = set()
    found = False
    for m in re.finditer(r"base64,([A-Za-z0-9+/=]+)\)", source):
        found = True
        raw = base64.b64decode(m.group(1))
        font = TTFont(io.BytesIO(raw))
        chars |= {chr(cp) for cp in font.getBestCmap()}
    return chars if found else None


def check(path: str) -> list[str]:
    name = os.path.basename(path)
    source = open(path, encoding="utf-8").read()
    problems: list[str] = []

    try:
        root = ET.fromstring(source)
    except ET.ParseError as e:
        return [f"{name}: does not parse -- {e}"]

    # --- ids and references ------------------------------------------------
    ids: list[str] = []
    for el in root.iter():
        if el.get("id"):
            ids.append(el.get("id"))
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        problems.append(f"{name}: duplicate id(s) {sorted(dupes)}")
    known = set(ids)

    for el in root.iter():
        for attr, val in el.attrib.items():
            m = re.fullmatch(r"url\(#([^)]+)\)", val or "")
            if m and m.group(1) not in known:
                problems.append(f"{name}: {attr} points at missing #{m.group(1)}")
        href = el.get(f"{{{XLINK}}}href") or el.get("href")
        if href and href.startswith("#") and href[1:] not in known:
            problems.append(f"{name}: href points at missing {href}")

    # --- css classes -------------------------------------------------------
    style = "".join(e.text or "" for e in root.iter(f"{{{SVG}}}style"))
    defined = set(re.findall(r"\.([a-zA-Z][\w-]*)\s*\{", style))
    for el in root.iter():
        for cls in (el.get("class") or "").split():
            if cls not in defined:
                problems.append(f"{name}: class .{cls} used but never defined")

    # --- animations --------------------------------------------------------
    for tag in ("animate", "set", "animateTransform", "animateMotion"):
        for el in root.iter(f"{{{SVG}}}{tag}"):
            if tag != "animateMotion" and not el.get("attributeName"):
                problems.append(f"{name}: <{tag}> with no attributeName")
            if el.get("to") is None and el.get("values") is None and tag != "animateMotion":
                problems.append(f"{name}: <{tag}> with neither to nor values")
            if tag in ("animate", "animateTransform") and not el.get("dur"):
                problems.append(f"{name}: <{tag}> with no dur")

    for el in root.iter(f"{{{SVG}}}animateMotion"):
        if not list(el.iter(f"{{{SVG}}}mpath")):
            problems.append(f"{name}: <animateMotion> with no <mpath>")

    # --- glyph coverage ----------------------------------------------------
    available = embedded_glyphs(source)
    if available is None:
        problems.append(f"{name}: no font embedded")
    else:
        drawn: set[str] = set()
        for el in root.iter(f"{{{SVG}}}text"):
            drawn |= set("".join(el.itertext()))
        missing = {c for c in drawn if c not in available and c != " "}
        if missing:
            problems.append(
                f"{name}: {len(missing)} glyph(s) drawn but not in the subset -- "
                f"would render as tofu: {sorted(missing)}"
            )

    # --- geometry ----------------------------------------------------------
    vb = (root.get("viewBox") or "").split()
    if len(vb) == 4:
        if abs(float(vb[2]) - float(root.get("width", 0))) > 0.5:
            problems.append(f"{name}: width {root.get('width')} != viewBox {vb[2]}")
        if abs(float(vb[3]) - float(root.get("height", 0))) > 0.5:
            problems.append(f"{name}: height {root.get('height')} != viewBox {vb[3]}")
    else:
        problems.append(f"{name}: missing or malformed viewBox")

    # --- content outside the canvas ---------------------------------------
    if len(vb) == 4:
        w, h = float(vb[2]), float(vb[3])
        for el in root.iter(f"{{{SVG}}}text"):
            x = float(el.get("x", 0))
            anchor = el.get("text-anchor", "start")
            size = float(el.get("font-size", 10))
            span = len("".join(el.itertext())) * size * 0.6
            left = x if anchor == "start" else (x - span if anchor == "end" else x - span / 2)
            right = left + span
            # A 2px margin, not zero: text set flush against the boundary gets
            # its last column of pixels clipped by the renderer.
            if left < -2 or right > w - 2:
                problems.append(
                    f"{name}: text {'\"' + ''.join(el.itertext())[:24] + '\"'} "
                    f"spans {left:.0f}..{right:.0f}, needs 2px inside 0..{w:.0f}"
                )
            y = float(el.get("y", 0))
            if y < -1 or y > h + 1:
                problems.append(f"{name}: text at y={y:.0f} outside 0..{h:.0f}")

    return problems


def main() -> int:
    files = sorted(glob.glob(os.path.join(ROOT, "*.svg")))
    if not files:
        print("no SVGs found -- run the generators first")
        return 1

    total = 0
    for path in files:
        problems = check(path)
        total += len(problems)
        mark = "FAIL" if problems else "ok  "
        print(f"  {mark} {os.path.basename(path)}")
        for p in problems:
            print(f"       - {p}")

    print(f"\n{len(files)} file(s), {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
