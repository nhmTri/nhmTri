#!/usr/bin/env python3
"""Regenerate the live parts of the profile README.

Run by .github/workflows/refresh.yml every morning. Reads only public GitHub
API endpoints and writes three things, nothing else:

  assets/activity.svg   twelve weeks of commits, one bar per week
  assets/stack.svg      the language split across public repositories
  README.md             the block between <!--LIVE:start--> and <!--LIVE:end-->

If the API is unreachable or returns something unexpected the script exits 0
without touching any file, so a bad morning at GitHub never leaves a broken
README behind.

    python3 scripts/refresh.py                  # live
    python3 scripts/refresh.py --fixture f.json # render from a saved payload
    python3 scripts/refresh.py --dump f.json    # save what the API returned
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

USER = "nhmTri"
API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# repo -> the workflow file whose result is worth putting on the profile.
# Deliberately the TEST workflow, not "whatever ran last" — a deployment
# workflow failing says nothing about whether the code is correct.
FEATURED = {
    "voucher-abuse-detection": "sql-tests.yml",
    "rfm-segmentation-sql": "sql-tests.yml",
    "Job_realtime": "build.yml",
    "Brazilian_E_Commerce": "checks.yml",
}

START = "<!--LIVE:start-->"
END = "<!--LIVE:end-->"
WEEKS = 12


# --------------------------------------------------------------------- fetch
def get(path: str, accept_202: bool = False):
    """GET a JSON endpoint. Returns None for 404/empty, retries a 202 once.

    The /stats/ endpoints answer 202 while GitHub computes them; the documented
    behaviour is to come back shortly.
    """
    for attempt in (0, 1):
        req = urllib.request.Request(
            API + path,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "nhmTri-profile-refresh",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                if r.status == 202 and accept_202 and attempt == 0:
                    time.sleep(6)
                    continue
                body = r.read().decode("utf-8").strip()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404, 409):      # empty repo, no such workflow, rate limit
                return None
            raise
    return None


def collect() -> dict:
    repos = [r for r in (get(f"/users/{USER}/repos?per_page=100&sort=pushed") or [])
             if not r.get("fork")]
    names = [r["name"] for r in repos][:15]

    # --- twelve weeks of commits, summed across repositories ----------------
    # /stats/commit_activity gives 52 weeks of real commit counts. The events
    # feed does not: it only carries recent *public push events*, lags by
    # minutes, and drops everything older than ninety days.
    weekly: dict[int, int] = {}
    for name in names:
        for w in (get(f"/repos/{USER}/{name}/stats/commit_activity", accept_202=True) or []):
            try:
                weekly[int(w["week"])] = weekly.get(int(w["week"]), 0) + int(w["total"])
            except (KeyError, TypeError, ValueError):
                continue

    # --- the most recent commit in each repository --------------------------
    recent = []
    for name in names:
        head = get(f"/repos/{USER}/{name}/commits?per_page=1")
        if not head:
            continue
        c = head[0].get("commit") or {}
        recent.append({
            "repo": name,
            "message": (c.get("message") or "").splitlines()[0].strip(),
            "date": ((c.get("author") or {}).get("date")
                     or (c.get("committer") or {}).get("date") or ""),
        })
    recent.sort(key=lambda r: r["date"], reverse=True)

    # --- language split -----------------------------------------------------
    languages: dict[str, int] = {}
    for name in names[:12]:
        for lang, size in (get(f"/repos/{USER}/{name}/languages") or {}).items():
            languages[lang] = languages.get(lang, 0) + size

    # --- the test workflow's verdict, per featured repository ---------------
    runs = {}
    for name, workflow in FEATURED.items():
        data = get(f"/repos/{USER}/{name}/actions/workflows/{workflow}"
                   f"/runs?branch=main&status=completed&per_page=1")
        wr = (data or {}).get("workflow_runs") or []
        if wr:
            runs[name] = {"conclusion": wr[0].get("conclusion"),
                          "workflow": wr[0].get("name") or workflow}

    return {"weekly": weekly, "recent": recent, "languages": languages, "runs": runs}


# ----------------------------------------------------------------- rendering
def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def last_weeks(weekly: dict, now: dt.datetime, n: int = WEEKS):
    """The n most recent week buckets, oldest first, as (date, count)."""
    if not weekly:
        return []
    keys = sorted(int(k) for k in weekly)
    cutoff = int(now.timestamp())
    keys = [k for k in keys if k <= cutoff + 7 * 86400][-n:]
    return [(dt.datetime.fromtimestamp(k, dt.timezone.utc).date(), int(weekly[k])) for k in keys]


def activity_svg(series) -> str:
    w, h = 820, 142
    pad_l, pad_b, top = 10, 30, 38
    n = max(1, len(series))
    gap = 9
    bw = (w - pad_l * 2 - gap * (n - 1)) / n
    peak = max([c for _, c in series] + [1])
    usable = h - top - pad_b

    bars, labels = [], []
    for i, (start, c) in enumerate(series):
        x = pad_l + i * (bw + gap)
        bh = max(3.0, usable * (c / peak))
        y = top + usable - bh
        dim = " dim" if c == 0 else ""
        bars.append(
            f'  <rect class="b{dim}" x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
            f'height="{bh:.1f}" rx="3" style="animation-delay:{i * 0.055:.2f}s"/>'
        )
        if c:
            bars.append(
                f'  <text class="v" x="{x + bw / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" '
                f'style="animation-delay:{0.3 + i * 0.055:.2f}s">{c}</text>'
            )
        if i % 3 == 0 or i == n - 1:
            labels.append(
                f'  <text class="d" x="{x + bw / 2:.1f}" y="{h - 10}" '
                f'text-anchor="middle">{start.strftime("%d %b")}</text>'
            )

    total = sum(c for _, c in series)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Commits across public repositories over the last twelve weeks: {total} in total.">
  <style>
    :root{{color-scheme:light dark}}
    .b{{fill:#184f95;transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);
       animation:g .6s cubic-bezier(.2,.7,.3,1) forwards}}
    .b.dim{{fill:#c3c2b7;opacity:.5}}
    @keyframes g{{to{{transform:scaleY(1)}}}}
    .v{{font:600 10px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#52514e;
       opacity:0;animation:f .4s ease-out forwards}}
    @keyframes f{{to{{opacity:1}}}}
    .d{{font:500 9.5px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#8a8880}}
    .t{{font:600 9.5px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#8a8880;letter-spacing:.16em}}
    @media (prefers-reduced-motion:reduce){{.b{{transform:scaleY(1);animation:none}}.v{{opacity:1;animation:none}}}}
    @media (prefers-color-scheme:dark){{.b{{fill:#5598e7}}.b.dim{{fill:#383835}}.v{{fill:#c3c2b7}}}}
  </style>
  <text class="t" x="{pad_l}" y="14">COMMITS, LAST 12 WEEKS &#183; {total} TOTAL</text>
{chr(10).join(bars)}
{chr(10).join(labels)}
</svg>
"""


LANG_COLOR = {
    "Python": "#184f95", "Java": "#5598e7", "SQL": "#2a78d6", "PLpgSQL": "#2a78d6",
    "TSQL": "#2a78d6", "CQL": "#86b6ef", "Jupyter Notebook": "#898781",
    "Shell": "#6f6d68", "HTML": "#e8736f", "JavaScript": "#b02e2d",
    "CSS": "#86b6ef", "Dockerfile": "#9a9890", "Makefile": "#52514e", "Scala": "#b02e2d",
}


def stack_svg(languages: dict) -> str:
    items = sorted(languages.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1
    keep, other = items[:6], sum(v for _, v in items[6:])
    if other:
        keep.append(("Other", other))

    w, h = 820, 96
    bar_y, bar_h, pad = 26, 16, 10
    inner = w - pad * 2
    segs, legend = [], []
    x = float(pad)
    lx = float(pad)
    for i, (name, size) in enumerate(keep):
        frac = size / total
        sw = max(3.0, inner * frac - (2 if i < len(keep) - 1 else 0))
        col = LANG_COLOR.get(name, "#898781")
        segs.append(
            f'  <rect class="s" x="{x:.1f}" y="{bar_y}" width="{sw:.1f}" height="{bar_h}" '
            f'rx="3" fill="{col}" style="animation-delay:{i * 0.08:.2f}s"/>'
        )
        x += sw + 2
        label = f"{esc(name)} {frac * 100:.0f}%"
        legend.append(
            f'  <circle cx="{lx + 5:.1f}" cy="{bar_y + 44}" r="4.5" fill="{col}"/>'
            f'<text class="l" x="{lx + 16:.1f}" y="{bar_y + 48}">{label}</text>'
        )
        lx += 22 + len(label) * 6.1

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Language split across public repositories: {esc(', '.join(n for n, _ in keep))}.">
  <style>
    :root{{color-scheme:light dark}}
    .s{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);
       animation:g .65s cubic-bezier(.2,.7,.3,1) forwards}}
    @keyframes g{{to{{transform:scaleX(1)}}}}
    .l{{font:500 10.5px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#52514e}}
    .t{{font:600 9.5px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#8a8880;letter-spacing:.16em}}
    @media (prefers-reduced-motion:reduce){{.s{{transform:scaleX(1);animation:none}}}}
    @media (prefers-color-scheme:dark){{.l{{fill:#c3c2b7}}}}
  </style>
  <text class="t" x="{pad}" y="14">WHAT THE PUBLIC REPOSITORIES ARE WRITTEN IN</text>
{chr(10).join(segs)}
{chr(10).join(legend)}
</svg>
"""


def ago(iso: str, now: dt.datetime) -> str:
    try:
        t = dt.datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return ""
    secs = max(0, (now - t).total_seconds())
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    days = int(secs // 86400)
    return f"{days}d ago" if days < 14 else f"{days // 7}w ago"


def live_block(data: dict, now: dt.datetime) -> str:
    lines = ["", "### What moved recently", ""]

    rows = [r for r in data["recent"] if r.get("message")][:5]
    if rows:
        lines += ["| | | |", "|---|---|---|"]
        for r in rows:
            msg = r["message"]
            msg = (msg[:68] + "…") if len(msg) > 69 else msg
            lines.append(
                f"| **[{r['repo']}](https://github.com/{USER}/{r['repo']})** "
                f"| {msg} | `{ago(r['date'], now)}` |"
            )
    else:
        lines.append("_Nothing public to report today._")

    checks = []
    for name in FEATURED:
        run = data["runs"].get(name)
        if not run:
            continue
        mark = {"success": "passing", "failure": "failing"}.get(
            run.get("conclusion"), run.get("conclusion") or "unknown")
        colour = {"passing": "1F7A5A", "failing": "C0392B"}.get(mark, "898781")
        checks.append(
            f"[![{name}](https://img.shields.io/badge/{name.replace('-', '--')}-{mark}-{colour}"
            f"?style=flat-square&logo=githubactions&logoColor=white)]"
            f"(https://github.com/{USER}/{name}/actions)"
        )
    if checks:
        lines += ["", "### Every repository below runs its own tests", "", " ".join(checks)]

    lines += [
        "",
        '<img src="assets/activity.svg" alt="Commits across public repositories over the last twelve weeks" width="100%">',
        "",
        '<img src="assets/stack.svg" alt="Language split across public repositories" width="100%">',
        "",
        f"<sub>Regenerated from the GitHub API every morning · last run "
        f"{now.strftime('%d %b %Y, %H:%M')} UTC</sub>",
        "",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ assembly
def splice(readme: str, block: str) -> str:
    if START not in readme or END not in readme:
        raise SystemExit("README is missing the LIVE markers — refusing to guess where to write.")
    return re.sub(re.escape(START) + r".*?" + re.escape(END), START + block + END, readme, flags=re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="a saved JSON payload, for offline testing")
    ap.add_argument("--dump", help="save what the API returned, for offline testing")
    ap.add_argument("--now", help="ISO timestamp to treat as now, for reproducible tests")
    args = ap.parse_args()

    now = (dt.datetime.strptime(args.now, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
           if args.now else dt.datetime.now(dt.timezone.utc))

    if args.fixture:
        with open(args.fixture, encoding="utf-8") as fh:
            data = json.load(fh)
        data["weekly"] = {int(k): v for k, v in data.get("weekly", {}).items()}
    else:
        try:
            data = collect()
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            print(f"GitHub API unreachable ({exc}) — leaving every file as it is.", file=sys.stderr)
            return 0
        if args.dump:
            with open(args.dump, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=1)

    series = last_weeks(data["weekly"], now)
    if not series:
        print("No weekly commit data came back — leaving every file as it is.", file=sys.stderr)
        return 0

    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    out = {
        os.path.join(ROOT, "assets", "activity.svg"): activity_svg(series),
        os.path.join(ROOT, "assets", "stack.svg"): stack_svg(data["languages"]),
    }
    readme_path = os.path.join(ROOT, "README.md")
    with open(readme_path, encoding="utf-8") as fh:
        out[readme_path] = splice(fh.read(), live_block(data, now))

    for path, text in out.items():
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote", os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
