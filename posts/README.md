# Adding a post

Posts are Markdown files in this folder. The live site is static HTML on DigitalOcean App Platform, and the platform does not run a build. `scripts/build_blog.py` writes the HTML, and that HTML is what gets committed and deployed.

## Add a post

1. Copy the front matter below into `posts/<slug>.md`. The file name must match `slug`.
2. Write the body in Markdown. Use at least two `##` headings. The builder inserts the mid-article call to action after the second one.
3. From the repo root, run:

```bash
python3 scripts/build_blog.py
```

4. Commit the new `posts/<slug>.md`, the generated `blog/<slug>/index.html`, and the updated `blog/index.html`, `sitemap.xml`, and `llms.txt`. If the post's topic already has a hub block on the site, that page changes too.

The script reads every `posts/*.md` except files whose names start with `_`, and except this README. It deletes a `blog/<slug>/` directory when the matching Markdown file is gone. Re-run it after any edit. Do not hand-edit the generated HTML.

Check output is part of the same command. A bad front matter, a broken internal link, or JSON-LD that does not match the visible FAQ fails the script before you commit.

## Front matter

```yaml
---
title: "Post title"
description: "Meta description, also used as the deck and the Open Graph description."
slug: post-title
date: 2026-10-31
topic: map
cta: bofu-map
takeaways:
  - "First takeaway."
  - "Second takeaway."
  - "Third takeaway."
faqs:
  - q: "Question shown on the page and in FAQPage JSON-LD?"
    a: "The same answer, visible on the page. Three to five of these."
video:
  youtube_id: abcdefghijk
  name: "Video title"
  description: "What the video actually covers."
  upload_date: 2026-10-31
  duration: PT5M30S
---
```

`video` is optional. Omit the whole block when there is no video. With `youtube_id`, the page embeds `https://www.youtube-nocookie.com/embed/<id>` and the VideoObject uses `https://www.youtube.com/embed/<id>` plus the standard `i.ytimg.com` thumbnail. Set `embed_url` and `thumbnail_url` only when those should be something else.

| Field | Required | Values |
| --- | --- | --- |
| `title` | yes | Visible h1 and BlogPosting `headline` |
| `description` | yes | Meta description, deck, and `BlogPosting.description` |
| `slug` | yes | Lowercase hyphenated. Must match the file name. URL is `/blog/<slug>/` |
| `date` | yes | `YYYY-MM-DD`. Published and modified date. Same-day posts sort by slug |
| `topic` | yes | `map`, `build`, `call`, or `citation`. See `docs/linking-plan.md` |
| `cta` | no | `15minutes` (default) or `bofu-map`. Both the mid-article and end blocks use it |
| `takeaways` | yes | 3 to 6 strings. Rendered in the Key takeaways box |
| `faqs` | yes | 3 to 5 `{q, a}` items. Visible FAQ and FAQPage JSON-LD, same words |
| `video` | no | `name`, `description`, `upload_date`, `duration` (`PT5M30S`), and `youtube_id` or both `embed_url` and `thumbnail_url` |

Strings can be quoted or bare. Keep each value on one line. The body supports `##`, `###`, paragraphs, `-` lists, `**bold**`, `*italic*`, and `[label](/path/)`.

## What the script updates

- `blog/<slug>/index.html` with BlogPosting, FAQPage, BreadcrumbList, and VideoObject when a video is set
- `blog/index.html`
- Spoke lists marked `<!-- hub:<topic> -->` on the homepage, `/bofu-map/`, `/pricing/`, and `/contact/`
- `sitemap.xml` and the posts list in `llms.txt`

Call to action links are:

`/15minutes5xtraffic/` or `/bofu-map/` plus `utm_source=bofubaby.com`, `utm_medium=blog`, `utm_campaign=blog_<slug>`, and `utm_content=inbody` or `utm_content=post_end`.

The heading and body of those blocks are the sentences already used on the homepage and the BoFu Map page. They are not taken from the Markdown file.

Every post gets the same byline: Colin Dowling, linked to `/about/`. The BlogPosting `author` is that person. It is not a front-matter field.

## Markdown the builder accepts

Headings, paragraphs, lists, emphasis, and links. No raw HTML, images, or tables. A link to another post is optional. The builder adds two sibling links at the end, same topic first, then the next most recent posts.
