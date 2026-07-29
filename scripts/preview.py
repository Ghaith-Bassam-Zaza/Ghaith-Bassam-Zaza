"""Build a local review page for every generated graphic.

GitHub renders these on two very different backgrounds and the SVGs carry no
background of their own, so anything that looks right on one theme can be
invisible on the other. This shows both at once, at true README display width,
with a replay button because SMIL only runs once.

    python scripts/preview.py  ->  preview.html
"""

from __future__ import annotations

import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Display widths matching README.md, so what you see here is what ships.
PANELS = [
    ("portrait.svg", 460),
    ("stats.svg", 620),
    ("hd-about.svg", 620),
    ("hd-work.svg", 620),
    ("hd-stack.svg", 620),
    ("stack.svg", 620),
    ("hd-projects.svg", 620),
    ("hd-pipeline.svg", 620),
    ("pipeline.svg", 620),
    ("hd-stats.svg", 620),
    ("streak.svg", 620),
    ("langs.svg", 620),
    ("year.svg", 620),
]

PAGE = """<!doctype html><meta charset="utf-8"><title>profile preview</title>
<style>
  body{{margin:0;font:13px ui-monospace,Menlo,Consolas,monospace}}
  .wrap{{display:grid;grid-template-columns:1fr 1fr;min-height:100vh}}
  .col{{padding:28px 24px 80px}}
  .light{{background:#fff;color:#57606a;color-scheme:light}}
  .dark{{background:#0d1117;color:#8b949e;color-scheme:dark}}
  h2{{font:600 11px ui-monospace,monospace;letter-spacing:.14em;
      text-transform:uppercase;opacity:.55;margin:0 0 24px}}
  figure{{margin:0 0 26px}}
  figcaption{{font-size:10px;opacity:.4;margin:0 0 6px;letter-spacing:.06em}}
  img{{display:block;max-width:100%}}
  .missing{{padding:14px;border:1px dashed currentColor;opacity:.35;
            font-size:11px}}
  button{{position:fixed;right:16px;bottom:16px;z-index:9;padding:9px 16px;
    font:600 12px ui-monospace,monospace;background:#e8b478;color:#1c1206;
    border:0;border-radius:6px;cursor:pointer}}
</style>
<div class="wrap">
  <div class="col light"><h2>github light</h2>{light}</div>
  <div class="col dark"><h2>github dark</h2>{dark}</div>
</div>
<button onclick="replay()">replay all</button>
<script>
function replay(){{
  document.querySelectorAll('img').forEach(function(i){{
    var s=i.src.split('?')[0]; i.src=s+'?t='+Date.now();
  }});
}}
</script>
"""


def column(scheme: str) -> str:
    out = []
    for name, width in PANELS:
        path = os.path.join(ROOT, name)
        cap = html.escape(name)
        if not os.path.exists(path):
            out.append(
                f'<figure><figcaption>{cap}</figcaption>'
                f'<div class="missing">not generated yet</div></figure>'
            )
            continue
        kb = os.path.getsize(path) / 1024
        out.append(
            f'<figure><figcaption>{cap} &middot; {kb:.0f} KB</figcaption>'
            f'<img src="{name}?{scheme}" width="{width}" alt="{cap}"></figure>'
        )
    return "".join(out)


if __name__ == "__main__":
    page = PAGE.format(light=column("l"), dark=column("d"))
    dest = os.path.join(ROOT, "preview.html")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote {dest}")
