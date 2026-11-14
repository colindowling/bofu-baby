"""Shared GA4 / Search Console helpers for set_tracking.py and build_blog.py."""

from __future__ import annotations

import re
from pathlib import Path

GA_PLACEHOLDER = "G-XXXXXXXXXX"
GA_RE = re.compile(r"^G-[A-Z0-9]{6,}$")
GA_ASSIGN_RE = re.compile(r'var GA_ID = "G-[A-Z0-9]+";')
GSC_FILE_RE = re.compile(r"^google[A-Za-z0-9]+\.html$")
GSC_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
GSC_META_RE = re.compile(
    r'<meta\s+[^>]*name="google-site-verification"[^>]*>',
    re.IGNORECASE,
)


def valid_ga(value: str) -> bool:
    return bool(GA_RE.fullmatch(value)) and value != GA_PLACEHOLDER


def classify_gsc(value: str) -> str:
    """Return 'file' or 'meta'. Raise ValueError when the value matches neither."""
    if GSC_FILE_RE.fullmatch(value):
        return "file"
    if GSC_TOKEN_RE.fullmatch(value) and not value.lower().endswith(".html"):
        return "meta"
    raise ValueError(
        "gsc value must be a verification filename like google1234abcd.html "
        "or a meta content token (letters, digits, underscore, hyphen)"
    )


def verification_body(filename: str) -> str:
    if not GSC_FILE_RE.fullmatch(filename):
        raise ValueError(f"not a Google verification filename: {filename}")
    return f"google-site-verification: {filename}\n"


def replace_ga_id(source: str, ga_id: str) -> str:
    if not valid_ga(ga_id):
        raise ValueError(f"GA4 id must look like G-XXXXXXX and not {GA_PLACEHOLDER}")
    updated, count = GA_ASSIGN_RE.subn(f'var GA_ID = "{ga_id}";', source, count=1)
    if count != 1:
        raise ValueError("assets/track.js is missing the GA_ID assignment")
    if GA_ASSIGN_RE.search(updated) is None:
        raise ValueError("GA_ID assignment did not stick")
    return updated


def read_token(path: Path) -> str | None:
    if not path.is_file():
        return None
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        return None
    if not GSC_TOKEN_RE.fullmatch(token):
        raise ValueError(f"{path.name} is not a safe Search Console token")
    return token


def strip_gsc_meta(page: str) -> str:
    return GSC_META_RE.sub("", page)


def apply_gsc_meta(page: str, token: str | None) -> str:
    """Insert or replace the google-site-verification meta tag. No token leaves the page unchanged."""
    if not token:
        return page
    if not GSC_TOKEN_RE.fullmatch(token):
        raise ValueError("Search Console token has characters that cannot go in a meta attribute")
    stripped = strip_gsc_meta(page)
    tag = f'<meta name="google-site-verification" content="{token}">'
    charset = re.search(r'<meta charset="utf-8">', stripped, re.IGNORECASE)
    if charset:
        at = charset.end()
        return stripped[:at] + tag + stripped[at:]
    head = re.search(r"<head[^>]*>", stripped, re.IGNORECASE)
    if not head:
        raise ValueError("HTML page has no head for the Search Console meta tag")
    at = head.end()
    return stripped[:at] + tag + stripped[at:]
