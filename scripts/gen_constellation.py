"""constellation.svg -- the stack as a weighted field rather than a list.

A comma-separated run of fifty tool names tells a reader nothing about which
ones actually matter. Here weight is size: the things at the centre of the work
are large, the things that are merely on the CV are small, and they cluster by
what they're for.

Weights are hand-set and deliberately opinionated -- edit ITEMS, re-run, done.

    python scripts/gen_constellation.py
"""

from __future__ import annotations

import math
import random
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402

W, H = 620, 250
FS = 8.6
SEED = 11

# (group, anchor_x, anchor_y)
GROUPS = {
    "agents": (128, 68),
    "ml": (330, 60),
    "data": (494, 78),
    "backend": (150, 182),
    "infra": (352, 190),
    "web": (520, 184),
}

# (label, group, weight 1-5). 5 is "I reach for this every week".
ITEMS = [
    ("langgraph", "agents", 5),
    ("langchain", "agents", 4),
    ("rag", "agents", 5),
    ("autogen", "agents", 3),
    ("azure openai", "agents", 4),
    ("n8n", "agents", 2),
    ("pytorch", "ml", 4),
    ("tensorflow", "ml", 3),
    ("scikit-learn", "ml", 3),
    ("opencv", "ml", 2),
    ("pgvector", "data", 4),
    ("postgres", "data", 4),
    ("pinecone", "data", 3),
    ("mongodb", "data", 2),
    ("python", "backend", 5),
    ("fastapi", "backend", 5),
    ("django", "backend", 2),
    ("spring boot", "backend", 2),
    ("docker", "infra", 4),
    ("kubernetes", "infra", 3),
    ("aws", "infra", 3),
    ("actions", "infra", 3),
    ("typescript", "web", 3),
    ("next.js", "web", 3),
    ("react", "web", 3),
]

PAD = 10.0


def radius(weight: int) -> float:
    return 1.9 + weight * 0.95


def box_of(label: str, weight: int) -> tuple[float, float]:
    r = radius(weight)
    return r * 2 + 6 + len(label) * FS * C.ADVANCE_EM, 13.0


def layout() -> list[dict]:
    """Seeded scatter around each group anchor, then relaxed apart.

    Deterministic on purpose: the file is committed, so a re-run that shuffled
    the layout would show up as a diff every time.
    """
    rng = random.Random(SEED)
    items = []
    per_group: dict[str, int] = {}
    for label, group, weight in ITEMS:
        i = per_group.get(group, 0)
        per_group[group] = i + 1
        gx, gy = GROUPS[group]
        # Golden angle keeps the initial scatter even instead of clumpy.
        ang = i * 2.39996 + rng.random() * 0.5
        rad = 16 + i * 13 + rng.random() * 8
        bw, bh = box_of(label, weight)
        items.append(
            {
                "label": label,
                "group": group,
                "weight": weight,
                "x": gx + math.cos(ang) * rad,
                "y": gy + math.sin(ang) * rad * 0.62,
                "w": bw,
                "h": bh,
                "gx": gx,
                "gy": gy,
            }
        )

    for _ in range(340):
        for a in items:
            for b in items:
                if a is b:
                    continue
                dx = (b["x"] + b["w"] / 2) - (a["x"] + a["w"] / 2)
                dy = b["y"] - a["y"]
                need_x = (a["w"] + b["w"]) / 2 + 7
                need_y = (a["h"] + b["h"]) / 2 + 1.5
                if abs(dx) < need_x and abs(dy) < need_y:
                    # Push along whichever axis needs less movement.
                    if (need_x - abs(dx)) / need_x < (need_y - abs(dy)) / need_y:
                        push = (need_x - abs(dx)) / 2 + 0.4
                        s = 1 if dx >= 0 else -1
                        a["x"] -= push * s
                        b["x"] += push * s
                    else:
                        push = (need_y - abs(dy)) / 2 + 0.4
                        s = 1 if dy >= 0 else -1
                        a["y"] -= push * s
                        b["y"] += push * s
        for a in items:
            # Mild pull home, so relaxation doesn't dissolve the clusters.
            a["x"] += (a["gx"] - (a["x"] + a["w"] / 2)) * 0.012
            a["y"] += (a["gy"] - a["y"]) * 0.012
            a["x"] = min(max(a["x"], PAD), W - PAD - a["w"])
            a["y"] = min(max(a["y"], PAD + 4), H - PAD - 4)
    return items


def build() -> str:
    items = layout()
    anchors = {}
    for it in items:
        g = it["group"]
        if g not in anchors or it["weight"] > anchors[g]["weight"]:
            anchors[g] = it

    rng = random.Random(SEED + 1)
    links, dots = [], []

    for it in items:
        a = anchors[it["group"]]
        if a is it:
            continue
        x0, y0 = it["x"] + radius(it["weight"]), it["y"]
        x1, y1 = a["x"] + radius(a["weight"]), a["y"]
        length = math.hypot(x1 - x0, y1 - y0)
        links.append(
            C.draw_line(
                f"M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}",
                length,
                0.20 + rng.random() * 0.5,
                0.7,
                "dim-s",
                0.7,
            )
        )

    order = sorted(range(len(items)), key=lambda i: -items[i]["weight"])
    for rank, idx in enumerate(order):
        it = items[idx]
        r = radius(it["weight"])
        begin = 0.15 + rank * 0.045
        cls = "hot-f" if it["weight"] >= 5 else ("ink-f" if it["weight"] >= 4 else "dim-f")
        tcls = "emp-f" if it["weight"] >= 4 else "mut-f"

        dot = (
            f'<circle cx="{r:.1f}" cy="0" r="0" class="{cls}">'
            f'<animate attributeName="r" from="0" to="{r:.1f}" '
            f'begin="{begin:.2f}s" dur="0.5s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 1.4 0.3 1" keyTimes="0;1"/></circle>'
        )
        lbl = C.fade_in(
            C.text(r * 2 + 6, FS * 0.36, it["label"], size=FS, cls=tcls),
            begin + 0.12,
            0.4,
        )

        # Each item drifts in from its cluster centre, so the field looks like
        # it condensed out of six points rather than appearing all at once.
        dx = (it["gx"] - it["x"]) * 0.55
        dy = (it["gy"] - it["y"]) * 0.55
        dots.append(
            f'<g transform="translate({it["x"]:.1f} {it["y"]:.1f})">'
            f'<g transform="translate({dx:.1f} {dy:.1f})">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{dx:.1f} {dy:.1f}" to="0 0" begin="{begin:.2f}s" dur="0.75s" '
            f'fill="freeze" calcMode="spline" keySplines="0.15 0.8 0.2 1" '
            f'keyTimes="0;1"/>{dot}{lbl}</g></g>'
        )

    # Cluster captions, placed above whatever the relaxation ended up putting
    # at the top of each group rather than at a fixed offset from the anchor.
    caps = []
    for name in GROUPS:
        members = [it for it in items if it["group"] == name]
        top = min(m["y"] for m in members)
        cx = sum(m["x"] + m["w"] / 2 for m in members) / len(members)
        caps.append(
            C.fade_in(
                C.label(cx, top - 13, name.upper(), size=7.6, cls="dim-f",
                        spacing=1.5, anchor="middle"),
                0.9,
            )
        )

    body = "".join(links) + "".join(dots) + "".join(caps)
    return C.svg(W, H, body, C.embed_font(C.glyphs_in_svg(body)),
                 title="stack, weighted by how often I actually reach for it")


if __name__ == "__main__":
    C.write("constellation.svg", build())
