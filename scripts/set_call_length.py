#!/usr/bin/env python3
"""Rename public Autopsy call-length copy.

  python3 scripts/set_call_length.py --minutes 20
  python3 scripts/set_call_length.py --minutes 15

--minutes 20 is the locked name: the free 20 Minute BoFu Autopsy.
Natural duration phrases stay duration phrases ("20 minutes to 5x",
"in 20 minutes"). The product name uses "20 Minute BoFu Autopsy".

Leaves the URL /15minutes5xtraffic/, its utm values, the blog slug
what-the-free-15-minute-call-includes, the cta key 15minutes, the
Calendly slug 20-minute-content-chat, the 5x claim, and $4,900.
Does not touch durations that are not this call (customer interviews,
the Map's 45-minute readout, "15 money pages").

Then runs scripts/build_blog.py.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Longer old strings first. apply() also sorts by length.
PAIRS: list[tuple[str, str]] = [
    (
        "Book a free 15-minute call. It gets you your BoFu Autopsy:",
        "Book the free 20 Minute BoFu Autopsy:",
    ),
    (
        "Book a free 15-minute call for your BoFu Autopsy",
        "Book the free 20 Minute BoFu Autopsy",
    ),
    (
        "Start with a free 15-minute call. It gets you your BoFu Autopsy:",
        "Start with the free 20 Minute BoFu Autopsy:",
    ),
    (
        "The homepage offer is a free 15-minute call that gets you your BoFu Autopsy:",
        "The homepage offer is the free 20 Minute BoFu Autopsy:",
    ),
    (
        "The [free 15-minute call](/15minutes5xtraffic/) gets you your BoFu Autopsy:",
        "The [free 20 Minute BoFu Autopsy](/15minutes5xtraffic/) gets you:",
    ),
    (
        "A free 15-minute call gets you your BoFu Autopsy:",
        "The free 20 Minute BoFu Autopsy gets you:",
    ),
    (
        "The free 15-minute call gets you your BoFu Autopsy:",
        "The free 20 Minute BoFu Autopsy:",
    ),
    (
        "The free 15-minute call gets you your BoFu Autopsy, which",
        "The free 20 Minute BoFu Autopsy, which",
    ),
    (
        "What you leave the free 15-minute call with: your BoFu Autopsy",
        "What you leave the free 20 Minute BoFu Autopsy with",
    ),
    (
        "On a free 15-minute call you get",
        "On the free 20 Minute BoFu Autopsy you get",
    ),
    (
        "Your BoFu Autopsy, from the 15-minute call,",
        "Your 20 Minute BoFu Autopsy",
    ),
    (
        "Free 15-minute call (your BoFu Autopsy)",
        "Free 20 Minute BoFu Autopsy",
    ),
    (
        "Free 15-minute call: your BoFu Autopsy",
        "Free 20 Minute BoFu Autopsy",
    ),
    (
        "The 15-minute call gets you your Autopsy",
        "The 20 Minute BoFu Autopsy gets you",
    ),
    (
        "The call is 15 minutes, it is free, and it gets you your BoFu Autopsy.",
        "The 20 Minute BoFu Autopsy is free, and you keep it either way.",
    ),
    (
        "Book My 15-Minute Autopsy",
        "Book the 20 Minute BoFu Autopsy",
    ),
    (
        "you've lost a quarter of an hour",
        "you've lost twenty minutes",
    ),
    (
        "on a fifteen-minute call",
        "on the 20 Minute BoFu Autopsy",
    ),
    (
        "costs you fifteen minutes",
        "costs you twenty minutes",
    ),
    (
        "Fifteen minutes against",
        "Twenty minutes against",
    ),
    (
        "How the 15 minutes goes",
        "How the 20 minutes goes",
    ),
    (
        "in 15 minutes",
        "in 20 minutes",
    ),
    (
        "THE FREE 15-MINUTE BOFU AUTOPSY",
        "THE FREE 20 MINUTE BOFU AUTOPSY",
    ),
    (
        "free 15-minute BoFu Autopsy",
        "free 20 Minute BoFu Autopsy",
    ),
    (
        "Free 15-minute BoFu Autopsy",
        "Free 20 Minute BoFu Autopsy",
    ),
    (
        "the free 15-minute Autopsy",
        "the free 20 Minute BoFu Autopsy",
    ),
    (
        "The 15-minute Autopsy",
        "The 20 Minute BoFu Autopsy",
    ),
    (
        "the 15-minute Autopsy",
        "the 20 Minute BoFu Autopsy",
    ),
    (
        "15-Minute Autopsy",
        "20 Minute BoFu Autopsy",
    ),
    (
        "15-minute Autopsy",
        "20 Minute BoFu Autopsy",
    ),
    (
        "Free 15-min Autopsy",
        "Free 20 Minute BoFu Autopsy",
    ),
    (
        "15-min Autopsy",
        "20 Minute BoFu Autopsy",
    ),
    (
        "On a free 15-minute call",
        "On the free 20 Minute BoFu Autopsy",
    ),
    (
        "a free 15-minute call",
        "the free 20 Minute BoFu Autopsy",
    ),
    (
        "A free 15-minute call",
        "The free 20 Minute BoFu Autopsy",
    ),
    (
        "free 15-minute call",
        "free 20 Minute BoFu Autopsy",
    ),
    (
        "on a 15-minute call",
        "on the 20 Minute BoFu Autopsy",
    ),
    (
        "from the 15-minute call",
        "from the 20 Minute BoFu Autopsy",
    ),
    (
        "15-minute call",
        "20 Minute BoFu Autopsy",
    ),
    (
        "15-minute page",
        "20 Minute BoFu Autopsy page",
    ),
    (
        "11\u201315 min",
        "11\u201320 min",
    ),
    (
        "15 minutes",
        "20 minutes",
    ),
]

# Restored after replacements so URLs and the post slug stay put.
PROTECT = ("what-the-free-15-minute-call-includes",)
# Not this call. Held aside while --minutes 15 walks the pairs backwards.
REVERSE_PROTECT = (
    "20-minute-content-chat",
    "20-minute calls",
    "Twenty minutes. The same three questions",
)

SKIP_DIRS = {".git", "_static", "docs", "node_modules"}
SKIP_NAMES = {"set_call_length.py", "test_set_call_length.py"}
SUFFIXES = {".html", ".md", ".py", ".txt", ".xml", ".js"}


def _ordered(minutes: int) -> list[tuple[str, str]]:
    pairs = sorted(PAIRS, key=lambda item: len(item[0 if minutes == 20 else 1]), reverse=True)
    if minutes == 20:
        return pairs
    return [(new, old) for old, new in pairs]


def apply_text(text: str, minutes: int) -> str:
    if minutes not in (15, 20):
        raise ValueError("minutes must be 15 or 20")
    held: list[tuple[str, str]] = []
    phrases = PROTECT if minutes == 20 else REVERSE_PROTECT
    for index, phrase in enumerate(phrases):
        token = f"\u0000P{index}\u0000"
        if phrase in text:
            text = text.replace(phrase, token)
            held.append((token, phrase))
    for old, new in _ordered(minutes):
        text = text.replace(old, new)
    for token, phrase in held:
        text = text.replace(token, phrase)
    return text


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.name in SKIP_NAMES or path.name.startswith("test_"):
            continue
        if path.suffix.lower() not in SUFFIXES:
            continue
        yield path


def apply_tree(root: Path, minutes: int) -> list[Path]:
    changed = []
    for path in iter_files(root):
        text = path.read_text(encoding="utf-8")
        updated = apply_text(text, minutes)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set public Autopsy call-length copy and rebuild.")
    parser.add_argument("--minutes", type=int, required=True, choices=(15, 20))
    args = parser.parse_args(argv)
    try:
        changed = apply_tree(ROOT, args.minutes)
        print(f"updated {len(changed)} file(s) for {args.minutes} minutes")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_blog.py")], cwd=ROOT, check=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
