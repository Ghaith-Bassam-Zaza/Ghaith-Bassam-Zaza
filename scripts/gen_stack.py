"""stack.svg -- the toolkit as a row of meters, grouped and weighted.

Two earlier attempts are worth recording, because both failed for reasons that
are easy to repeat.

The first drew each tool linked back to the heaviest item in its group. The
links carried no meaning a reader could recover, so it read as random strokes
with the labels bunched in the middle.

The second dropped the links for a clean dot-and-label grid. Legible, and
completely inert -- it looked like a text list with bullets, because that is
essentially what it was.

The third filled a rounded box behind each name in proportion to its weight.
That put a hard vertical step through the middle of words, which reads as a
paint failure rather than as a value.

So: each tool sits above its own level meter, where the weight is drawn plainly
and can't be mistaken for a glitch. The fills carry a permanent travelling wave,
because an entrance animation is invisible to anyone who arrives by scrolling --
see `common.wave`.

    python scripts/gen_stack.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

W = 620
FS = 9.4
LABEL_X = 62          # right edge of the group-name column
ITEMS_X = 74          # where the chips start
CHIP_H = 20.0      # text plus meter
CHIP_GAP = 17.0    # between tools on a line
LINE_GAP = 9.0
TOP = 10.0

# How long one full brightness cycle takes, and how much of it separates
# neighbouring chips. Slow and closely phased reads as a wave rolling through
# the panel; fast or widely phased reads as flickering.
CYCLE = 5.2
PHASE_STEP = 0.11

# (group, [(tool, weight 1-5)]). 5 is "every week"; 2 is "I know it, it isn't
# what I'd reach for". Hand-set on purpose -- this is a claim, not a metric.
GROUPS: list[tuple[str, list[tuple[str, int]]]] = [
    ("agents", [
        ("langgraph", 5), ("function calling", 5), ("langchain", 4),
        ("autogen", 3), ("semantic kernel", 3), ("n8n", 2),
    ]),
    ("llm", [
        ("claude", 5), ("rag", 5), ("prompt engineering", 4), ("gpt-4", 4),
        ("fine-tuning", 3),
    ]),
    ("ml", [
        ("pytorch", 4), ("tensorflow", 3), ("scikit-learn", 3),
        ("chronos-bolt", 3), ("cryptobert", 2), ("opencv", 2),
    ]),
    ("backend", [
        ("python", 5), ("fastapi", 5), ("flask", 3), ("django", 2),
        ("spring boot", 2),
    ]),
    ("data", [
        ("postgres", 5), ("pgvector", 4), ("redis", 4), ("timescaledb", 3),
        ("pinecone", 3), ("mongodb", 2),
    ]),
    ("web", [
        ("next.js", 4), ("react", 4), ("typescript", 4), ("tailwind", 3),
    ]),
    ("cloud", [
        ("docker", 5), ("github actions", 4), ("azure ai foundry", 4),
        ("aws", 3), ("kubernetes", 3), ("railway", 3),
    ]),
]

MAX_WEIGHT = 5


def chip_width(tool: str) -> float:
    return len(tool) * FS * C.ADVANCE_EM


def flow(items: list[tuple[str, int]], width: float):
    """Lay a group's chips into lines, wrapping at the column width.

    Wrapping rather than trimming: the row that overflows is whichever group
    you last added a tool to, and silently dropping it is worse than a
    second line.
    """
    lines: list[list[tuple[str, int, float]]] = [[]]
    x = 0.0
    for tool, weight in items:
        w = chip_width(tool)
        if x and x + w > width:
            lines.append([])
            x = 0.0
        lines[-1].append((tool, weight, x))
        x += w + CHIP_GAP
    return lines


def chip(tool: str, weight: int, x: float, y: float, index: int,
         begin: float) -> str:
    """A tool name over a level meter.

    An earlier version filled a rounded box *behind* the name in proportion to
    the weight. It read as a rendering fault -- a hard vertical step through the
    middle of a word looks like something failed to paint, not like a value. The
    meter belongs under the text where it can't be mistaken for anything else.
    """
    w = len(tool) * FS * C.ADVANCE_EM
    fill_w = w * (weight / MAX_WEIGHT)
    heavy = weight >= 4
    bar_y = y + FS + 4.5

    text = C.fade_in(
        C.text(x, y + FS * 0.85, tool, size=FS,
               cls="emp-f" if heavy else "mut-f"),
        begin + 0.08,
        0.35,
    )
    track = (
        f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{w:.1f}" height="2.6" '
        f'rx="1.3" class="dim-f" opacity="0.28"/>'
    )
    # The fill is the weight, and it carries the wave -- so the row of meters
    # ripples like a level display instead of sitting there.
    fill = C.wave(
        f'<rect x="{x:.1f}" y="{bar_y:.1f}" height="2.6" width="0" rx="1.3" '
        f'class="{"hot-f" if weight >= 5 else "ink-f"}">'
        f'<animate attributeName="width" from="0" to="{fill_w:.1f}" '
        f'begin="{begin:.2f}s" dur="0.7s" fill="freeze" calcMode="spline" '
        f'keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>',
        phase=index * PHASE_STEP,
        cycle=CYCLE,
        lo=0.34,
        hi=1.0,
    )
    return text + track + fill


def build() -> str:
    col_w = W - ITEMS_X
    laid = [(name, flow(items, col_w)) for name, items in GROUPS]

    y = TOP
    rows = []
    for name, lines in laid:
        rows.append((name, lines, y))
        y += len(lines) * (CHIP_H + LINE_GAP)
    height = y - LINE_GAP + TOP

    parts = []
    index = 0
    t = 0.05
    for name, lines, ry in rows:
        parts.append(
            C.fade_in(
                C.label(LABEL_X, ry + FS * 0.85, name.upper(), size=7.8,
                        cls="dim-f", spacing=1.4, anchor="end"),
                t,
            )
        )
        for li, line in enumerate(lines):
            ly = ry + li * (CHIP_H + LINE_GAP)
            for tool, weight, x in line:
                parts.append(chip(tool, weight, ITEMS_X + x, ly, index, t))
                index += 1
                t += 0.04
        t += 0.04

    body = "".join(parts)
    return C.svg(W, height, body, C.embed_font(C.glyphs_in_svg(body)),
                 title="the stack, sized by how often I reach for it")


if __name__ == "__main__":
    C.write("stack.svg", build())
