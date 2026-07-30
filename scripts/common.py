"""Shared spine for every graphic on the profile page.

Everything here exists because of two GitHub constraints: READMEs are stripped
of <script> and of CSS. So motion has to be SMIL inside the SVG, and any
typography that isn't the viewer's default monospace has to arrive as an image
with the font embedded in it.
"""

from __future__ import annotations

import base64
import io
import os
import re
from xml.sax.saxutils import escape

from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# ---------------------------------------------------------------- palette

# Warm bronze, pulled from the skin tones and low-key lighting of the portrait
# so the graphics read as descended from the photo rather than parked next to
# it. Light values come first because GitHub's light theme is the fallback for
# anyone whose OS doesn't report a preference.
PALETTE = {
    #        light      dark
    "ink": ("#8a5a28", "#e8b478"),  # portrait strokes, live values
    "dim": ("#c9a882", "#6b4f38"),  # rails, gridlines, empty states
    "mut": ("#6e7681", "#8b949e"),  # labels, captions, units
    "emp": ("#24292f", "#f0e0cc"),  # headings, proper nouns
    "hot": ("#b5651d", "#ffcf9a"),  # the one accent, used sparingly
}

# Quiet to loud. The short ramp is for the contribution calendar, where five
# levels is all the data has.
RAMP = " .:+#@"

# The portrait needs far finer gradation than a heatmap does. These fifteen
# glyphs were chosen by rendering every printable ASCII character in
# JetBrains Mono, measuring its actual ink coverage, and picking the ones that
# land closest to evenly spaced steps from empty to solid. Picking by eye gives
# a ramp with flat spots and cliffs, and a face is mostly midtones -- that is
# exactly where a bad ramp falls apart.
PORTRAIT_RAMP = " `,:^+rcCXO&MW@"

FONT_STACK = (
    "JBMono,ui-monospace,SFMono-Regular,Menlo,Consolas,"
    "&apos;Liberation Mono&apos;,monospace"
)

# JetBrains Mono advances exactly 0.600 em at every weight. The character grids
# depend on it: a viewer falling back to a narrower monospace would see the
# portrait squeezed horizontally, which is the whole reason the font ships
# inlined rather than merely named.
ADVANCE_EM = 0.600


def style_block(font_faces: str, extra: str = "") -> str:
    """Palette as CSS classes, with a dark-theme override for each."""
    light = "".join(
        f".{k}-f{{fill:{v[0]}}}.{k}-s{{stroke:{v[0]}}}" for k, v in PALETTE.items()
    )
    dark = "".join(
        f".{k}-f{{fill:{v[1]}}}.{k}-s{{stroke:{v[1]}}}" for k, v in PALETTE.items()
    )
    return (
        f"<style>{font_faces}{light}{extra}"
        f"@media(prefers-color-scheme:dark){{{dark}}}</style>"
    )


# ---------------------------------------------------------------- font

def embed_font(chars: str, weight: str = "Regular") -> str:
    """Subset the font to `chars` and inline it as a base64 @font-face.

    Subsetting matters more than it looks: the full face is ~270 KB, and a
    README that loads six of these would be slower than the page it decorates.
    A portrait needs six glyphs; a heading needs about thirty.
    """
    path = os.path.join(FONT_DIR, f"JetBrainsMono-{weight}.ttf")
    font = TTFont(path)

    sub = Subsetter()
    sub.populate(text="".join(sorted(set(chars))) or " ")
    sub.subset(font)

    # fontTools stamps the current time into head.modified on save, which makes
    # the base64 blob -- and therefore the whole SVG -- different on every run.
    # Left alone, the daily workflow would commit all thirteen files every day
    # while claiming to commit only what changed. Pin it to the source font's
    # own creation date so the output is byte-reproducible.
    font["head"].modified = font["head"].created

    buf = io.BytesIO()
    try:
        font.flavor = "woff2"  # needs brotli
        font.save(buf)
        mime = "font/woff2"
        fmt = "woff2"
    except Exception:
        buf = io.BytesIO()
        font.flavor = "woff"  # zlib only, always available
        font.save(buf)
        mime = "font/woff"
        fmt = "woff"

    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    css_weight = 700 if weight == "Bold" else 400
    return (
        "@font-face{font-family:JBMono;font-style:normal;"
        f"font-weight:{css_weight};font-display:block;"
        f"src:url(data:{mime};base64,{b64}) format('{fmt}')}}"
    )


# ---------------------------------------------------------------- motion

def fade_in(body: str, begin: float, dur: float = 0.45) -> str:
    """Wrap `body` in a group that fades up once and stays."""
    return (
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>{body}</g>'
    )


_uid = [0]


def _next_id(prefix: str) -> str:
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def reset_ids() -> None:
    """Restart id numbering, for generators that write several files per run.

    The counter is process-global, so without this, inserting one new heading
    renumbers the clip ids in every heading after it and they all show up as
    modified. Diffs should mean something.
    """
    _uid[0] = 0


def wave(body: str, phase: float, cycle: float = 5.0, lo: float = 0.62,
         hi: float = 1.0, attr: str = "fill-opacity") -> str:
    """Wrap `body` in a brightness wave that never stops.

    This exists because of how GitHub serves these files. An SVG inside an
    <img> gets no script, no scroll position and no IntersectionObserver, so
    every entrance animation fires the moment the *page* loads -- not when the
    graphic comes into view. By the time a reader has scrolled to the stack or
    the stats, those reveals played and froze minutes ago, and the only thing
    anyone ever sees moving is whatever sits above the fold.

    So the data ink also carries a permanent slow pulse. Phase it by index
    across a row or a grid and it reads as one wave travelling through the
    graphic, which is alive whenever you happen to arrive.

    The offset is a *negative* begin rather than a delay: a positive one would
    leave the element at its base value until the animation kicked in, and the
    whole set would visibly jump at staggered moments. Negative begin starts
    every element already mid-cycle.
    """
    return (
        f'<g><animate attributeName="{attr}" values="{lo};{hi};{lo}" '
        f'keyTimes="0;0.5;1" dur="{cycle:.2f}s" begin="-{phase:.2f}s" '
        f'repeatCount="indefinite" calcMode="spline" '
        f'keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>{body}</g>'
    )


def wipe(body: str, x: float, y: float, w: float, h: float,
         begin: float, dur: float) -> str:
    """Reveal `body` by growing a clip rect left to right.

    This is the workhorse. Bars grow with it, headings rule themselves in with
    it, the portrait types itself out with it -- one primitive, so everything
    on the page shares a single sense of how motion starts and stops.
    """
    cid = _next_id("w")
    return (
        f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" '
        f'height="{h:.1f}" width="0">'
        f'<animate attributeName="width" from="0" to="{w:.1f}" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#{cid})">{body}</g>'
    )


def cursor(x0: float, x1: float, y: float, begin: float, dur: float,
           cls: str = "ink-f", w: float = 6, h: float = 12) -> str:
    """A block cursor that runs ahead of a wipe and blinks out at the end."""
    return (
        f'<rect y="{y:.1f}" width="{w}" height="{h}" class="{cls}" opacity="0">'
        f'<animate attributeName="x" from="{x0:.1f}" to="{x1:.1f}" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.75" begin="{begin:.2f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{(begin + dur):.2f}s"/>'
        f"</rect>"
    )


def grow_bar(x: float, y: float, w: float, h: float, begin: float,
             dur: float, cls: str = "ink-f", rx: float = 1.5) -> str:
    """A horizontal bar that grows from zero and stays."""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" height="{h:.1f}" width="0" rx="{rx}" '
        f'class="{cls}"><animate attributeName="width" from="0" to="{w:.1f}" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze" '
        f'calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>'
    )


def draw_line(d: str, length: float, begin: float, dur: float,
              cls: str = "dim-s", width: float = 1.0) -> str:
    """A path that draws itself via dash-offset."""
    return (
        f'<path d="{d}" class="{cls}" fill="none" stroke-width="{width}" '
        f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze" '
        f'calcMode="spline" keySplines="0.3 0.7 0.2 1" keyTimes="0;1"/></path>'
    )


def count_up(x: float, y: float, value: int, begin: float, dur: float,
             size: float, cls: str = "emp-f", anchor: str = "start",
             weight: int = 700, steps: int = 14, suffix: str = "") -> str:
    """A number that ticks up to `value`.

    SMIL can't interpolate text, so this stacks the intermediate values and
    swaps visibility. Cheap, and it only runs once.
    """
    if value <= 0:
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size:.1f}" '
            f'font-weight="{weight}" text-anchor="{anchor}">0{suffix}</text>'
        )
    steps = min(steps, max(2, value))
    frames = [round(value * ((i + 1) / steps) ** 0.75) for i in range(steps)]
    frames[-1] = value
    step_dur = dur / steps
    out = []
    for i, v in enumerate(frames):
        t0 = begin + i * step_dur
        last = i == len(frames) - 1
        hide = (
            ""
            if last
            else f'<set attributeName="opacity" to="0" begin="{(t0 + step_dur):.2f}s"/>'
        )
        out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size:.1f}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="0">'
            f"{v:,}{escape(suffix)}"
            f'<set attributeName="opacity" to="1" begin="{t0:.2f}s"/>{hide}</text>'
        )
    return "".join(out)


def label(x: float, y: float, text: str, size: float = 9,
          cls: str = "mut-f", spacing: float = 1.3,
          anchor: str = "start") -> str:
    """The small letter-spaced caps used to title every panel."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}" '
        f'letter-spacing="{spacing}" text-anchor="{anchor}">{escape(text)}</text>'
    )


def text(x: float, y: float, s: str, size: float = 11, cls: str = "mut-f",
         anchor: str = "start", weight: int | None = None,
         spacing: float | None = None) -> str:
    bits = [
        f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}"',
        f' text-anchor="{anchor}"',
    ]
    if weight:
        bits.append(f' font-weight="{weight}"')
    if spacing is not None:
        bits.append(f' letter-spacing="{spacing}"')
    bits.append(f">{escape(s)}</text>")
    return "".join(bits)


# ---------------------------------------------------------------- output

def svg(width: float, height: float, body: str, font_faces: str,
        extra_css: str = "", title: str = "") -> str:
    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{width:g}" '
        f'height="{height:g}" viewBox="0 0 {width:g} {height:g}" fill="none" '
        f'font-family="{FONT_STACK}">'
    )
    t = f"<title>{escape(title)}</title>" if title else ""
    return head + style_block(font_faces, extra_css) + t + body + "</svg>"


_FONT_BLOB = re.compile(rb"base64,[A-Za-z0-9+/=]+")


def _meaningful(data: bytes) -> bytes:
    """The part of a file worth diffing: everything but the compressed font.

    Subsetting the same glyphs twice does not reliably produce the same bytes
    -- the woff2 payload shifts by a few bytes between runs even with
    PYTHONHASHSEED pinned. Comparing raw bytes therefore reports every file as
    changed on every run, which would have the daily workflow committing all
    thirteen graphics each morning while claiming to commit only what moved.
    The markup is what carries the data, so that is what gets compared.
    """
    return _FONT_BLOB.sub(b"base64,-", data)


def write(name: str, content: str) -> bool:
    """Write only when the drawing actually changed."""
    path = os.path.join(ROOT, name)
    data = content.encode("utf-8")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            if _meaningful(fh.read()) == _meaningful(data):
                print(f"  unchanged  {name}")
                return False
    with open(path, "wb") as fh:
        fh.write(data)
    print(f"  wrote      {name}  ({len(data) / 1024:.1f} KB)")
    return True


def glyphs_in_svg(body: str) -> str:
    """Pull the text content out of assembled SVG markup.

    Lets a generator build its body first and subset to exactly what ended up
    on screen, instead of maintaining a hand-written list that silently drifts
    and leaves tofu boxes in the output.
    """
    found = re.findall(r"<text[^>]*>(.*?)</text>", body, flags=re.S)
    raw = "".join(found)
    raw = re.sub(r"<[^>]+>", "", raw)
    return (
        raw.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )
