# scripts

Everything that draws the profile page.

```bash
pip install -r scripts/requirements.txt
```

| script | writes | when to run |
| --- | --- | --- |
| `gen_portrait.py` | `portrait.svg` | only when `me.png` changes |
| `gen_headings.py` | `hd-*.svg` | when a section is renamed |
| `gen_pipeline.py` | `pipeline.svg` | when the agent diagram changes |
| `gen_constellation.py` | `constellation.svg` | when the stack changes — edit `ITEMS` |
| `gen_stats.py` | `stats · streak · langs · year · timeline` | daily, in CI |

`gen_stats.py` takes graphic names to redraw a subset, and then fetches only what
those need:

```bash
python scripts/gen_stats.py stats year
```

`stats`, `streak` and `year` come from the contributions grid, which has no API
quota. `timeline` and `langs` cost one request per repository — so while you are
nudging a label two pixels, name the graphic and stay off the rate limit.

`common.py` holds the palette, the font subsetter and the animation primitives;
change a colour there and re-run everything. `ghdata.py` is the API layer — it
uses GraphQL when a token is present and falls back to the public contributions
grid when there isn't one, so every script runs on a laptop with no secrets.

## Checking your work

```bash
python scripts/check.py
```

Validates every `*.svg`: that it parses, that no `url(#…)` or `mpath` points at a
missing id, that no id is duplicated, that every CSS class used is defined, that
every animation has the attributes it needs, that width/height agree with the
viewBox, that no text runs off the canvas — and, most usefully, that every
character drawn exists in that file's embedded font subset. A missing glyph
renders as a tofu box and silently breaks the character grid; nothing else will
tell you.

## Reviewing changes

```bash
python scripts/preview.py && python -m http.server 8731
```

then open `http://localhost:8731/preview.html`, which shows every graphic on both
the light and dark GitHub backgrounds with a replay button, since SMIL only plays
once per load.

`rasterize.py` renders a single graphic to PNG in its *settled* state — animations
applied rather than stripped — which is how you check tone and layout without a
browser:

```bash
python scripts/rasterize.py portrait.svg 460 dark
```

## Retuning the portrait

`me.png` is a very low-key photograph; 92% of its pixels sit in the darkest eighth
of the range. If you replace it, expect to adjust `BOX`, `FLOOR` and `GAMMA` at the
top of `gen_portrait.py` and to check the result with `rasterize.py` before
committing. `FLOOR` is the one that matters most — it is what keeps the background
gradient from rendering as a wedge of stray dots.

## Rate limits

`gen_stats.py` makes one request per repository for language bytes. Unauthenticated
that is 60/hour and you will hit it; set `STATS_TOKEN` or `GITHUB_TOKEN` in the
environment to lift it to 5000. If any repository fails, `langs.svg` is deliberately
*not* rewritten — percentages of an incomplete total are wrong, not approximate.

## A note on reproducibility

`common.write()` compares files with the base64 font blob masked out. Subsetting
the same glyphs twice does not reliably produce identical bytes — the woff2 payload
drifts a few bytes between processes even with `PYTHONHASHSEED` pinned — so a raw
byte comparison reports every file as changed on every run, and the daily workflow
would commit all thirteen graphics each morning while claiming to commit only what
moved. Don't "simplify" that back to a plain equality check.
