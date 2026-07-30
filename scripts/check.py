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

    # Spline timing arity. Browsers respond to a mismatch by discarding the
    # whole animation rather than complaining, so the graphic just sits there --
    # which is the precise bug the looping waves exist to fix. Worth asserting.
    for tag in ("animate", "animateTransform"):
        for el in root.iter(f"{{{SVG}}}{tag}"):
            if el.get("calcMode") != "spline":
                continue
            splines = [s for s in (el.get("keySplines") or "").split(";") if s.strip()]
            times = [t for t in (el.get("keyTimes") or "").split(";") if t.strip()]
            vals = [v for v in (el.get("values") or "").split(";") if v.strip()]
            stops = len(vals) or len(times)
            if not splines:
                problems.append(f"{name}: calcMode=spline with no keySplines")
            elif stops and len(splines) != stops - 1:
                problems.append(
                    f"{name}: {len(splines)} keySplines for {stops} stops "
                    f"(needs {stops - 1}) -- browsers will drop this animation"
                )
            for s in splines:
                nums = s.split()
                if len(nums) != 4 or not all(0.0 <= float(n) <= 1.0 for n in nums):
                    problems.append(
                        f"{name}: keySplines segment '{s.strip()}' is not four "
                        f"values in 0..1"
                    )

    # A repeating animation with fill="freeze" is a contradiction: it holds the
    # final value and stops, so the loop never visibly runs.
    for el in root.iter(f"{{{SVG}}}animate"):
        if el.get("repeatCount") == "indefinite" and el.get("fill") == "freeze":
            problems.append(
                f"{name}: <animate {el.get('attributeName')}> repeats "
                f"indefinitely but freezes -- it will play once and stop"
            )

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


def check_readme() -> list[str]:
    """README references and the files on disk have to agree.

    A renamed or deleted graphic leaves a broken image on the profile, and
    an orphaned SVG is dead weight in the repo. Neither shows up in the
    per-file checks because both files are individually fine.
    """
    path = os.path.join(ROOT, "README.md")
    if not os.path.exists(path):
        return ["README.md missing"]

    source = open(path, encoding="utf-8").read()
    referenced = set(re.findall(r'src="\./([^"]+\.svg)"', source))
    on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.svg"))}

    problems = []
    for name in sorted(referenced - on_disk):
        problems.append(f"README references {name}, which does not exist")
    for name in sorted(on_disk - referenced):
        problems.append(f"{name} exists but nothing in the README shows it")
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

    readme = check_readme()
    total += len(readme)
    print(f"  {'FAIL' if readme else 'ok  '} README.md")
    for p in readme:
        print(f"       - {p}")

    print(f"\n{len(files)} file(s), {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
