"""The data graphics. This is the script the daily workflow runs.

    python scripts/gen_stats.py

Everything here is drawn from the GitHub API at build time and committed, so
the README loads nothing from a third party and cannot be rate-limited or go
dark when someone else's badge service does.
"""

from __future__ import annotations

import sys
from datetime import date

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as C  # noqa: E402
import ghdata as D  # noqa: E402

W = 620
MONTHS = "JFMAMJJASOND"


def _month_key(d: date) -> tuple[int, int]:
    return d.year, d.month


# ------------------------------------------------------------------ stats

def stats_svg(days, s) -> str:
    H = 112
    parts = [C.fade_in(C.label(0, 11, "LAST 12 MONTHS"), 0.05)]

    parts.append(
        C.count_up(0, 58, s["total"], 0.25, 0.9, 34, "emp-f", weight=700)
    )
    parts.append(
        C.fade_in(
            C.text(0, 78, "contributions", size=10.5, cls="mut-f"), 0.85
        )
    )
    parts.append(
        C.fade_in(
            C.text(0, 95, f"{s['active']} active days  ·  best day {s['busiest']}",
                   size=9.5, cls="dim-f"),
            0.95,
        )
    )

    # Monthly totals. Twelve bars is enough to show shape without pretending
    # to the precision of the day grid further down the page.
    buckets: dict[tuple[int, int], int] = {}
    for d, n in days:
        buckets[_month_key(d)] = buckets.get(_month_key(d), 0) + n
    keys = sorted(buckets)[-12:]
    peak = max((buckets[k] for k in keys), default=1) or 1

    x0, span, base, tall = 286, W - 286, 82, 54
    slot = span / max(len(keys), 1)
    bw = slot - 6.5
    for i, k in enumerate(keys):
        v = buckets[k]
        h = max(1.5, tall * (v / peak))
        x = x0 + i * slot
        cls = "hot-f" if v == peak else ("ink-f" if v else "dim-f")
        parts.append(
            f'<rect x="{x:.1f}" y="{base:.1f}" width="{bw:.1f}" height="0" rx="1.5" '
            f'class="{cls}"><animate attributeName="height" from="0" to="{h:.1f}" '
            f'begin="{0.4 + i * 0.05:.2f}s" dur="0.55s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>'
            f'<animate attributeName="y" from="{base:.1f}" to="{base - h:.1f}" '
            f'begin="{0.4 + i * 0.05:.2f}s" dur="0.55s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>'
        )
        parts.append(
            C.fade_in(
                C.text(x + bw / 2, 95, MONTHS[k[1] - 1], size=8.5, cls="dim-f",
                       anchor="middle"),
                0.5 + i * 0.05,
            )
        )

    parts.append(C.fade_in(C.label(W - 3, 11, "BY MONTH", anchor="end"), 0.05))
    body = "".join(parts)
    return C.svg(W, H, body, _faces(body), title="contributions in the last year")


# ----------------------------------------------------------------- streak

def _span_text(a: date | None, b: date | None) -> str:
    if not a or not b:
        return "none yet"
    if a == b:
        return a.strftime("%-d %b %Y") if sys.platform != "win32" else a.strftime("%d %b %Y").lstrip("0")
    same_year = a.year == b.year
    left = a.strftime("%d %b").lstrip("0") if same_year else a.strftime("%d %b %Y").lstrip("0")
    return f"{left} – {b.strftime('%d %b %Y').lstrip('0')}"


def streak_svg(s) -> str:
    H = 92
    cells = [
        ("CURRENT STREAK", s["current"],
         "day" if s["current"] == 1 else "days",
         _span_text(s["current_start"], s["current_start"]) if s["current"] else "—"),
        ("LONGEST STREAK", s["longest"],
         "day" if s["longest"] == 1 else "days",
         _span_text(*s["longest_span"])),
        ("ACTIVE DAYS", s["active"], f"of {s['days']}",
         f"{100 * s['active'] / max(s['days'], 1):.0f}% of the year"),
    ]

    parts = []
    cw = W / 3
    for i, (title, value, unit, sub) in enumerate(cells):
        x = i * cw
        parts.append(C.fade_in(C.label(x, 12, title), 0.05 + i * 0.08))
        parts.append(
            C.count_up(x, 50, value, 0.3 + i * 0.12, 0.8, 27,
                       "hot-f" if i == 0 else "emp-f", weight=700)
        )
        digits = len(f"{value:,}")
        parts.append(
            C.fade_in(
                C.text(x + digits * 27 * C.ADVANCE_EM + 7, 50, unit, size=10,
                       cls="mut-f"),
                0.6 + i * 0.12,
            )
        )
        parts.append(
            C.fade_in(C.text(x, 70, sub, size=9.5, cls="dim-f"), 0.7 + i * 0.12)
        )
        if i:
            parts.append(
                C.draw_line(f"M{x - 22:.1f} 4V78", 74, 0.2 + i * 0.1, 0.5,
                            "dim-s", 1.0)
            )

    # The active-days bar is the only one of the three that has a denominator,
    # so it is the only one that gets a bar.
    frac = s["active"] / max(s["days"], 1)
    parts.append(
        f'<rect x="{2 * cw:.1f}" y="80" width="{cw - 30:.1f}" height="3" rx="1.5" '
        f'class="dim-f" opacity="0.5"/>'
    )
    parts.append(C.grow_bar(2 * cw, 80, (cw - 30) * frac, 3, 0.9, 0.8, "ink-f"))

    body = "".join(parts)
    return C.svg(W, H, body, _faces(body), title="streaks")


# ------------------------------------------------------------------ langs

# GitHub's own names, shortened to fit the column without ellipsing into
# something unreadable ("jupyter note…").
LANG_ALIAS = {
    "Jupyter Notebook": "jupyter",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "PowerShell": "powershell",
}


def _lang_column(entries, x, width, title, fmt, begin, top) -> list[str]:
    parts = [C.fade_in(C.label(x, top - 18, title), begin)]
    if not entries:
        return parts
    total = sum(v for _, v in entries) or 1
    peak = max(v for _, v in entries) or 1
    name_w, gap = 86, 10
    bar_x = x + name_w + gap
    bar_w = width - name_w - gap - 52
    for i, (name, value) in enumerate(entries):
        y = top + i * 19
        t = begin + 0.14 + i * 0.07
        short = LANG_ALIAS.get(name, name)
        short = short if len(short) <= 13 else short[:12] + "…"
        parts.append(
            C.fade_in(C.text(x, y + 4, short.lower(), size=10,
                             cls="emp-f" if i == 0 else "mut-f"), t)
        )
        parts.append(
            f'<rect x="{bar_x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="6" '
            f'rx="3" class="dim-f" opacity="0.35"/>'
        )
        parts.append(
            C.grow_bar(bar_x, y, bar_w * (value / peak), 6, t, 0.85,
                       "hot-f" if i == 0 else "ink-f", rx=3)
        )
        parts.append(
            C.fade_in(
                C.text(x + width, y + 5, fmt(value, total), size=9,
                       cls="dim-f", anchor="end"),
                t + 0.1,
            )
        )
    return parts


def langs_svg(by_bytes, by_repo) -> str:
    rows = 6
    top = 50
    H = top + rows * 19 + 6
    left = list(by_bytes.items())[:rows]
    right = list(by_repo.items())[:rows]
    col = 288

    # Said outright, on the graphic itself. This counts public repositories and
    # nothing else -- mostly coursework and Kaggle notebooks -- while the work
    # that actually represents him lives in private repos it cannot see. A
    # reader who takes this for a summary of his output is being misled, and a
    # caption is the cheapest possible fix.
    parts = [
        C.fade_in(C.label(0, 11, "PUBLIC REPOSITORIES ONLY", cls="mut-f"), 0.02),
        C.fade_in(
            C.text(W - 3, 11, "private work is not counted here", size=9,
                   cls="dim-f", anchor="end"),
            0.06,
        ),
        C.draw_line(f"M0 20H{W}", W, 0.10, 0.6, "dim-s", 1.0),
    ]
    parts += _lang_column(left, 0, col, "BY BYTES",
                          lambda v, t: f"{100 * v / t:.1f}%", 0.14, top)
    # The right column's values are end-anchored, so it stops short of the
    # canvas rather than setting them flush against the edge.
    parts += _lang_column(right, W - col, col - 4, "BY REPO",
                          lambda v, t: f"{v}", 0.22, top)
    body = "".join(parts)
    return C.svg(W, H, body, _faces(body),
                 title="languages across public repositories only")


# ------------------------------------------------------------------- year

def year_svg(days, s) -> str:
    """365-odd days, one character each, on the portrait's own ramp."""
    cols = (len(days) + 6) // 7
    cell_w = W / cols
    row_h = 13.0
    top = 54
    H = int(top + 7 * row_h + 8)

    nonzero = sorted(n for _, n in days if n > 0)
    # Quantile thresholds rather than fixed cutoffs: with 93 active days out of
    # 368, fixed buckets would put almost everything in the lowest one.
    def level(n: int) -> int:
        if n <= 0:
            return 0
        i = sum(1 for v in nonzero if v < n)
        return 1 + min(4, int(4 * i / max(len(nonzero) - 1, 1)))

    parts = [
        C.fade_in(C.label(0, 12, "THE YEAR"), 0.05),
        C.fade_in(
            C.text(0, 30, f"{s['active']} of {s['days']} days had a contribution",
                   size=10.5, cls="mut-f"),
            0.12,
        ),
    ]

    # Legend
    parts.append(C.fade_in(C.text(W - 96, 30, "less", size=9, cls="dim-f",
                                  anchor="end"), 0.2))
    for i, ch in enumerate(C.RAMP[1:]):
        parts.append(
            C.fade_in(
                C.text(W - 88 + i * 12, 30, ch, size=10.5, cls="ink-f",
                       anchor="middle"),
                0.2,
            )
        )
    parts.append(C.fade_in(C.text(W - 3, 30, "more", size=9, cls="dim-f",
                                  anchor="end"), 0.2))

    # Month rules along the top of the grid
    seen = set()
    for i, (d, _) in enumerate(days):
        if d.month in seen or d.day > 7:
            continue
        seen.add(d.month)
        cx = (i // 7) * cell_w
        if cx < 4 or cx > W - 18:
            continue
        parts.append(
            C.fade_in(
                C.text(cx, 47, MONTHS[d.month - 1], size=8, cls="dim-f"), 0.25
            )
        )

    # Week by week, left to right.
    for c in range(cols):
        week = days[c * 7 : c * 7 + 7]
        glyphs = []
        for r, (_, n) in enumerate(week):
            lv = level(n)
            if lv == 0:
                continue
            glyphs.append(
                C.text(
                    c * cell_w + cell_w / 2,
                    top + r * row_h + 10,
                    C.RAMP[lv],
                    size=11.5,
                    cls="hot-f" if lv >= 4 else "ink-f",
                    anchor="middle",
                )
            )
        if glyphs:
            parts.append(C.fade_in("".join(glyphs), 0.35 + c * 0.016, 0.3))

    body = "".join(parts)
    return C.svg(W, H, body, _faces(body), title="the year, one character per day")


# ------------------------------------------------------------------- glue

def _faces(body: str) -> str:
    used = C.glyphs_in_svg(body)
    return C.embed_font(used) + C.embed_font(used, "Bold")


# Which upstream data each graphic needs. Contributions come from an endpoint
# with no API quota; anything touching `repos` costs one request per repository
# and will exhaust the unauthenticated 60/hour allowance in three runs.
NEEDS = {
    "stats": "contributions",
    "streak": "contributions",
    "year": "contributions",
    "langs": "repos",
}


def main(only: set[str] | None = None) -> None:
    wanted = only or set(NEEDS)
    unknown = wanted - set(NEEDS)
    if unknown:
        sys.exit(f"unknown graphic(s): {', '.join(sorted(unknown))}")

    sources = {NEEDS[w] for w in wanted}
    days = s = rs = by_bytes = by_repo = None
    failed: list[str] = []

    if "contributions" in sources:
        days = D.contributions()
        s = D.streaks(days)
    if "repos" in sources:
        rs = D.repos()
        if "langs" in wanted:
            by_bytes, failed = D.language_bytes(rs)
            by_repo = D.language_repos(rs)

    changed = 0
    if "stats" in wanted:
        changed += C.write("stats.svg", stats_svg(days, s))
    if "streak" in wanted:
        changed += C.write("streak.svg", streak_svg(s))
    if "year" in wanted:
        changed += C.write("year.svg", year_svg(days, s))
    if "langs" in wanted:
        if failed:
            # Percentages of an incomplete total are simply wrong. Leave the
            # last good chart in place and let the next run pick it up.
            print(
                f"  langs.svg SKIPPED: {len(failed)} repo(s) unreadable "
                f"({', '.join(failed[:4])}) -- keeping the committed version"
            )
        else:
            changed += C.write("langs.svg", langs_svg(by_bytes, by_repo))

    print(f"{changed} file(s) changed")


if __name__ == "__main__":
    # No arguments redraws everything, which is what CI wants. Naming graphics
    # redraws just those, and skips fetching anything they don't need -- the
    # difference between one request and twenty when you are iterating on a
    # label position.
    main(set(sys.argv[1:]) or None)
