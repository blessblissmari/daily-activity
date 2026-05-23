#!/usr/bin/env python3
"""update readme + activity log. formatting only, no code touched."""
import datetime
import pathlib
import random
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
LOG = ROOT / "activity.log"

QUOTES = [
    "small steps every day.",
    "consistency beats intensity.",
    "ship something, even small.",
    "the best time to start was yesterday.",
    "done is better than perfect.",
    "1% better each day.",
    "code is read more than written.",
    "simple is hard.",
    "make it work, make it right, make it fast.",
    "the only way out is through.",
    "build in public.",
    "future you will thank present you.",
    "deep work > busy work.",
    "show up. that's it.",
    "discipline equals freedom.",
]

LEAVES = ["🌱", "🌿", "🍀", "🌳", "🌲", "🪴", "🌾"]

today = datetime.date.today().isoformat()
quote = random.choice(QUOTES)
leaf = random.choice(LEAVES)

# bump log
LOG.touch(exist_ok=True)
lines = LOG.read_text().splitlines()
lines.append(f"{today} {leaf} {quote}")
LOG.write_text("\n".join(lines) + "\n")

commits = len(lines)

# streak
streak = 1
prev = datetime.date.today()
for ln in reversed(lines[:-1]):
    try:
        d = datetime.date.fromisoformat(ln.split()[0])
    except Exception:
        break
    if (prev - d).days == 1:
        streak += 1
        prev = d
    elif (prev - d).days == 0:
        continue
    else:
        break

readme = f"""# {leaf} daily activity

automated daily commits via github actions.
only touches readme + formatting. no real code changes.

## last update
- date: `{today}`
- note: *{quote}*

## stats
- commits: **{commits}**
- streak: **{streak} days**

## recent
"""

for ln in lines[-7:][::-1]:
    readme += f"- {ln}\n"

readme += "\n---\n*powered by github actions*\n"

README.write_text(readme)
print(f"updated: {today} commits={commits} streak={streak}")
