#!/usr/bin/env python3
"""Regenerate the live parts of the profile README.

Run by .github/workflows/refresh.yml once a day. Reads only public GitHub API
endpoints, writes three things and nothing else:

  assets/activity.svg   twelve weeks of push activity, one bar per week
  assets/stack.svg      the language split across public repositories
  README.md             the block between <!--LIVE:start--> and <!--LIVE:end-->

If the API is unreachable or returns something unexpected the script exits 0
without touching any file, so a bad morning at GitHub never leaves a broken
README behind.

    python3 scripts/refresh.py               # live
    python3 scripts/refresh.py --fixture f   # render from a saved payload
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

USER = "nhmTri"
API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEATURED = [
    "voucher-abuse-detection",
    "rfm-segmentation-sql",
    "Job_realtime",
    "FPT_processing_bigdata",
]

START = "<!--LIVE:start-->"
END = "<!--LIVE:end-->"


# --------------------------------------------------------------------- fetch
def get(path: str):
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
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def collect() -> dict:
    events = []
    for page in (1, 2, 3):
        batch = get(f"/users/{USER}/events/public?per_page=100&page={page}")
        if not batch:
            break
        events.extend(batch)
        if len(batch) < 100:
            break

    repos = [r for r in get(f"/users/{USER}/repos?per_page=100&sort=pushed")
             if not r.get("fork")]

    languages = {}
    for r in repos[:12]:
        try:
            for lang, size in get(f"/repos/{USER}/{r['name']}/languages").items():
                languages[lang] = languages.get(lang, 0) + size
        except Exception:
            pass

    runs = {}
    for name in FEATURED:
        try:
            data = get(f"/repos/{USER}/{name}/actions/runs?per_page=1&status=completed")
            wr = data.get("workflow_runs") or []
            if wr:
                runs[name] = {"conclusion": wr[0].get("conclusion"),
                              "name": wr[0].get("name")}
        except Exception:
            pass

    return {"events": events, "repos": repos, "languages": languages, "runs": runs}


# ----------------------------------------------------------------- rendering
def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def week_buckets(events, weeks=12, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    monday = today - dt.timedelta(days=today.weekday())
    starts = [monday - dt.timedelta(weeks=(weeks - 1 - i)) for i in range(weeks)]
    counts = [0] * weeks
    for ev in events:
        if ev.get("type") != "PushEvent":
            continue
        raw = ev.get("created_at") or ""
        try:
            day = dt.datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        for i in range(weeks - 1, -1, -1):
            if day >= starts[i]:
                counts[i] += len((ev.get("payload") or {}).get("commits") or []) or 1
                break
    return starts, counts


def activity_svg(starts, counts) -> str:
    w, h = 820, 142
    pad_l, pad_b, top = 10, 30, 38
    n = len(counts)
    gap = 9
    bw = (w - pad_l * 2 - gap * (n - 1)) / n
    peak = max(counts + [1])
    usable = h - top - pad_b

    bars, labels = [], []
    for i, c in enumerate(counts):
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
                f'  <text class="v" x="{x + bw / 2:.1f}" y="{y - 6:.1f}" '
                f'text-anchor="middle" style="animation-delay:{0.3 + i * 0.055:.2f}s">{c}</text>'
            )
        if i % 3 == 0 or i == n - 1:
            labels.append(
                f'  <text class="d" x="{x + bw / 2:.1f}" y="{h - 10}" '
                f'text-anchor="middle">{starts[i].strftime("%d %b")}</text>'
            )

    total = sum(counts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Commits pushed to public repositories over the last twelve weeks: {total} in total.">
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
  <text class="t" x="{pad_l}" y="11">COMMITS PUSHED, LAST 12 WEEKS &#183; {total} TOTAL</text>
{chr(10).join(bars)}
{chr(10).join(labels)}
</svg>
"""


LANG_COLOR = {
    "Python": "#184f95", "Java": "#5598e7", "SQL": "#2a78d6", "PLpgSQL": "#2a78d6",
    "Jupyter Notebook": "#898781", "Shell": "#6f6d68", "HTML": "#e8736f",
    "JavaScript": "#b02e2d", "CSS": "#86b6ef", "Dockerfile": "#9a9890",
    "Makefile": "#52514e", "TSQL": "#2a78d6",
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


def ago(iso: str, now=None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        t = dt.datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return ""
    secs = (now - t).total_seconds()
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    days = int(secs // 86400)
    if days < 14:
        return f"{days}d ago"
    return f"{days // 7}w ago"


def live_block(data: dict, now=None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    lines = ["", "### What moved recently", ""]

    seen, rows = set(), []
    for ev in data["events"]:
        if ev.get("type") != "PushEvent":
            continue
        repo = (ev.get("repo") or {}).get("name", "")
        short = repo.split("/")[-1]
        if not short or short in seen:
            continue
        commits = (ev.get("payload") or {}).get("commits") or []
        msg = ""
        for c in reversed(commits):
            m = (c.get("message") or "").splitlines()[0].strip()
            if m and not m.lower().startswith("merge"):
                msg = m
                break
        seen.add(short)
        rows.append((short, msg, ago(ev.get("created_at", ""), now)))
        if len(rows) == 5:
            break

    if rows:
        lines += ["| | | |", "|---|---|---|"]
        for short, msg, when in rows:
            msg = (msg[:68] + "…") if len(msg) > 69 else (msg or "—")
            lines.append(
                f"| **[{short}](https://github.com/{USER}/{short})** | {msg} | `{when}` |"
            )
    else:
        lines.append("_Nothing pushed publicly in the last ninety days._")

    checks = []
    for name in FEATURED:
        run = data["runs"].get(name)
        if not run:
            continue
        mark = {"success": "passing", "failure": "failing"}.get(run["conclusion"], run["conclusion"] or "—")
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
        '<img src="assets/activity.svg" alt="Commits pushed to public repositories over the last twelve weeks" width="100%">',
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
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    return pattern.sub(START + block + END, readme)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="a saved JSON payload, for offline testing")
    ap.add_argument("--now", help="ISO timestamp to treat as now, for reproducible tests")
    args = ap.parse_args()

    now = (dt.datetime.strptime(args.now, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
           if args.now else dt.datetime.now(dt.timezone.utc))

    if args.fixture:
        with open(args.fixture, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        try:
            data = collect()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            print(f"GitHub API unreachable ({exc}) — leaving every file as it is.", file=sys.stderr)
            return 0

    starts, counts = week_buckets(data["events"], today=now.date())

    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    out = {
        os.path.join(ROOT, "assets", "activity.svg"): activity_svg(starts, counts),
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
