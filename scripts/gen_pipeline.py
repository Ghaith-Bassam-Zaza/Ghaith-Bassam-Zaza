"""pipeline.svg -- the shape of an agent run, drawn and then kept moving.

This is the one graphic on the page that isn't derived from a photo or from
the API. It is here because "agentic systems" is a phrase that means nothing
until you show the loop: the planner decides, the tools run, the evaluator
judges, and the interesting edge is the one that goes backwards.

    python scripts/gen_pipeline.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

W, H = 620, 232
MID = 100          # main row centreline
FAN = 62           # vertical offset of the fanned-out worker row
BOX_H = 28
FS = 10.5

# (id, label, x, width, centre-y, emphasis)
NODES = [
    ("trigger", "trigger", 4, 68, MID, False),
    ("planner", "planner", 104, 78, MID, True),
    ("research", "research", 226, 96, MID - FAN, False),
    ("retrieval", "retrieval", 226, 96, MID, False),
    ("tools", "tools", 226, 96, MID + FAN, False),
    ("evaluator", "evaluator", 376, 90, MID, True),
    ("ship", "ship", 520, 62, MID, False),
]
BY_ID = {n[0]: n for n in NODES}


def right(nid: str) -> tuple[float, float]:
    _, _, x, w, cy, _ = BY_ID[nid]
    return x + w, cy


def left(nid: str) -> tuple[float, float]:
    _, _, x, _, cy, _ = BY_ID[nid]
    return x, cy


def link(a: str, b: str) -> tuple[str, float]:
    """A cubic from the right edge of `a` to the left edge of `b`."""
    x0, y0 = right(a)
    x1, y1 = left(b)
    dx = (x1 - x0) * 0.55
    d = f"M{x0:.1f} {y0:.1f}C{x0 + dx:.1f} {y0:.1f} {x1 - dx:.1f} {y1:.1f} {x1:.1f} {y1:.1f}"
    # Close enough for a dash-array; the curves here are shallow.
    length = abs(x1 - x0) + abs(y1 - y0) * 0.45
    return d, length


# The reject edge. Everything else on this diagram flows left to right; this
# one doesn't, which is the whole point of it being drawn.
RETRY_Y = MID + 108
_ev_x = BY_ID["evaluator"][2] + BY_ID["evaluator"][3] / 2
_pl_x = BY_ID["planner"][2] + BY_ID["planner"][3] / 2
RETRY_D = (
    f"M{_ev_x:.1f} {MID + BOX_H / 2:.1f}"
    f"C{_ev_x:.1f} {RETRY_Y:.1f} {_ev_x:.1f} {RETRY_Y:.1f} {_ev_x - 40:.1f} {RETRY_Y:.1f}"
    f"H{_pl_x + 40:.1f}"
    f"C{_pl_x:.1f} {RETRY_Y:.1f} {_pl_x:.1f} {RETRY_Y:.1f} {_pl_x:.1f} {MID + BOX_H / 2:.1f}"
)
RETRY_LEN = (RETRY_Y - MID) * 2 + (_ev_x - _pl_x) + 80

EDGES = [
    ("trigger", "planner"),
    ("planner", "research"),
    ("planner", "retrieval"),
    ("planner", "tools"),
    ("research", "evaluator"),
    ("retrieval", "evaluator"),
    ("tools", "evaluator"),
    ("evaluator", "ship"),
]


def node(nid: str, label: str, x: float, w: float, cy: float, emph: bool,
         begin: float) -> str:
    y = cy - BOX_H / 2
    stroke = "ink-s" if emph else "dim-s"
    fill = "emp-f" if emph else "mut-f"
    box = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{BOX_H}" rx="4" '
        f'class="{stroke}" stroke-width="1" fill="none"/>'
    )
    tx = x + w / 2
    txt = C.text(tx, cy + FS * 0.36, label, size=FS, cls=fill, anchor="middle",
                 weight=700 if emph else None)
    return C.fade_in(box + txt, begin, 0.4)


def pulse(path_id: str, dur: float, begin: float, r: float = 2.6,
          cls: str = "hot-f") -> str:
    """A dot that runs the edge forever.

    Indefinite repeat is deliberate. A pipeline that animates once and stops is
    a picture of a pipeline; this one should still be working when you scroll
    back to it.
    """
    return (
        f'<circle r="{r}" class="{cls}" opacity="0">'
        f'<animate attributeName="opacity" values="0;0.95;0.95;0" '
        f'keyTimes="0;0.12;0.8;1" dur="{dur:.2f}s" begin="{begin:.2f}s" '
        f'repeatCount="indefinite"/>'
        f'<animateMotion dur="{dur:.2f}s" begin="{begin:.2f}s" '
        f'repeatCount="indefinite" rotate="auto">'
        f'<mpath xlink:href="#{path_id}"/></animateMotion></circle>'
    )


def build() -> str:
    defs, drawn, dots = [], [], []

    for i, (a, b) in enumerate(EDGES):
        d, length = link(a, b)
        pid = f"e{i}"
        defs.append(f'<path id="{pid}" d="{d}"/>')
        drawn.append(C.draw_line(d, length, 0.30 + i * 0.07, 0.5, "dim-s", 1.0))

    # The reject edge draws in its own colour rather than a dashed stroke --
    # dash-array is already spoken for by the draw-in animation.
    defs.append(f'<path id="eretry" d="{RETRY_D}"/>')
    drawn.append(C.draw_line(RETRY_D, RETRY_LEN, 1.15, 0.9, "ink-s", 1.0))

    nodes = [
        node(*n, begin=0.10 + i * 0.06) for i, n in enumerate(NODES)
    ]

    # Pulse timings are staggered so the three workers read as running in
    # parallel rather than in lockstep.
    dots.append(pulse("e0", 1.5, 1.6))
    for i, off in ((1, 0.0), (2, 0.25), (3, 0.5)):
        dots.append(pulse(f"e{i}", 1.4, 3.1 + off))
    for i, off in ((4, 0.0), (5, 0.25), (6, 0.5)):
        dots.append(pulse(f"e{i}", 1.4, 4.6 + off))
    dots.append(pulse("e7", 1.3, 6.3))
    dots.append(pulse("eretry", 2.2, 6.3, r=2.2, cls="ink-f"))

    captions = [
        C.fade_in(
            C.text(_ev_x - 46, RETRY_Y - 7, "reject", size=8.5, cls="mut-f",
                   anchor="end", spacing=1.1),
            1.5,
        ),
        C.fade_in(
            C.text(W - 4, MID - 26, "ship", size=8.5, cls="mut-f", anchor="end",
                   spacing=1.1),
            1.5,
        ),
    ]
    captions = captions[:1]  # the "ship" node already says it

    body = (
        "<defs>" + "".join(defs) + "</defs>"
        + "".join(drawn) + "".join(nodes) + "".join(captions) + "".join(dots)
    )
    return C.svg(W, H, body, C.embed_font(C.glyphs_in_svg(body), "Bold")
                 + C.embed_font(C.glyphs_in_svg(body)),
                 title="how an agent run moves")


if __name__ == "__main__":
    C.write("pipeline.svg", build())
