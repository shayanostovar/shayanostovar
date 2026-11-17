#!/usr/bin/env python3
"""Update the public GitHub profile from public repositories only.

This script intentionally NEVER calls /user/repos (which can return private data),
and it never publishes internal repository names, private counts, or secrets.
"""
import html
import json
import os
import urllib.request
from pathlib import Path
from textwrap import shorten
from urllib.parse import quote

USERNAME = "shayanostovar"
ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MAP = ROOT / "assets" / "project-ecosystem.svg"
CONFIG = ROOT / "profile-projects.json"
START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"

SHOWCASE = [
    ("RasafamCRM", "ENTERPRISE SYSTEMS", "Customer operations & workflow automation", "#63e6be"),
    ("Kherad AI", "AI INFRASTRUCTURE", "Self-hosted inference & intelligent orchestration", "#9d8cff"),
    ("4U Energy Sharing", "ENERGY TECHNOLOGY", "Community-driven energy sharing tools", "#74b9ff"),
    ("Danial Pardaz", "DIGITAL PLATFORMS", "Business websites & digital product experiences", "#ffc68b"),
]


def get_public_repos():
    """The /users/{username}/repos endpoint returns publicly available repos.

    Always filter visibility again as defense in depth. Do not change this to
    /user/repos, even if a GitHub token with broader access becomes available.
    """
    items = []
    page = 1
    token = os.getenv("GITHUB_TOKEN", "")
    while True:
        url = (f"https://api.github.com/users/{USERNAME}/repos"
               f"?type=owner&per_page=100&page={page}&sort=updated")
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-profile-public-sync",
        })
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub API response; refusing to update profile")
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def load_config():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return data.get("excluded_repos", []), data.get("public_labels", {})


def public_projects():
    excluded, labels = load_config()
    excluded = set(excluded)
    result = []
    for repo in get_public_repos():
        name = repo.get("name", "")
        if (name == USERNAME or name in excluded or repo.get("private")
                or repo.get("visibility", "public") != "public"
                or repo.get("archived") or repo.get("fork")):
            continue
        label = labels.get(name, {})
        result.append({
            "name": name,
            "title": str(label.get("title") or name),
            "focus": str(label.get("focus") or repo.get("description") or "Public repository"),
            "url": f"https://github.com/{USERNAME}/{quote(name, safe='-_.')}",
        })
    return sorted(result, key=lambda item: item["name"].lower())


def svg_text(value, max_width=48):
    return html.escape(shorten(str(value), width=max_width, placeholder="…"), quote=True)


def make_map(repos):
    cols, card_w, card_h = 2, 562, 160
    public_rows = max(1, (len(repos) + 1) // 2)
    height = 680 + public_rows * 89 + 45
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 {height}" role="img" aria-label="Selected work and public repositories">',
        '<title>Shayan Ostovar: project landscape</title>',
        '<desc>Four selected case studies and an automatically updated set of public GitHub projects.</desc>',
        '<defs>',
        '  <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#101b32"/><stop offset="1" stop-color="#07101f"/></linearGradient>',
        '  <linearGradient id="stroke" x1="0" x2="1"><stop stop-color="#8b8df9"/><stop offset="1" stop-color="#4dd4c5"/></linearGradient>',
        '</defs>',
        f'<rect width="1280" height="{height}" rx="26" fill="url(#bg)"/>',
        '<rect x="24" y="24" width="1232" height="100" rx="19" fill="#16243d" stroke="#2a3e5f"/>',
        '<text x="62" y="67" fill="#9ed8ed" font-family="Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="3">PROJECT LANDSCAPE</text>',
        '<text x="62" y="98" fill="#f1f6ff" font-family="Arial,sans-serif" font-size="24" font-weight="700">Business analysis → dependable digital systems</text>',
        '<rect x="1100" y="45" width="115" height="40" rx="20" fill="#213654"/>',
        '<text x="1157" y="71" text-anchor="middle" fill="#a6e4dc" font-family="Arial,sans-serif" font-size="15" font-weight="700">SELECTED</text>',
    ]
    for i, (title, group, description, color) in enumerate(SHOWCASE):
        x, y = 62 + (i % cols) * 594, 154 + (i // cols) * 186
        s += [
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="18" fill="#16243c" stroke="#324562"/>',
            f'<rect x="{x}" y="{y+20}" width="5" height="120" rx="2.5" fill="{color}"/>',
            f'<text x="{x+27}" y="{y+42}" fill="{color}" font-family="Arial,sans-serif" font-size="14" font-weight="700" letter-spacing="2">{html.escape(group)}</text>',
            f'<text x="{x+27}" y="{y+90}" fill="#f2f6ff" font-family="Arial,sans-serif" font-size="29" font-weight="700">{html.escape(title)}</text>',
            f'<text x="{x+27}" y="{y+127}" fill="#adbed8" font-family="Arial,sans-serif" font-size="17">{html.escape(description)}</text>',
        ]
    s += [
        '<line x1="62" x2="1218" y1="555" y2="555" stroke="#38506e"/>',
        '<text x="62" y="605" fill="#f0f5ff" font-family="Arial,sans-serif" font-size="24" font-weight="700">Public GitHub projects</text>',
        f'<text x="1218" y="603" text-anchor="end" fill="#88a9c6" font-family="Arial,sans-serif" font-size="16">{len(repos)} PUBLIC REPOSITORIES</text>',
    ]
    if not repos:
        s.append('<text x="78" y="683" fill="#adbed8" font-family="Arial,sans-serif" font-size="18">No public projects available at this time.</text>')
    for i, repo in enumerate(repos):
        x, y = 62 + (i % cols) * 594, 632 + (i // cols) * 89
        s += [
            f'<rect x="{x}" y="{y}" width="{card_w}" height="75" rx="13" fill="#142238" stroke="#2e465e"/>',
            f'<circle cx="{x+25}" cy="{y+38}" r="6" fill="#52d0bc"/>',
            f'<text x="{x+43}" y="{y+32}" fill="#f2f6ff" font-family="Arial,sans-serif" font-size="18" font-weight="700">{svg_text(repo["title"], 38)}</text>',
            f'<text x="{x+43}" y="{y+57}" fill="#a6b6cd" font-family="Arial,sans-serif" font-size="14">{svg_text(repo["focus"], 59)}</text>',
        ]
    s += [
        f'<text x="62" y="{height-29}" fill="#7e99b8" font-family="Arial,sans-serif" font-size="14">Selected case studies are privately maintained · Public repositories update automatically</text>',
        '</svg>',
    ]
    return "\n".join(s) + "\n"


def safe_md(value, width=115):
    return shorten(" ".join(str(value).replace("|", "·").replace("`", "'").split()),
                   width=width, placeholder="…")


def dynamic_block(repos):
    lines = [
        START,
        "## 🌐 Public Work & Project Map",
        "",
        "A curated view of my work, plus an **automatically updated** index of public repositories.",
        "",
        '<p align="center"><img width="100%" src="https://raw.githubusercontent.com/shayanostovar/shayanostovar/main/assets/project-ecosystem.svg" alt="A map of four selected projects and my public GitHub repositories" /></p>',
        "",
        "### Public repositories",
        "",
        "| Repository | Focus |",
        "|:--|:--|",
    ]
    if repos:
        for repo in repos:
            lines.append(f'| [{safe_md(repo["title"])}]({repo["url"]}) | {safe_md(repo["focus"])} |')
    else:
        lines.append("| _No public repositories listed_ | — |")
    lines.extend([
        "",
        "<sub>Only publicly visible, non-archived repositories are listed. Private code and internal repository names are never indexed.</sub>",
        "",
        END,
    ])
    return "\n".join(lines)


def update_readme(repos):
    content = README.read_text(encoding="utf-8")
    if content.count(START) != 1 or content.count(END) != 1:
        raise RuntimeError("Missing or duplicate AUTO markers; refusing to overwrite README")
    first, tail = content.split(START, 1)
    _, last = tail.split(END, 1)
    README.write_text(first + dynamic_block(repos) + last, encoding="utf-8")


def main():
    projects = public_projects()
    MAP.parent.mkdir(parents=True, exist_ok=True)
    MAP.write_text(make_map(projects), encoding="utf-8")
    update_readme(projects)
    print(f"Updated public profile: {len(projects)} public repositories; no private inventory used")


if __name__ == "__main__":
    main()
