#!/usr/bin/env python3
"""Build blog/<slug>/index.html from posts/*.md and refresh the index, hubs, and sitemap.

App Platform serves the committed HTML. Run this script before committing a post.
It does not run on deploy. See posts/README.md.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
BLOG_DIR = ROOT / "blog"
TEMPLATES = Path(__file__).resolve().parent / "templates"
SITE = "https://www.bofubaby.com"
ORG_NAME = "BoFu, Baby"
ORG_URL = f"{SITE}/"
LOGO = f"{SITE}/assets/logo.svg"

TOPICS = {
    "map": {
        "label": "The keyword set",
        "hub_href": "/bofu-map/",
        "hub_name": "The BoFu Map",
        "offer": "/bofu-map/",
    },
    "build": {
        "label": "The 90-day build",
        "hub_href": "/pricing/",
        "hub_name": "Pricing",
        "offer": "/pricing/",
    },
    "call": {
        "label": "The 15-minute call",
        "hub_href": "/15minutes5xtraffic/",
        "hub_name": "the free 15-minute call",
        "offer": "/15minutes5xtraffic/",
    },
    "citation": {
        "label": "Getting named by AI",
        "hub_href": "/#aeo",
        "hub_name": "how AI citation is measured",
        "offer": "/15minutes5xtraffic/",
    },
}

# Spoke lists are written between these markers. The direct-response
# page /15minutes5xtraffic/ is the offer URL for call and citation posts
# and does not receive a spoke list. See docs/linking-plan.md.
HUB_FILES = {
    "map": ROOT / "bofu-map" / "index.html",
    "build": ROOT / "pricing" / "index.html",
    "call": ROOT / "contact" / "index.html",
    "citation": ROOT / "index.html",
}

CTAS = {
    "15minutes": {
        "path": "/15minutes5xtraffic/",
        "heading": "Want leads who show up <em>ready to buy?</em>",
        "body": (
            "Start with a free 15-minute call. We'll give you five high-intent searches "
            "your buyers are making right now, where you're missing from them, and whether "
            "the AIs are naming you or your competitor. Yours to keep either way."
        ),
        "button": "Book the 15 minutes",
    },
    "bofu-map": {
        "path": "/bofu-map/",
        "heading": "Every search your buyers make. <em>Not a sample.</em>",
        "body": (
            "Five business days. The complete bottom-of-funnel keyword set for your category "
            "&mdash; usually 40 to 80 terms &mdash; scored, prioritized, and checked against "
            "what the AIs are already saying about you. $1,500. If you go on to the 90-day build, "
            "it comes off month one."
        ),
        "button": "See the BoFu Map",
    },
}

# lastmod for pages this script does not rewrite from a post date.
# /blog/ and post URLs are dated from the posts themselves.
# Unlisted landing pages. They stay out of NAV_MENU, NAV_LINKS, and the homepage.
# write_sitemap() rebuilds sitemap.xml from this list, which is what keeps them.
UNLISTED_PATHS = [
    "/how-to-get-cited-by-chatgpt/",
    "/aeo-specialist-vs-seo-agency/",
    "/bofu-content-for-saas/",
]

STATIC_SITEMAP = [
    ("https://www.bofubaby.com/", "2026-10-31"),
    ("https://www.bofubaby.com/services/", "2026-10-31"),
    ("https://www.bofubaby.com/pricing/", "2026-10-31"),
    ("https://www.bofubaby.com/bofu-map/", "2026-10-31"),
    ("https://www.bofubaby.com/about/", "2026-10-31"),
    ("https://www.bofubaby.com/contact/", "2026-10-31"),
    ("https://www.bofubaby.com/15minutes5xtraffic/", "2026-10-23"),
    ("https://www.bofubaby.com/how-to-get-cited-by-chatgpt/", "2026-11-01"),
    ("https://www.bofubaby.com/aeo-specialist-vs-seo-agency/", "2026-11-01"),
    ("https://www.bofubaby.com/bofu-content-for-saas/", "2026-11-01"),
]

NAV_LINKS = [
    ("/services/", "Services"),
    ("/pricing/", "Pricing"),
    ("/bofu-map/", "BoFu Map"),
    ("/15minutes5xtraffic/", "15 minutes"),
    ("/about/", "About"),
    ("/blog/", "Resources"),
    ("/contact/", "Contact"),
]

# Header only. Five top-level items. About, Resources, and Contact sit under Company.
# The footer keeps the flat NAV_LINKS list. Do not add pages that are not in NAV_LINKS.
NAV_MENU = [
    ("link", "/services/", "Services"),
    ("link", "/pricing/", "Pricing"),
    ("link", "/bofu-map/", "BoFu Map"),
    ("link", "/15minutes5xtraffic/", "15 minutes"),
    (
        "group",
        "company",
        "Company",
        [
            ("/about/", "About"),
            ("/blog/", "Resources"),
            ("/contact/", "Contact"),
        ],
    ),
]

CHEVRON = (
    '<svg class="chev" viewBox="0 0 10 6" fill="none" aria-hidden="true">'
    '<path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

AUTHOR = {
    "@type": "Person",
    "name": "Colin Dowling",
    "url": f"{SITE}/about/",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DURATION_RE = re.compile(r"^PT(?:\d+H)?(?:\d+M)?(?:\d+S)?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Post:
    title: str
    description: str
    slug: str
    date: str
    topic: str
    cta: str
    takeaways: list[str]
    faqs: list[dict[str, str]]
    body_md: str
    video: dict[str, str] | None = None
    body_html: str = ""
    path: Path | None = None


def parse_scalar(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        inner = raw[1:-1]
        if raw[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\n", "\n")
        return inner
    return raw


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("front matter must start with ---")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("front matter is not closed with ---")
    raw = text[4:end]
    body = text[end + 5 :].strip() + "\n"
    lines: list[tuple[int, str]] = []
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") is False and line.startswith("-") is False and ":" not in line:
            raise ValueError(f"bad front matter line: {line}")
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))

    def parse_block(i: int, indent: int) -> tuple[object, int]:
        if i >= len(lines):
            raise ValueError("unexpected end of front matter")
        if lines[i][1].startswith("- "):
            items: list[object] = []
            while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                content = lines[i][1][2:]
                i += 1
                if ":" in content and not content.startswith(('"', "'")):
                    key, _, rest = content.partition(":")
                    item: dict[str, object] = {}
                    if rest.strip():
                        item[key.strip()] = parse_scalar(rest)
                    else:
                        child_indent = lines[i][0] if i < len(lines) else indent + 2
                        val, i = parse_block(i, child_indent)
                        item[key.strip()] = val
                    while (
                        i < len(lines)
                        and lines[i][0] > indent
                        and not lines[i][1].startswith("- ")
                    ):
                        k, _, r = lines[i][1].partition(":")
                        child_indent = lines[i][0]
                        i += 1
                        if r.strip():
                            item[k.strip()] = parse_scalar(r)
                        else:
                            val, i = parse_block(i, child_indent + 2)
                            item[k.strip()] = val
                    items.append(item)
                else:
                    items.append(parse_scalar(content))
            return items, i
        obj: dict[str, object] = {}
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
            key, _, rest = lines[i][1].partition(":")
            i += 1
            if rest.strip():
                obj[key.strip()] = parse_scalar(rest)
            else:
                child_indent = lines[i][0] if i < len(lines) else indent + 2
                val, i = parse_block(i, child_indent)
                obj[key.strip()] = val
        return obj, i

    parsed, i = parse_block(0, 0)
    if i != len(lines):
        raise ValueError(f"unparsed front matter near: {lines[i][1]}")
    if not isinstance(parsed, dict):
        raise ValueError("front matter must be a mapping")
    return parsed, body


def inline(text: str) -> str:
    links: list[tuple[str, str]] = []

    def hold(match: re.Match[str]) -> str:
        links.append((match.group(1), match.group(2)))
        return f"\u0000{len(links) - 1}\u0000"

    held = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", hold, text)
    escaped = html.escape(held, quote=False)

    def strong(match: re.Match[str]) -> str:
        return "<strong>" + match.group(1) + "</strong>"

    def em(match: re.Match[str]) -> str:
        return "<em>" + match.group(1) + "</em>"

    escaped = re.sub(r"\*\*([^*]+)\*\*", strong, escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", em, escaped)

    def put(match: re.Match[str]) -> str:
        label, href = links[int(match.group(1))]
        safe_href = html.escape(href, quote=True)
        return f'<a href="{safe_href}">{inline(label)}</a>'

    return re.sub(r"\u0000(\d+)\u0000", put, escaped)


def render_markdown(md: str) -> str:
    lines = md.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(f"<h3>{inline(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(f"<h2>{inline(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:].strip())}</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("## ", "### ", "- ")):
            para.append(lines[i].strip())
            i += 1
        blocks.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(blocks)


def insert_mid_cta(body_html: str, cta_html: str) -> str:
    parts = re.split(r"(?=<h2>)", body_html)
    h2_at = [n for n, part in enumerate(parts) if part.startswith("<h2>")]
    if len(h2_at) >= 2:
        idx = h2_at[1]
        # Place the mid CTA after the second h2 and the content that belongs to it,
        # which is the next part if that part does not itself start a new h2.
        insert_at = idx + 1
        if insert_at < len(parts) and not parts[insert_at].startswith("<h2>"):
            insert_at += 1
        # The second section is parts[idx] plus any following non-h2 chunk already counted.
        # Additional h2s stay after the CTA.
        return "\n".join(parts[:insert_at]) + "\n" + cta_html + "\n" + "\n".join(parts[insert_at:])
    return body_html + "\n" + cta_html


def load_post(path: Path) -> Post:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    required = ["title", "description", "slug", "date", "topic", "takeaways", "faqs"]
    missing = [key for key in required if key not in meta]
    if missing:
        raise ValueError(f"{path.name}: missing {', '.join(missing)}")
    slug = str(meta["slug"])
    if not SLUG_RE.match(slug):
        raise ValueError(f"{path.name}: slug must be lowercase words separated by hyphens")
    if path.stem != slug:
        raise ValueError(f"{path.name}: file name must match slug ({slug})")
    if not DATE_RE.match(str(meta["date"])):
        raise ValueError(f"{path.name}: date must be YYYY-MM-DD")
    datetime.strptime(str(meta["date"]), "%Y-%m-%d")
    topic = str(meta["topic"])
    if topic not in TOPICS:
        raise ValueError(f"{path.name}: topic must be one of {', '.join(TOPICS)}")
    cta = str(meta.get("cta") or "15minutes")
    if cta not in CTAS:
        raise ValueError(f"{path.name}: cta must be 15minutes or bofu-map")
    takeaways = meta["takeaways"]
    if not isinstance(takeaways, list) or not all(isinstance(item, str) and item.strip() for item in takeaways):
        raise ValueError(f"{path.name}: takeaways must be a list of strings")
    if not 3 <= len(takeaways) <= 6:
        raise ValueError(f"{path.name}: takeaways must be 3 to 6 items")
    faqs = meta["faqs"]
    if not isinstance(faqs, list) or not 3 <= len(faqs) <= 5:
        raise ValueError(f"{path.name}: faqs must be 3 to 5 items")
    clean_faqs = []
    for n, item in enumerate(faqs, 1):
        if not isinstance(item, dict) or "q" not in item or "a" not in item:
            raise ValueError(f"{path.name}: faq {n} needs q and a")
        clean_faqs.append({"q": str(item["q"]).strip(), "a": str(item["a"]).strip()})
    video = None
    if meta.get("video"):
        video = normalize_video(path.name, meta["video"])
    post = Post(
        title=str(meta["title"]).strip(),
        description=str(meta["description"]).strip(),
        slug=slug,
        date=str(meta["date"]),
        topic=topic,
        cta=cta,
        takeaways=[str(item).strip() for item in takeaways],
        faqs=clean_faqs,
        body_md=body,
        video=video,
        path=path,
    )
    if body.count("\n## ") + (1 if body.startswith("## ") else 0) < 2:
        raise ValueError(f"{path.name}: body needs at least two ## headings so the mid-article CTA has a place to land")
    post.body_html = render_markdown(body)
    return post


def normalize_video(name: str, video: object) -> dict[str, str]:
    if not isinstance(video, dict):
        raise ValueError(f"{name}: video must be a mapping")
    youtube_id = str(video.get("youtube_id") or "").strip()
    embed = str(video.get("embed_url") or "").strip()
    thumb = str(video.get("thumbnail_url") or "").strip()
    if youtube_id:
        if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", youtube_id):
            raise ValueError(f"{name}: youtube_id looks wrong")
        embed = embed or f"https://www.youtube.com/embed/{youtube_id}"
        thumb = thumb or f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg"
    required = ["name", "description", "upload_date", "duration"]
    missing = [key for key in required if not str(video.get(key) or "").strip()]
    if missing or not embed or not thumb:
        raise ValueError(
            f"{name}: video needs name, description, upload_date, duration, "
            "and youtube_id (or both embed_url and thumbnail_url)"
        )
    upload = str(video["upload_date"])
    if not DATE_RE.match(upload):
        raise ValueError(f"{name}: video upload_date must be YYYY-MM-DD")
    duration = str(video["duration"])
    if not DURATION_RE.match(duration) or duration == "PT":
        raise ValueError(f"{name}: video duration must be ISO 8601, like PT5M30S")
    return {
        "name": str(video["name"]).strip(),
        "description": str(video["description"]).strip(),
        "thumbnail_url": thumb,
        "upload_date": upload,
        "embed_url": embed,
        "duration": duration,
        "youtube_id": youtube_id,
    }


def load_posts() -> list[Post]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        posts.append(load_post(path))
    slugs = [post.slug for post in posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate slugs")
    posts.sort(key=lambda post: (post.date, post.slug), reverse=True)
    return posts


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def jsonld(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    raw = raw.replace("<", "\\u003c")
    return f'<script type="application/ld+json">\n{raw}\n</script>'


def org() -> dict:
    return {"@type": "Organization", "name": ORG_NAME, "url": ORG_URL, "logo": {"@type": "ImageObject", "url": LOGO}}


def cta_url(path: str, slug: str, content: str) -> str:
    query = urllib.parse.urlencode(
        {
            "utm_source": "bofubaby.com",
            "utm_medium": "blog",
            "utm_campaign": f"blog_{slug}",
            "utm_content": content,
        }
    )
    return f"{path}?{query}"


def cta_block(post: Post, content: str, end: bool) -> str:
    cta = CTAS[post.cta]
    href = cta_url(cta["path"], post.slug, content)
    if end:
        return (
            '<section class="cta"><div class="wrap">'
            f"<h2>{cta['heading']}</h2>"
            f"<p class=\"lead\">{cta['body']}</p>"
            f"<div class=\"go\"><a class=\"pill\" href=\"{attr(href)}\">{esc(cta['button'])}</a></div>"
            "</div></section>"
        )
    return (
        '<aside class="midcta">'
        f"<h2>{cta['heading']}</h2>"
        f"<p>{cta['body']}</p>"
        f"<a class=\"pill\" href=\"{attr(href)}\">{esc(cta['button'])}</a>"
        "</aside>"
    )


def _current_attr(href: str, current: str) -> str:
    return ' aria-current="page"' if href == current else ""


def nav_html(current: str) -> str:
    items = []
    for entry in NAV_MENU:
        kind = entry[0]
        if kind == "link":
            _, href, label = entry
            items.append(f'<li><a href="{href}"{_current_attr(href, current)}>{label}</a></li>')
            continue
        _, menu_id, label, children = entry
        child_html = []
        child_current = False
        for href, child_label in children:
            child_current = child_current or href == current
            child_html.append(f'<li><a href="{href}"{_current_attr(href, current)}>{child_label}</a></li>')
        current_attr = ' aria-current="page"' if child_current else ""
        items.append(
            '<li class="navdrop">'
            f'<span class="navdrop-label">{label}</span>'
            f'<button type="button" class="navdrop-trigger" aria-expanded="false" aria-haspopup="true" '
            f'aria-controls="menu-{menu_id}"{current_attr}>{label}{CHEVRON}</button>'
            f'<ul class="navdrop-menu" id="menu-{menu_id}">{"".join(child_html)}</ul>'
            "</li>"
        )
    return (
        '<nav class="site" aria-label="Primary">'
        '<a href="/" class="logo-img"><img src="/assets/logo.svg" alt="BoFu, Baby" height="60"></a>'
        '<button type="button" class="navtoggle" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu">'
        "<span></span><span></span><span></span></button>"
        f'<ul class="menu" id="site-menu">{"".join(items)}</ul></nav>'
    )


def footer_html(current: str) -> str:
    links = []
    for href, label in NAV_LINKS:
        current_attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return (
        "<footer><span>&copy; BoFu, Baby</span>"
        f"<span class=\"flinks\">{''.join(links)}</span>"
        "<span>Qualified leads. Real customers. No vanity metrics.</span></footer>"
    )


def display_date(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%-d %b %Y")


def siblings(post: Post, posts: list[Post]) -> str:
    same = [other for other in posts if other.slug != post.slug and other.topic == post.topic]
    others = [other for other in posts if other.slug != post.slug and other.topic != post.topic]
    chosen = (same + others)[:2]
    if not chosen:
        return ""
    items = []
    for other in chosen:
        items.append(
            f'<a class="sib" href="/blog/{other.slug}/"><h3>{esc(other.title)}</h3>'
            f"<p>{esc(other.description)}</p></a>"
        )
    return "<section class=\"siblings\"><h2>More notes</h2>" + "".join(items) + "</section>"


def video_html(post: Post) -> str:
    if not post.video:
        return ""
    video = post.video
    src = video["embed_url"]
    if video["youtube_id"]:
        src = f"https://www.youtube-nocookie.com/embed/{video['youtube_id']}"
    return (
        f'<figure class="video"><iframe src="{attr(src)}" title="{attr(video["name"])}" '
        'loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        'allowfullscreen></iframe></figure>'
    )


def schema_blocks(post: Post) -> str:
    url = f"{SITE}/blog/{post.slug}/"
    topic = TOPICS[post.topic]
    blocks = [
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.description,
            "datePublished": post.date,
            "dateModified": post.date,
            "inLanguage": "en",
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "url": url,
            "author": AUTHOR,
            "publisher": org(),
            "isPartOf": {"@type": "Blog", "name": "Resources", "url": f"{SITE}/blog/"},
            "about": topic["label"],
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": faq["a"]},
                }
                for faq in post.faqs
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Resources", "item": f"{SITE}/blog/"},
                {"@type": "ListItem", "position": 3, "name": post.title, "item": url},
            ],
        },
    ]
    if post.video:
        video = post.video
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "VideoObject",
                "name": video["name"],
                "description": video["description"],
                "thumbnailUrl": video["thumbnail_url"],
                "uploadDate": video["upload_date"],
                "embedUrl": video["embed_url"],
                "duration": video["duration"],
            }
        )
    return "\n".join(jsonld(block) for block in blocks)


def render_post(post: Post, posts: list[Post]) -> str:
    topic = TOPICS[post.topic]
    takeaways = "\n".join(f"<li>{esc(item)}</li>" for item in post.takeaways)
    faq_html = "\n".join(
        f"<details><summary>{esc(faq['q'])}</summary><p>{esc(faq['a'])}</p></details>" for faq in post.faqs
    )
    body = insert_mid_cta(post.body_html, cta_block(post, "inbody", end=False))
    template = (TEMPLATES / "post.html").read_text(encoding="utf-8")
    page = template
    replacements = {
        "CANONICAL": f"{SITE}/blog/{post.slug}/",
        "TITLE": esc(post.title),
        "DESCRIPTION": esc(post.description),
        "JSONLD": schema_blocks(post),
        "NAV": nav_html("/blog/"),
        "TOPIC_LABEL": esc(topic["label"]),
        "DATE": post.date,
        "DATE_DISPLAY": display_date(post.date),
        "HUB_HREF": topic["hub_href"],
        "HUB_NAME": esc(topic["hub_name"]),
        "TAKEAWAYS": takeaways,
        "VIDEO": video_html(post),
        "BODY": body,
        "FAQ": faq_html,
        "SIBLINGS": siblings(post, posts),
        "END_CTA": cta_block(post, "post_end", end=True),
        "FOOTER": footer_html("/blog/"),
    }
    # TITLE and DESCRIPTION are escaped once. Attribute contexts in the template
    # use the same escaped string, which is safe for the quotes in our copy.
    for key, value in replacements.items():
        page = page.replace(f"%%{key}%%", value)
    if "%%" in page:
        raise ValueError(f"unfilled template slot in {post.slug}")
    return page


def index_schema(posts: list[Post]) -> str:
    blog = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Resources",
        "description": "Short, practical writing on winning the searches buyers make right before they choose a vendor.",
        "url": f"{SITE}/blog/",
        "publisher": org(),
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": post.title,
                "url": f"{SITE}/blog/{post.slug}/",
                "datePublished": post.date,
            }
            for post in posts
        ],
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Resources", "item": f"{SITE}/blog/"},
        ],
    }
    items = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": post.title,
                "url": f"{SITE}/blog/{post.slug}/",
            }
            for index, post in enumerate(posts, 1)
        ],
    }
    return jsonld(blog) + "\n" + jsonld(items) + "\n" + jsonld(crumbs)


def render_index(posts: list[Post]) -> str:
    if posts:
        rows = []
        for post in posts:
            topic = TOPICS[post.topic]
            rows.append(
                f'<a class="row" href="/blog/{post.slug}/"><time datetime="{post.date}">{display_date(post.date)}</time>'
                f"<div><p class=\"tag\">{esc(topic['label'])}</p><h3>{esc(post.title)}</h3>"
                f"<p>{esc(post.description)}</p></div></a>"
            )
        listing = '<div class="posts">\n' + "\n".join(rows) + "\n</div>"
    else:
        listing = (
            '<div class="empty"><div class="eb">First posts coming soon</div>'
            "<p>We are writing the first set now. Each one takes a single buying search and shows what it takes to win it.</p>"
            '<div class="go" style="margin-top:28px"><a class="pill" href="/contact/">See the traffic you\'re missing</a></div></div>'
        )
    # Index cards use h2 for each post title. The page title is the h1 in the template.
    template = (TEMPLATES / "blog-index.html").read_text(encoding="utf-8")
    page = (
        template.replace("%%JSONLD%%", index_schema(posts))
        .replace("%%NAV%%", nav_html("/blog/"))
        .replace("%%LIST%%", listing)
        .replace("%%FOOTER%%", footer_html("/blog/"))
    )
    if "%%" in page:
        raise ValueError("unfilled template slot on the blog index")
    return page


def hub_block(topic: str, posts: list[Post]) -> str:
    spokes = [post for post in posts if post.topic == topic]
    if not spokes:
        return ""
    rows = []
    for n, post in enumerate(spokes, 1):
        rows.append(
            f'<a class="row" href="/blog/{post.slug}/"><div class="no">{n:02d}</div>'
            f"<h4>{esc(post.title)}</h4><p>{esc(post.description)}</p><div class=\"tag\">Note</div></a>"
        )
    inner = "\n".join(rows)
    if topic == "citation":
        return (
            '<div class="eyebrow" style="margin-top:56px">Notes</div>\n'
            f'<div class="idx" id="citation-notes">\n{inner}\n</div>'
        )
    headings = {
        "map": "Notes on <em>the keyword set.</em>",
        "build": "Notes on <em>the build.</em>",
        "call": "Notes on <em>the 15-minute call.</em>",
    }
    return (
        f'<section id="{topic}-notes" style="padding:72px 0"><div class="wrap">\n'
        '<div class="eyebrow">Resources</div>\n'
        f"<h2>{headings[topic]}</h2>\n"
        f'<div class="idx">\n{inner}\n</div>\n'
        "</div></section>"
    )


def replace_marked(path: Path, start: str, end: str, inner: str) -> None:
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        raise ValueError(f"{path} is missing {start}")
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    block = f"\n{inner}\n" if inner else "\n"
    path.write_text(pre + start + block + end + post, encoding="utf-8")


def write_sitemap(posts: list[Post]) -> None:
    blog_date = max((post.date for post in posts), default="2026-10-23")
    urls = []
    for loc, lastmod in STATIC_SITEMAP:
        urls.append((loc, lastmod))
        if loc == f"{SITE}/about/":
            urls.append((f"{SITE}/blog/", blog_date))
    for post in posts:
        urls.append((f"{SITE}/blog/{post.slug}/", post.date))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        lines.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


def write_llms(posts: list[Post]) -> None:
    items = []
    for post in posts:
        items.append(f"- [{post.title}]({SITE}/blog/{post.slug}/): {post.description}")
    replace_marked(ROOT / "llms.txt", "<!-- posts:start -->", "<!-- posts:end -->", "\n".join(items))


def remove_stale(posts: list[Post]) -> None:
    keep = {post.slug for post in posts}
    for child in BLOG_DIR.iterdir():
        if not child.is_dir():
            continue
        if child.name not in keep:
            shutil.rmtree(child)


def write_all(posts: list[Post]) -> None:
    BLOG_DIR.mkdir(exist_ok=True)
    for post in posts:
        dest = BLOG_DIR / post.slug
        dest.mkdir(exist_ok=True)
        (dest / "index.html").write_text(render_post(post, posts), encoding="utf-8")
    (BLOG_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    remove_stale(posts)
    for topic, path in HUB_FILES.items():
        replace_marked(path, f"<!-- hub:{topic} -->", f"<!-- /hub:{topic} -->", hub_block(topic, posts))
    write_sitemap(posts)
    write_llms(posts)


def local_exists(href: str) -> bool:
    path = href.split("#", 1)[0].split("?", 1)[0]
    if path.startswith(SITE):
        path = path[len(SITE) :]
    if not path.startswith("/"):
        return True
    if path == "/":
        return (ROOT / "index.html").is_file()
    rel = path.strip("/")
    if not rel:
        return True
    return (ROOT / rel / "index.html").is_file() or (ROOT / rel).is_file()


def check_jsonld(page: str, where: str) -> tuple[list[str], list[str]]:
    errors = []
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', page, re.S)
    if not blocks:
        return [f"{where}: no JSON-LD"], []
    types = []
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"{where}: JSON-LD does not parse ({exc})")
            continue
        if data.get("@context") != "https://schema.org":
            errors.append(f"{where}: JSON-LD @context is {data.get('@context')}")
        types.append(data.get("@type"))
        if data.get("@type") == "FAQPage":
            questions = data.get("mainEntity") or []
            if not 3 <= len(questions) <= 5:
                errors.append(f"{where}: FAQPage has {len(questions)} questions")
            for question in questions:
                if question.get("@type") != "Question" or not question.get("name"):
                    errors.append(f"{where}: FAQ question is incomplete")
                answer = (question.get("acceptedAnswer") or {}).get("text")
                if not answer:
                    errors.append(f"{where}: FAQ answer is empty")
                elif esc(answer) not in page:
                    errors.append(f"{where}: FAQ answer is not visible on the page")
        if data.get("@type") == "VideoObject":
            for key in ("name", "description", "thumbnailUrl", "uploadDate", "embedUrl", "duration"):
                if not data.get(key):
                    errors.append(f"{where}: VideoObject missing {key}")
        if data.get("@type") == "BreadcrumbList":
            items = data.get("itemListElement") or []
            if len(items) < 2:
                errors.append(f"{where}: breadcrumb is too short")
        if data.get("@type") == "BlogPosting":
            for key in ("headline", "description", "datePublished", "url"):
                if not data.get(key):
                    errors.append(f"{where}: BlogPosting missing {key}")
    return errors, types


def check_output(posts: list[Post]) -> list[str]:
    errors: list[str] = []
    index = (BLOG_DIR / "index.html").read_text(encoding="utf-8")
    index_errors, index_types = check_jsonld(index, "blog index")
    errors.extend(index_errors)
    if "Blog" not in index_types or "BreadcrumbList" not in index_types:
        errors.append(f"blog index schema types: {index_types}")
    for post in posts:
        if f'/blog/{post.slug}/' not in index:
            errors.append(f"index does not list {post.slug}")
        page_path = BLOG_DIR / post.slug / "index.html"
        page = page_path.read_text(encoding="utf-8")
        page_errors, types = check_jsonld(page, post.slug)
        errors.extend(page_errors)
        for needed in ("BlogPosting", "FAQPage", "BreadcrumbList"):
            if needed not in types:
                errors.append(f"{post.slug}: missing {needed}")
        if post.video and "VideoObject" not in types:
            errors.append(f"{post.slug}: missing VideoObject")
        if not post.video and "VideoObject" in types:
            errors.append(f"{post.slug}: VideoObject without a video")
        if "Key takeaways" not in page:
            errors.append(f"{post.slug}: missing takeaways")
        if 'href="/about/"' not in page or "Colin Dowling" not in page:
            errors.append(f"{post.slug}: missing byline linking to /about/")
        if '"name": "Colin Dowling"' not in page:
            errors.append(f"{post.slug}: BlogPosting author is not Colin Dowling")
        if 'utm_content=inbody' not in page or 'utm_content=post_end' not in page:
            errors.append(f"{post.slug}: missing CTA utm_content")
        if f"utm_campaign=blog_{post.slug}" not in page:
            errors.append(f"{post.slug}: missing utm_campaign")
        if post.video and "youtube-nocookie.com/embed/" not in page and "iframe" not in page:
            errors.append(f"{post.slug}: missing video iframe")
        for href in re.findall(r'href="([^"]+)"', page):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = href
            if href.startswith("/"):
                if not local_exists(href):
                    errors.append(f"{post.slug}: broken link {href}")
            elif not href.startswith("#"):
                errors.append(f"{post.slug}: unexpected href {href}")
        others = [other.slug for other in posts if other.slug != post.slug]
        linked = [slug for slug in others if f"/blog/{slug}/" in page]
        if len(posts) >= 3 and len(linked) < 2:
            errors.append(f"{post.slug}: expected links to 2 sibling posts, found {linked}")
        if TOPICS[post.topic]["hub_href"] not in page:
            errors.append(f"{post.slug}: missing hub link")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for post in posts:
        if f"{SITE}/blog/{post.slug}/" not in sitemap:
            errors.append(f"sitemap missing {post.slug}")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    if 'property="og:title"' not in home or '"@type": "Organization"' not in home and '"@type":"Organization"' not in home:
        errors.append("homepage is missing Organization JSON-LD or Open Graph")
    for href in ("/15minutes5xtraffic/", "/bofu-map/", "/services/"):
        if f'href="{href}"' not in home:
            errors.append(f"homepage nav/footer missing {href}")
    def has_type(text: str, name: str) -> bool:
        return f'"@type": "{name}"' in text or f'"@type":"{name}"' in text

    services = (ROOT / "services" / "index.html").read_text(encoding="utf-8")
    for name in ("Service", "Offer", "BreadcrumbList"):
        if not has_type(services, name):
            errors.append(f"services page missing {name} schema")
    for needed in ("calendly.com/30minutechat/20-minute-content-chat", 'href="/pricing/"'):
        if needed not in services:
            errors.append(f"services page missing {needed}")
    for price in ("$1,500", "$22,500", "$9,000", "$7,500", "$6,000", "$4,500", "$1,500"):
        if price not in services:
            errors.append(f"services page missing visible price {price}")
    about = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
    if not has_type(about, "AboutPage"):
        errors.append("about page missing AboutPage schema")
    main_entity = None
    for block in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', about, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"about page: JSON-LD does not parse ({exc})")
            continue
        if data.get("@type") == "AboutPage":
            main_entity = data.get("mainEntity")
    if (
        not isinstance(main_entity, dict)
        or main_entity.get("@type") != "Organization"
        or main_entity.get("name") != "BoFu, Baby"
        or main_entity.get("url") != f"{SITE}/"
    ):
        errors.append("about page AboutPage mainEntity is not the BoFu, Baby Organization")
    if 'href="/15minutes5xtraffic/"' not in about:
        errors.append('about page missing href="/15minutes5xtraffic/"')
    return errors


def check_video_slot() -> list[str]:
    """Build one in-memory post with a video and confirm VideoObject is emitted."""
    sample = Post(
        title="Example video note",
        description="An in-memory check that the optional video slot emits an embed and VideoObject.",
        slug="example-video-note",
        date="2026-10-31",
        topic="call",
        cta="15minutes",
        takeaways=["One.", "Two.", "Three."],
        faqs=[
            {"q": "Is this published?", "a": "No. This object is built in memory by the checker."},
            {"q": "Does it include a video?", "a": "Yes. The iframe and VideoObject are required when video front matter is present."},
            {"q": "Where does the CTA go?", "a": "To the 15-minute page, with the blog campaign parameters."},
        ],
        body_md="## First\n\nParagraph.\n\n## Second\n\nParagraph.\n",
        video={
            "name": "Example",
            "description": "Example description for the checker.",
            "thumbnail_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
            "upload_date": "2026-10-31",
            "embed_url": "https://www.youtube.com/embed/abcdefghijk",
            "duration": "PT2M",
            "youtube_id": "abcdefghijk",
        },
    )
    sample.body_html = render_markdown(sample.body_md)
    page = render_post(sample, [sample])
    errors, types = check_jsonld(page, "video-slot")
    if "VideoObject" not in types:
        errors.append("video-slot: VideoObject was not emitted")
    if "youtube-nocookie.com/embed/abcdefghijk" not in page:
        errors.append("video-slot: iframe missing")
    if page.count("<h2>") < 2:
        errors.append("video-slot: headings missing")
    if page.find('utm_content=inbody') > page.find('utm_content=post_end'):
        errors.append("video-slot: end CTA appears before the in-body CTA")
    # The in-body CTA sits after the second heading's paragraph.
    second = page.find("<h2>Second</h2>")
    inbody = page.find("utm_content=inbody")
    third_marker = page.find('class="faq"')
    if not (second < inbody < third_marker):
        errors.append("video-slot: in-body CTA is not between section 2 and the FAQ")
    return errors


def check_unlisted_pages() -> list[str]:
    """Landing pages that are in the sitemap and llms.txt, and absent from the nav."""
    errors: list[str] = []
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    nav_hrefs = {href for href, _label in NAV_LINKS}
    for entry in NAV_MENU:
        if entry[0] == "link":
            nav_hrefs.add(entry[1])
        elif entry[0] == "group":
            for href, _label in entry[3]:
                nav_hrefs.add(href)
    for path in UNLISTED_PATHS:
        url = f"{SITE}{path}"
        campaign = path.strip("/")
        if url not in sitemap:
            errors.append(f"sitemap missing {path}")
        if url not in llms:
            errors.append(f"llms.txt missing {path}")
        if path in nav_hrefs:
            errors.append(f"{path} is in the nav")
        if f'href="{path}"' in home:
            errors.append(f"homepage links to {path}")
        page_path = ROOT / campaign / "index.html"
        if not page_path.is_file():
            errors.append(f"missing page {path}")
            continue
        page = page_path.read_text(encoding="utf-8")
        nav_html, _, after_nav = page.partition("</nav>")
        if f'href="{path}"' in nav_html:
            errors.append(f"{path} is linked from its own nav")
        if page.count("<h1") != 1:
            errors.append(f"{path} has {page.count('<h1')} h1 elements")
        if page.count(f"utm_campaign={campaign}") < 2:
            errors.append(f"{path} needs the CTA in the body and at the end")
        if "utm_source=bofubaby" not in page or "utm_medium=bofu_page" not in page:
            errors.append(f"{path} CTA is missing utm_source or utm_medium")
        if 'href="/services/"' not in page:
            errors.append(f"{path} missing a link to /services/")
        blogs = set(re.findall(r'href="(/blog/[a-z0-9-]+/)"', page))
        if len(blogs) < 2:
            errors.append(f"{path} links to {len(blogs)} blog posts")
        for other in UNLISTED_PATHS:
            if other != path and f'href="{other}"' not in page:
                errors.append(f"{path} does not cross-link {other}")
        article = re.search(r"<article\b[\s\S]*</article>", page)
        if not article:
            errors.append(f"{path} missing article")
        else:
            chunk = re.sub(r"<script\b[\s\S]*?</script>", " ", article.group(0))
            text = html.unescape(re.sub(r"<[^>]+>", " ", chunk))
            count = len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text))
            if not 900 <= count <= 1500:
                errors.append(f"{path} word count {count} is outside 900-1500")
        answer = re.search(r'<p class="answer">(.*?)</p>', page, re.S)
        if not answer:
            errors.append(f"{path} missing the answer paragraph under the h1")
        else:
            answer_text = html.unescape(re.sub(r"<[^>]+>", " ", answer.group(1)))
            # llms.txt is one name, not two sentences.
            answer_text = re.sub(r"\.txt\b", " txt", answer_text)
            sentences = [part for part in re.split(r"[.!?]+", answer_text) if part.strip()]
            if not 2 <= len(sentences) <= 3:
                errors.append(f"{path} answer paragraph has {len(sentences)} sentences")
        lowered = page.lower()
        for banned in ("colin", "guarantee", "money-back", "money back", "ghostwrit"):
            if banned in lowered:
                errors.append(f"{path} contains {banned!r}")
        if "$" in page:
            errors.append(f"{path} contains a dollar figure")
        visible = re.sub(r"<script\b[\s\S]*?</script>", " ", page)
        blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', page, re.S)
        types = []
        saw_publisher = False
        saw_modified = False
        for block in blocks:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: JSON-LD does not parse ({exc})")
                continue
            if data.get("@context") != "https://schema.org":
                errors.append(f"{path}: JSON-LD @context is {data.get('@context')}")
            kind = data.get("@type")
            types.append(kind)
            if kind == "WebPage":
                publisher = data.get("publisher") or {}
                if publisher.get("@type") == "Organization" and publisher.get("name") == "BoFu, Baby":
                    saw_publisher = True
                if data.get("dateModified"):
                    saw_modified = True
            if kind == "Service":
                provider = data.get("provider") or {}
                if provider.get("@type") == "Organization" and provider.get("name") == "BoFu, Baby":
                    saw_publisher = True
                if data.get("dateModified"):
                    saw_modified = True
            if kind == "FAQPage":
                questions = data.get("mainEntity") or []
                if not 4 <= len(questions) <= 6:
                    errors.append(f"{path}: FAQPage has {len(questions)} questions")
                for question in questions:
                    answer_text = ((question.get("acceptedAnswer") or {}).get("text")) or ""
                    if not answer_text:
                        errors.append(f"{path}: FAQ answer is empty")
                    elif answer_text not in visible and esc(answer_text) not in visible:
                        errors.append(f"{path}: FAQ answer is not visible")
            if kind == "BreadcrumbList" and len(data.get("itemListElement") or []) < 2:
                errors.append(f"{path}: breadcrumb is too short")
        if "FAQPage" not in types or "BreadcrumbList" not in types:
            errors.append(f"{path} schema types {types}")
        if "WebPage" not in types and "Service" not in types:
            errors.append(f"{path} missing WebPage or Service schema")
        if not saw_publisher:
            errors.append(f"{path} missing publisher Organization BoFu, Baby")
        if not saw_modified:
            errors.append(f"{path} missing dateModified")
        if not after_nav:
            errors.append(f"{path} nav markup missing")
    return errors


def main() -> int:
    try:
        posts = load_posts()
        write_all(posts)
        errors = check_output(posts) + check_video_slot() + check_unlisted_pages()
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("check failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print(f"built {len(posts)} post(s): {', '.join(post.slug for post in posts) or '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
