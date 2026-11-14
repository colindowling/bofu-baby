#!/usr/bin/env python3
"""Stage a GA4 measurement ID and/or Google Search Console verification, then rebuild.

Do not pass a live ID until you are ready to ship it. The placeholder
G-XXXXXXXXXX never loads gtag. Examples:

  python3 scripts/set_tracking.py --ga G-XXXXXXX
  python3 scripts/set_tracking.py --gsc google1234abcd.html
  python3 scripts/set_tracking.py --gsc YOUR_META_CONTENT_TOKEN
  python3 scripts/set_tracking.py --ga G-XXXXXXX --gsc google1234abcd.html

A --gsc value ending in .html is an HTML-file verification name. The script
writes that file at the repo root with the standard one-line body. Anything
else is a meta content token, stored for build_blog.py and injected into
every public HTML head, including the blog templates.

The script then runs scripts/build_blog.py so _static/ matches.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import tracking_util

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPTS / "gsc-meta.txt"
TRACK_JS = ROOT / "assets" / "track.js"


def _html_targets(root: Path) -> list[Path]:
    paths = [root / "index.html"]
    paths.extend(sorted(p for p in root.glob("*/index.html") if p.is_file()))
    blog = root / "blog"
    if blog.is_dir():
        paths.extend(sorted(blog.glob("*/index.html")))
        index = blog / "index.html"
        if index.is_file() and index not in paths:
            paths.append(index)
    templates = root / "scripts" / "templates"
    if templates.is_dir():
        paths.extend(sorted(templates.glob("*.html")))
    return [path for path in paths if path.is_file()]


def strip_meta_tree(root: Path) -> None:
    for path in _html_targets(root):
        text = path.read_text(encoding="utf-8")
        updated = tracking_util.strip_gsc_meta(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def remove_verification_files(root: Path) -> None:
    for path in root.glob("google*.html"):
        if path.is_file() and tracking_util.GSC_FILE_RE.fullmatch(path.name):
            path.unlink()


def stage(root: Path, ga: str | None, gsc: str | None, *, run_build: bool = True) -> None:
    if not ga and not gsc:
        raise ValueError("pass --ga and/or --gsc")
    if ga:
        if not tracking_util.valid_ga(ga):
            raise ValueError(
                f"--ga must match G- followed by at least 6 letters or digits, "
                f"and must not be {tracking_util.GA_PLACEHOLDER}"
            )
        track = root / "assets" / "track.js"
        track.write_text(tracking_util.replace_ga_id(track.read_text(encoding="utf-8"), ga), encoding="utf-8")
    if gsc:
        kind = tracking_util.classify_gsc(gsc)
        token_path = root / "scripts" / "gsc-meta.txt"
        if kind == "file":
            if token_path.is_file():
                token_path.unlink()
            strip_meta_tree(root)
            remove_verification_files(root)
            (root / gsc).write_text(tracking_util.verification_body(gsc), encoding="utf-8")
        else:
            remove_verification_files(root)
            token_path.write_text(gsc + "\n", encoding="utf-8")
    if run_build:
        script = root / "scripts" / "build_blog.py"
        subprocess.run([sys.executable, str(script)], cwd=root, check=True)


def checklist(ga: str | None, gsc: str | None) -> None:
    print("Checklist")
    if ga:
        print(f"[ ] GA4 measurement ID {ga} is in assets/track.js and, after the build, _static/assets/track.js")
        print("[ ] The same ID is the web stream in GA4 Admin")
        print("[ ] Load a page with ?debug_track=1 and confirm gtag.js is requested")
        print("[ ] In GA4 Admin, mark book_call_scheduled, contact_form_submit, autopsy_request, and book_call_click as key events")
    else:
        print("[ ] GA4 still uses the placeholder, so gtag is not loaded")
    if gsc and tracking_util.classify_gsc(gsc) == "file":
        print(f"[ ] {gsc} is at the site root and was copied into _static/")
        print(f"[ ] File body is: google-site-verification: {gsc}")
        print("[ ] In Search Console, choose the HTML-file method and verify")
    elif gsc:
        print("[ ] The meta token is in scripts/gsc-meta.txt")
        print("[ ] Every public HTML head, including blog templates, has google-site-verification")
        print("[ ] _static/ copies of those pages include the same meta tag")
        print("[ ] In Search Console, choose the HTML-tag method and verify")
    else:
        print("[ ] No Search Console token was staged")
    print("[ ] Commit the updated source, _static/, and (for a meta token) scripts/gsc-meta.txt")
    print("[ ] Push to the branch App Platform deploys. This app publishes _static/ and does not run a build")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage GA4 and/or Google Search Console verification, then rebuild.")
    parser.add_argument("--ga", help="GA4 measurement ID, G- followed by letters and digits")
    parser.add_argument("--gsc", help="google<token>.html filename, or a meta content token")
    args = parser.parse_args(argv)
    try:
        stage(ROOT, args.ga, args.gsc, run_build=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    checklist(args.ga, args.gsc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
