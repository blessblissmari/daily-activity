#!/usr/bin/env python3
"""touch readmes in other repos with invisible html comment. safe, no code edits."""
import datetime
import json
import os
import pathlib
import random
import subprocess
import sys
import tempfile
import urllib.request

TOKEN = os.environ["GH_PAT"]
USER = os.environ.get("GH_USER", "blessblissmari")
SELF_REPO = "daily-activity"
PICK_COUNT = int(os.environ.get("PICK_COUNT", "2"))

MARK_START = "<!-- activity-bot:start -->"
MARK_END = "<!-- activity-bot:end -->"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "daily-activity-bot",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def list_repos():
    out = []
    page = 1
    while True:
        items = api(f"/user/repos?per_page=100&affiliation=owner&page={page}")
        if not items:
            break
        out.extend(items)
        page += 1
    return [
        r for r in out
        if not r["fork"]
        and not r["archived"]
        and not r["disabled"]
        and r["owner"]["login"] == USER
        and r["name"] != SELF_REPO
        and r.get("default_branch")
    ]


def run(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def update_readme(repo_dir: pathlib.Path) -> bool:
    """find readme, add/refresh hidden block. returns true if changed."""
    candidates = ["README.md", "readme.md", "Readme.md", "README.MD", "README"]
    readme = None
    for name in candidates:
        p = repo_dir / name
        if p.exists():
            readme = p
            break
    if readme is None:
        readme = repo_dir / "README.md"
        readme.write_text(f"# {repo_dir.name}\n")

    text = readme.read_text()
    today = datetime.date.today().isoformat()
    nonce = random.randint(1000, 9999)
    block = f"{MARK_START}\n<!-- last touched: {today} #{nonce} -->\n{MARK_END}"

    if MARK_START in text and MARK_END in text:
        before, _, rest = text.partition(MARK_START)
        _, _, after = rest.partition(MARK_END)
        new = before.rstrip() + "\n\n" + block + after
    else:
        new = text.rstrip() + "\n\n" + block + "\n"

    if new == text:
        return False
    readme.write_text(new)
    return True


def touch_repo(repo) -> bool:
    name = repo["name"]
    branch = repo["default_branch"]
    print(f"\n=== {name} (branch: {branch}) ===")
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        url = f"https://x-access-token:{TOKEN}@github.com/{USER}/{name}.git"
        try:
            run(["git", "clone", "--depth=1", "--branch", branch, url, str(td / name)])
        except subprocess.CalledProcessError:
            print(f"skip {name}: clone failed")
            return False
        rd = td / name
        if not update_readme(rd):
            print(f"skip {name}: no change")
            return False
        run(["git", "config", "user.name", "github-actions[bot]"], cwd=rd)
        run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=rd)
        run(["git", "add", "-A"], cwd=rd)
        msg = random.choice([
            "docs: touch up readme",
            "docs: refresh",
            "chore(readme): update",
            "docs: minor",
            "chore: readme tidy",
        ])
        run(["git", "commit", "-m", msg], cwd=rd)
        run(["git", "push", "origin", branch], cwd=rd)
        return True


def main():
    repos = list_repos()
    print(f"found {len(repos)} candidate repos")
    if not repos:
        return
    random.shuffle(repos)
    touched = 0
    for r in repos:
        if touched >= PICK_COUNT:
            break
        try:
            if touch_repo(r):
                touched += 1
        except Exception as e:
            print(f"error on {r['name']}: {e}")
    print(f"\ntouched {touched} repo(s)")


if __name__ == "__main__":
    main()
