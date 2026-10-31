# Internal linking plan

Four topic hubs. Each one uses a page that already exists. Posts declare a `topic` in front matter. `scripts/build_blog.py` links each post up to its hub, adds two sibling posts, and writes the spoke list onto the hub page that can hold one.

The mid-article and end calls to action are not the hub link. They go to `/15minutes5xtraffic/` (the default) or `/bofu-map/` when the post sets `cta: bofu-map`. Parameters: `utm_campaign=blog_<slug>` and `utm_content=inbody` or `utm_content=post_end`.

`/services/` is the page between the homepage and `/pricing/`. It repeats the published offers and links to Calendly and the full pricing page. It is not a topic hub, and post calls to action do not point at it.

## Hubs

| Topic | What it covers | Hub | Offer the post promotes | Where spokes are listed |
| --- | --- | --- | --- | --- |
| `map` | The finite bottom-of-funnel keyword set: alternatives, versus, pricing, best-for, switching, integrations | [/bofu-map/](/bofu-map/) | `/bofu-map/` | On `/bofu-map/` |
| `build` | The 90-day build, what ships, and the published fee | [/pricing/](/pricing/) | `/15minutes5xtraffic/` or `/bofu-map/`. The hub link is still `/pricing/` | On `/pricing/` |
| `call` | What the free 15-minute call hands over | [/15minutes5xtraffic/](/15minutes5xtraffic/) | `/15minutes5xtraffic/` | On [/contact/](/contact/), which books the same call |
| `citation` | Getting named by ChatGPT, Perplexity, Google AI Overviews, and Claude, and the 200 monthly checks | The measurement section on the homepage, [/#aeo](/#aeo) | `/15minutes5xtraffic/` for a first look. The Map's citation baseline is `/bofu-map/` | On the homepage, under that section |

`/15minutes5xtraffic/` stays a single-action page. It does not list posts. Spokes for the call topic are listed on `/contact/` instead, and every call-topic post still links up to `/15minutes5xtraffic/`.

## Rules for a new post

- Set `topic` to one hub. In the body, link to that hub in the first or second section.
- Link to two other posts. The builder appends the two siblings, preferring the same topic, so the body does not have to.
- Use `cta: 15minutes` unless the post's job is to send the reader to the Map. Build-topic posts still link to `/pricing/` as the hub.
- When a video is published, the post embeds it and the YouTube description links back to `https://www.bofubaby.com/blog/<slug>/`. The description edit happens in YouTube. This repo only emits the embed and the VideoObject.
- Do not add a cross-site link unless the post is actually about the same subject as a page on rncld.com or withants.com. None of the current notes are.

## Current spokes

| Post | Topic | Hub | CTA |
| --- | --- | --- | --- |
| `/blog/bottom-of-funnel-search-is-finite/` | `map` | `/bofu-map/` | `/bofu-map/` |
| `/blog/what-the-free-15-minute-call-includes/` | `call` | `/15minutes5xtraffic/` | `/15minutes5xtraffic/` |
| `/blog/ranking-and-getting-cited/` | `citation` | `/#aeo` | `/15minutes5xtraffic/` |

`build` has no spoke yet. A post with `topic: build` is added the same way, and the pricing page picks it up on the next build.
