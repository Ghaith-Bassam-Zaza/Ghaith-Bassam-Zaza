"""stack.svg -- the toolkit, grouped and weighted.

This replaces an earlier "constellation" version that drew each tool linked
back to the heaviest item in its group. It tested badly for the obvious reason:
the links carried no meaning a reader could recover, so the whole thing read as
random strokes with the labels bunched in the middle. Structure you have to be
told about isn't structure.

So: one row per group, tools flowing left to right, dot size carrying weight,
and nothing on the canvas that isn't a label or a value.

    python scripts/gen_stack.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

W = 620
FS = 9.4
LABEL_X = 64          # right edge of the group-name column
ITEMS_X = 78          # where the row of tools starts
LINE_H = 17.0
ROW_GAP = 13.0
TOP = 10.0

# (group, [(tool, weight 1-5)]). 5 is "every week"; 1 is "I know it, it isn't
# what I'd reach for". Hand-set on purpose -- this is a claim, not a metric.
GROUPS: list[tuple[str, list[tuple[str, int]]]] = [
    ("agents", [
        ("langgraph", 5), ("langchain", 4), ("function calling", 5),
        ("autogen", 3), ("semantic kernel", 3), ("n8n", 2),
    ]),
    ("llm", [
        ("claude", 5), ("gpt-4", 4), ("rag", 5), ("prompt engineering", 4),
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


def radius(weight: int) -> float:
    return 1.8 + weight * 0.72


def item_width(tool: str, weight: int) -> float:
    return radius(weight) * 2 + 5 + len(tool) * FS * C.ADVANCE_EM


GAP = 15.0


def flow(items: list[tuple[str, int]], width: float) -> list[list[tuple[str, int, float]]]:
    """Lay a group's tools into lines, wrapping at the column width.

    Wrapping rather than trimming: the row that overflows today is whichever
    group you last added a tool to, and silently dropping it is worse than an
    extra line.
    """
    lines: list[list[tuple[str, int, float]]] = [[]]
    x = 0.0
    for tool, weight in items:
        w = item_width(tool, weight)
        if x and x + w > width:
            lines.append([])
            x = 0.0
        lines[-1].append((tool, weight, x))
        x += w + GAP
    return lines


def build() -> str:
    col_w = W - ITEMS_X
    laid = [(name, flow(items, col_w)) for name, items in GROUPS]

    height = TOP
    rows = []
    for name, lines in laid:
        rows.append((name, lines, height))
        height += len(lines) * LINE_H + ROW_GAP
    height = height - ROW_GAP + TOP

    parts = []
    t = 0.05
    for name, lines, y in rows:
        parts.append(
            C.fade_in(
                C.label(LABEL_X, y + FS * 0.9, name.upper(), size=7.8,
                        cls="dim-f", spacing=1.4, anchor="end"),
                t,
            )
        )
        for li, line in enumerate(lines):
            ly = y + li * LINE_H
            for tool, weight, x in line:
                r = radius(weight)
                cx = ITEMS_X + x + r
                cy = ly + FS * 0.55
                dot_cls = "hot-f" if weight >= 5 else (
                    "ink-f" if weight >= 4 else "dim-f"
                )
                txt_cls = "emp-f" if weight >= 4 else "mut-f"
                parts.append(
                    f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="0" class="{dot_cls}">'
                    f'<animate attributeName="r" from="0" to="{r:.2f}" '
                    f'begin="{t:.2f}s" dur="0.42s" fill="freeze" '
                    f'calcMode="spline" keySplines="0.2 1.5 0.3 1" '
                    f'keyTimes="0;1"/></circle>'
                )
                parts.append(
                    C.fade_in(
                        C.text(cx + r + 5, ly + FS * 0.9, tool, size=FS,
                               cls=txt_cls),
                        t + 0.06,
                        0.34,
                    )
                )
                t += 0.035
        t += 0.05

    body = "".join(parts)
    return C.svg(W, height, body, C.embed_font(C.glyphs_in_svg(body)),
                 title="the stack, sized by how often I reach for it")


if __name__ == "__main__":
    C.write("stack.svg", build())
