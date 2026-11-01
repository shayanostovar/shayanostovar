#!/usr/bin/env python3
import json, os, html, urllib.request
from pathlib import Path
from collections import Counter

USERNAME = "shayanostovar"
PROFILE_REPO = "shayanostovar/shayanostovar"
ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MANIFEST = ROOT / "profile-projects.json"
MAP = ROOT / "assets" / "project-ecosystem.svg"

TOKEN = os.getenv("PROFILE_REPO_TOKEN") or os.getenv("GITHUB_TOKEN") or ""

def api(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-auto-sync")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_repos():
    repos = []
    if os.getenv("PROFILE_REPO_TOKEN"):
        base = "https://api.github.com/user/repos?affiliation=owner&visibility=all&sort=updated&per_page=100"
    else:
        base = f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100"
    page = 1
    while True:
        rows = api(base + f"&page={page}")
        if not rows:
            break
        repos.extend(rows)
        if len(rows) < 100:
            break
        page += 1
    return repos

def load_manifest():
    if not MANIFEST.exists():
        return []
    return json.loads(MANIFEST.read_text(encoding="utf-8")).get("projects", [])

def merged_projects():
    seen = {}
    for p in load_manifest():
        seen[p["name"]] = dict(p)
    for r in fetch_repos():
        if r["name"] == USERNAME:
            continue
        seen[r["name"]] = {
            "name": r["name"],
            "visibility": "private" if r.get("private") else "public",
            "html_url": r.get("html_url"),
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "updated_at": r.get("updated_at") or "",
        }
    items = list(seen.values())
    items.sort(key=lambda x: x["name"].lower())
    return items

def category(name):
    n = name.lower()
    if any(k in n for k in ["kherad", "rasafam", "behavior", "workflowoptimization"]):
        return "AI & Intelligent Systems"
    if any(k in n for k in ["parastoo", "flight", "pars", "pouya", "visa"]):
        return "Travel Tech & Operations"
    if any(k in n for k in ["crm", "customerclub", "salesfunnel", "atris"]):
        return "Business Systems"
    if any(k in n for k in ["4u", "danial", "website"]):
        return "Digital Products & Web"
    if any(k in n for k in ["old", "magisk", "fal-e-hafez"]):
        return "Experiments & Legacy"
    return "Other Projects"

def wrap_label(name, max_chars=28):
    if len(name) <= max_chars:
        return [name]
    parts = name.replace("-", " ").split()
    lines, cur = [], ""
    for p in parts:
        candidate = (cur + " " + p).strip()
        if len(candidate) > max_chars and cur:
            lines.append(cur)
            cur = p
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines[:2]

def make_svg(projects):
    groups = {}
    for p in projects:
        groups.setdefault(category(p["name"]), []).append(p)
    order = [
        "AI & Intelligent Systems",
        "Business Systems",
        "Travel Tech & Operations",
        "Digital Products & Web",
        "Experiments & Legacy",
        "Other Projects",
    ]
    groups = {k: groups.get(k, []) for k in order if groups.get(k)}
    width = 1500
    col_w = 650
    gap = 70
    left_x, right_x = 75, 775
    core_y = 100
    y_positions = [280, 280]
    placed = []
    for i, (g, items) in enumerate(groups.items()):
        col = i % 2
        x = left_x if col == 0 else right_x
        y = y_positions[col]
        h = 96 + len(items) * 68
        placed.append((g, items, x, y, h))
        y_positions[col] += h + gap
    height = max(y_positions) + 50

    s = []
    s.append(f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shayan Ostovar project ecosystem map">')
    s.append("""<style>
:root{--bg:#ffffff;--ink:#111827;--muted:#6b7280;--rule:#d1d5db;--accent:#2563eb;--core:#f8fafc;--node:#ffffff}
@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--ink:#f0f6fc;--muted:#8b949e;--rule:#30363d;--accent:#58a6ff;--core:#161b22;--node:#0d1117}}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
.node{fill:var(--node);stroke:var(--rule);stroke-width:1.4}.group{fill:none;stroke:var(--rule);stroke-width:1.5}.core{fill:var(--core);stroke:var(--accent);stroke-width:2}
.wire{stroke:var(--rule);stroke-width:1.5;stroke-dasharray:900;stroke-dashoffset:900;animation:draw 1.5s ease forwards}
.flow{stroke:var(--accent);stroke-width:1.2;stroke-dasharray:5 14;opacity:.3;animation:flow 1.8s linear infinite}
.pop{opacity:0;animation:pop .45s ease forwards}@keyframes draw{to{stroke-dashoffset:0}}@keyframes flow{to{stroke-dashoffset:-19}}@keyframes pop{to{opacity:1}}
@media(prefers-reduced-motion:reduce){.wire,.flow,.pop{animation:none;stroke-dashoffset:0;opacity:1}}
</style>""")
    s.append(f'<rect width="{width}" height="{height}" rx="24" fill="var(--bg)"/>')
    s.append('<text x="70" y="44" class="mono" fill="var(--muted)" font-size="16" letter-spacing="3">PROJECT ECOSYSTEM — BUSINESS ANALYSIS × AI × SOFTWARE × AUTOMATION</text>')
    s.append(f'<text x="{width-70}" y="44" class="mono" fill="var(--muted)" font-size="15" text-anchor="end">{len(projects)} PROJECTS</text>')
    s.append(f'<line x1="70" y1="64" x2="{width-70}" y2="64" stroke="var(--rule)"/>')
    s.append('<rect class="core" x="425" y="95" width="650" height="125" rx="14"/>')
    s.append('<text x="750" y="137" text-anchor="middle" class="mono" fill="var(--ink)" font-size="27" font-weight="700">ICT BUSINESS ANALYSIS</text>')
    s.append('<text x="750" y="172" text-anchor="middle" class="mono" fill="var(--accent)" font-size="18">AI · SOFTWARE · AUTOMATION</text>')
    s.append('<text x="750" y="199" text-anchor="middle" class="mono" fill="var(--muted)" font-size="14">process optimization → practical systems</text>')

    for idx, (g, items, x, y, h) in enumerate(placed):
        cx = x + col_w / 2
        s.append(f'<line class="wire" x1="750" y1="220" x2="{cx}" y2="{y}"/>')
        s.append(f'<line class="flow" x1="750" y1="220" x2="{cx}" y2="{y}"/>')
        s.append(f'<g class="pop" style="animation-delay:{0.15+idx*0.12:.2f}s">')
        s.append(f'<rect class="group" x="{x}" y="{y}" width="{col_w}" height="{h}" rx="12"/>')
        s.append(f'<text x="{x+24}" y="{y+34}" class="mono" fill="var(--accent)" font-size="17" font-weight="700" letter-spacing="1.6">{html.escape(g.upper())}</text>')
        for j, p in enumerate(items):
            ny = y + 56 + j * 68
            s.append(f'<rect class="node" x="{x+20}" y="{ny}" width="{col_w-40}" height="54" rx="8"/>')
            lines = wrap_label(p["name"])
            if len(lines) == 1:
                s.append(f'<text x="{x+40}" y="{ny+34}" class="mono" fill="var(--ink)" font-size="16" font-weight="700">{html.escape(lines[0])}</text>')
            else:
                s.append(f'<text x="{x+40}" y="{ny+23}" class="mono" fill="var(--ink)" font-size="15.5" font-weight="700">{html.escape(lines[0])}</text>')
                s.append(f'<text x="{x+40}" y="{ny+42}" class="mono" fill="var(--ink)" font-size="15.5" font-weight="700">{html.escape(lines[1])}</text>')
            vis = p.get("visibility", "public").upper()
            s.append(f'<text x="{x+col_w-40}" y="{ny+34}" text-anchor="end" class="mono" fill="var(--muted)" font-size="11">{vis}</text>')
        s.append('</g>')
    s.append('</svg>')
    return "\n".join(s)

def dynamic_block(projects):
    groups = {}
    for p in projects:
        groups.setdefault(category(p["name"]), []).append(p)
    public = sum(1 for p in projects if p.get("visibility") == "public")
    private = len(projects) - public
    langs = Counter(p.get("language") for p in projects if p.get("language"))
    lang_line = " · ".join(k for k, _ in langs.most_common(8)) or "Python · C# · JavaScript · TypeScript · SQL"
    lines = [
        "<!-- AUTO:START -->",
        "## 🗺️ Project Ecosystem",
        "",
        f"**{len(projects)} projects** · {public} public · {private} private",
        "",
        '<p align="center">',
        '  <img width="100%" src="https://raw.githubusercontent.com/shayanostovar/shayanostovar/main/assets/project-ecosystem.svg" alt="Shayan Ostovar project ecosystem map" />',
        "</p>",
        "",
        "### Repository Index",
        "",
    ]
    for g in ["AI & Intelligent Systems","Business Systems","Travel Tech & Operations","Digital Products & Web","Experiments & Legacy","Other Projects"]:
        items = groups.get(g, [])
        if not items:
            continue
        lines.append(f"**{g}**")
        for p in items:
            if p.get("visibility") == "public" and p.get("html_url"):
                lines.append(f"- [{p['name']}]({p['html_url']})")
            else:
                lines.append(f"- {p['name']} *(private)*")
        lines.append("")
    lines += ["### Current Stack Signals", "", lang_line, "", "<!-- AUTO:END -->"]
    return "\n".join(lines)

def update_readme(block):
    text = README.read_text(encoding="utf-8")
    start = "<!-- AUTO:START -->"
    end = "<!-- AUTO:END -->"
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        text = before + "\n\n" + block + ("\n\n" + after if after else "\n")
    else:
        marker = "## 🗺️ Project Ecosystem"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip()
        text += "\n\n---\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8")

def update_manifest(projects):
    MANIFEST.write_text(json.dumps({"projects":[{"name":p["name"],"visibility":p.get("visibility","public")} for p in projects]}, indent=2) + "\n", encoding="utf-8")

def main():
    projects = merged_projects()
    MAP.parent.mkdir(parents=True, exist_ok=True)
    MAP.write_text(make_svg(projects), encoding="utf-8")
    update_readme(dynamic_block(projects))
    update_manifest(projects)
    print(f"Profile synced with {len(projects)} projects")

if __name__ == "__main__":
    main()
