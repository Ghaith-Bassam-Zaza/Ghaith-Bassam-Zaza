"""me.png -> portrait.svg

A photograph pushed through a character ramp, then typed out row by row.

The source is a very low-key portrait: 92% of its pixels sit in the darkest
eighth of the range. Mapped naively it produces an almost blank field with a
face faintly floating in it, so the tone handling below is doing most of the
work. The numbers were derived by measuring the actual file, not guessed --
re-run this script if the photo is ever replaced, and expect to retune FLOOR.
"""

from __future__ import annotations

import sys
import numpy as np
from PIL import Image, ImageFilter
from xml.sax.saxutils import escape

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

SRC = "me.png"
OUT = "portrait.svg"

# Framing. Measured: the lit face occupies x 290-586, y 187-650 in the source;
# below that the suit falls under the noise floor entirely, and the sparkle
# watermark sits in the bottom-right corner outside this box.
BOX = (250, 172, 672, 662)
COLS = 86

# The background is not pure black -- it carries a soft gradient that peaks
# around 29 on the right side. Anything below FLOOR is treated as empty, which
# is what stops that gradient from rendering as a wedge of stray dots.
FLOOR = 25
HI_PCT = 99.0
# Slightly under 1.0: lifts the midtones that carry the modelling of the cheek
# and jaw without pushing the forehead highlight into a solid block.
GAMMA = 0.9

FONT_SIZE = 12.9
LINE_H = 14.0
PAD = 14.0
CELL_ASPECT = FONT_SIZE * C.ADVANCE_EM / LINE_H  # 0.553

# One flat colour for the whole portrait. Tone is carried entirely by glyph
# density, and adding a brightness ramp on top of it double-encodes: highlights
# blow out into solid blocks and the shadow gradient disappears. The face has
# to be built out of character weight alone.
INK = "ink-f"

PER_ROW = 0.085


def quantize() -> list[list[int]]:
    im = Image.open(SRC).convert("L").crop(BOX)
    im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=90, threshold=2))
    w, h = im.size
    rows = int(round(COLS * CELL_ASPECT * h / w))
    a = np.asarray(im.resize((COLS, rows), Image.LANCZOS), dtype=float)

    lit = a[a > FLOOR]
    hi = np.percentile(lit, HI_PCT) if lit.size else 255.0
    norm = np.clip((a - FLOOR) / max(hi - FLOOR, 1e-6), 0, 1) ** GAMMA
    top = len(C.PORTRAIT_RAMP) - 1
    g = np.clip((norm * top).round().astype(int), 0, top)

    return despeckle(g).tolist()


def despeckle(g: np.ndarray, min_area: int = 26) -> np.ndarray:
    """Drop small isolated blobs of faint ink.

    What survives the floor is not only the subject: the background gradient
    peaks around 29 on the right, and grain elsewhere clears it in patches.
    Those land as loose specks that read as dirt on the page. Anything faint
    and smaller than min_area cells is not part of a face.
    """
    faint = (g > 0) & (g <= 2)
    seen = np.zeros_like(g, dtype=bool)
    h, w = g.shape
    for y in range(h):
        for x in range(w):
            if not faint[y, x] or seen[y, x]:
                continue
            stack, blob = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                blob.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] \
                                and g[ny, nx] > 0:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            # A blob touching solid ink is a shadow edge of the subject; only
            # blobs that are faint all the way through get removed.
            if len(blob) < min_area and all(g[p] <= 2 for p in blob):
                for p in blob:
                    g[p] = 0
    return g


def row_runs(levels: list[int]) -> list[tuple[int, str]]:
    """Split a row into (start_col, text) runs of contiguous ink.

    Blank stretches are dropped rather than emitted as spaces: they carry no
    ink, and leaving them out roughly halves the file.
    """
    runs = []
    col = 0
    while col < len(levels):
        if levels[col] == 0:
            col += 1
            continue
        start = col
        chars = []
        while col < len(levels) and levels[col] > 0:
            chars.append(C.PORTRAIT_RAMP[levels[col]])
            col += 1
        runs.append((start, "".join(chars)))
    return runs


def build() -> str:
    grid = quantize()
    adv = FONT_SIZE * C.ADVANCE_EM
    width = PAD * 2 + COLS * adv
    height = PAD * 2 + len(grid) * LINE_H

    widest = max((sum(len(t) for _, t in row_runs(r)) for r in grid), default=1) or 1
    parts = []
    t = 0.0
    for i, levels in enumerate(grid):
        runs = row_runs(levels)
        if not runs:
            t += PER_ROW * 0.25
            continue
        y = PAD + i * LINE_H
        last_col = max(s + len(txt) for s, txt in runs)
        ink = sum(len(txt) for _, txt in runs)
        dur = max(PER_ROW * 0.35, PER_ROW * (ink / widest))

        body = "".join(
            f'<text xml:space="preserve" x="{PAD + s * adv:.1f}" '
            f'y="{y + FONT_SIZE * 0.85:.1f}" class="{INK}" '
            f'font-size="{FONT_SIZE}">{escape(txt)}</text>'
            for s, txt in runs
        )
        end_x = PAD + last_col * adv
        parts.append(C.wipe(body, PAD, y, end_x - PAD, LINE_H + 1, t, dur))
        parts.append(
            C.cursor(PAD, end_x, y + 1.5, t, dur, "hot-f", w=adv, h=LINE_H * 0.78)
        )
        t += dur

    print(f"  grid {COLS}x{len(grid)}  reveal {t:.1f}s")
    face = C.embed_font(C.PORTRAIT_RAMP)
    return C.svg(width, height, "".join(parts), face, title="Ghaith Zaza")


if __name__ == "__main__":
    C.write(OUT, build())
