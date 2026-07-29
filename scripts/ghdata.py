"""Everything this page knows about the GitHub account.

Two paths to the same numbers. With a token it asks the GraphQL API, which is
authoritative and can include private contributions if the profile is set to
show them. Without one it parses the public contributions grid that any visitor
can see. The fallback matters: it means the generators run on a laptop with no
secrets configured, so the graphics can be checked before they ever reach CI.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime

LOGIN = os.environ.get("GH_LOGIN", "Ghaith-Bassam-Zaza")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""

API = "https://api.github.com"
UA = "profile-readme-generator (+https://github.com/%s)" % LOGIN

# Set GH_CACHE=1 to reuse the last successful fetch instead of hitting the API.
# Language bytes cost one request per repository, so three runs exhaust the
# unauthenticated 60/hour allowance -- and you will want more than three runs
# while nudging a label. Opt-in rather than automatic, so CI (which never sets
# it) can never serve stale numbers.
CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "_render", "ghcache.json",
)
USE_CACHE = os.environ.get("GH_CACHE") == "1"


def _cache_read(key: str):
    if not USE_CACHE or not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            hit = json.load(fh).get(key)
    except (OSError, ValueError):
        return None
    if hit is not None:
        print(f"  {key}: from cache (GH_CACHE=1)")
    return hit


def _cache_write(key: str, value) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    blob = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as fh:
                blob = json.load(fh)
        except (OSError, ValueError):
            blob = {}
    blob[key] = value
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(blob, fh)


def _get(url: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _graphql(query: str, variables: dict) -> dict | None:
    if not TOKEN:
        return None
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        f"{API}/graphql",
        data=body,
        headers={
            "User-Agent": UA,
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  graphql unavailable ({e.code}), falling back to public data")
        return None
    if payload.get("errors"):
        print(f"  graphql errors: {payload['errors'][0].get('message')}")
        return None
    return payload.get("data")


CAL_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""


def contributions() -> list[tuple[date, int]]:
    """One (date, count) per day of the trailing year, oldest first."""
    data = _graphql(CAL_QUERY, {"login": LOGIN})
    if data:
        weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = [
            (date.fromisoformat(d["date"]), d["contributionCount"])
            for w in weeks
            for d in w["contributionDays"]
        ]
        print(f"  contributions via graphql: {len(days)} days")
        return sorted(days)
    return _contributions_public()


def _contributions_public() -> list[tuple[date, int]]:
    html = _get(
        f"https://github.com/users/{LOGIN}/contributions", accept="text/html"
    ).decode("utf-8", "replace")

    # Counts live in the tooltip, which is linked to its cell by id. Levels on
    # the cell itself are only buckets, and the year graphic wants real numbers.
    counts: dict[str, int] = {}
    for m in re.finditer(
        r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html
    ):
        cell_id, txt = m.group(1), m.group(2)
        n = re.match(r"\s*(No|[\d,]+)\s+contribution", txt)
        if n:
            raw = n.group(1)
            counts[cell_id] = 0 if raw == "No" else int(raw.replace(",", ""))

    days = []
    for m in re.finditer(
        r'<td[^>]*\bdata-date="(\d{4}-\d\d-\d\d)"[^>]*\bid="([^"]+)"[^>]*', html
    ):
        d, cell_id = m.group(1), m.group(2)
        days.append((date.fromisoformat(d), counts.get(cell_id, 0)))

    if not days:  # markup changed under us; better to fail loudly than ship zeros
        raise RuntimeError("could not parse the public contributions grid")
    print(f"  contributions via public grid: {len(days)} days")
    return sorted(days)


def repos() -> list[dict]:
    """Public, non-fork repositories, newest first."""
    hit = _cache_read("repos")
    if hit is not None:
        return hit
    out, page = [], 1
    while True:
        chunk = json.loads(
            _get(f"{API}/users/{LOGIN}/repos?per_page=100&page={page}&type=owner")
        )
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    keep = [r for r in out if not r["fork"]]
    print(f"  repos: {len(keep)} public")
    _cache_write("repos", keep)
    return keep


def language_bytes(rs: list[dict]) -> tuple[dict[str, int], list[str]]:
    """Bytes per language across every public repo, plus any repos that failed.

    One request per repo. Unauthenticated that is 60/hour, which is fine for a
    manual run; in CI the token lifts it to 5000.

    The failure list is not decoration. These are percentages of a total, so a
    single skipped repo silently moves every other number on the chart -- when
    the rate limit bites, dropping four repos shifted the top language by three
    points. The caller is expected to refuse to write a partial chart.
    """
    hit = _cache_read("language_bytes")
    if hit is not None:
        return hit, []
    totals: dict[str, int] = {}
    failed: list[str] = []
    for r in rs:
        try:
            langs = json.loads(_get(f"{API}/repos/{r['full_name']}/languages"))
        except urllib.error.HTTPError as e:
            print(f"  languages for {r['name']}: HTTP {e.code}")
            failed.append(r["name"])
            continue
        for name, n in langs.items():
            totals[name] = totals.get(name, 0) + n
    ordered = dict(sorted(totals.items(), key=lambda kv: -kv[1]))
    if not failed:
        _cache_write("language_bytes", ordered)
    return ordered, failed


def language_repos(rs: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rs:
        if r.get("language"):
            counts[r["language"]] = counts.get(r["language"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def streaks(days: list[tuple[date, int]]) -> dict:
    """Current and longest run of consecutive days with any contribution.

    Today is excluded from breaking the current streak: a day that hasn't
    finished yet shouldn't zero out a run that is still alive.
    """
    today = datetime.utcnow().date()
    best, best_span = 0, (None, None)
    run, run_start = 0, None
    for d, n in days:
        if n > 0:
            run_start = d if run == 0 else run_start
            run += 1
            if run > best:
                best, best_span = run, (run_start, d)
        else:
            run, run_start = 0, None

    cur, cur_start = 0, None
    for d, n in reversed(days):
        if n > 0:
            cur += 1
            cur_start = d
        elif d == today:
            continue  # still in progress
        else:
            break

    active = sum(1 for _, n in days if n > 0)
    return {
        "current": cur,
        "current_start": cur_start,
        "longest": best,
        "longest_span": best_span,
        "active": active,
        "total": sum(n for _, n in days),
        "busiest": max((n for _, n in days), default=0),
        "days": len(days),
    }
