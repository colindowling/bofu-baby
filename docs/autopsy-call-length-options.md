# Autopsy call length

Option B is applied in this tree. The free call is the **20 Minute BoFu Autopsy**. Option A (leave the site on 15 minutes and shorten the Calendly event instead) was not taken.

`scripts/set_call_length.py --minutes 20` is what applied the copy. `--minutes 15` walks the same pairs backwards. It was not run after the apply.

## What shipped

The product name is `20 Minute BoFu Autopsy`. Running text uses that name, for example `the free 20 Minute BoFu Autopsy` and `Book the 20 Minute BoFu Autopsy`. A few lines stay durations rather than the product name, because that is how the sentence was built:

- `20 minutes to 5x` (the `5x` claim is unchanged)
- `in 20 minutes`, `How the 20 minutes goes`, `· 20 minutes`
- `Twenty minutes against…`
- `you've lost twenty minutes` (was `a quarter of an hour`)
- `it costs you twenty minutes`
- The agenda on `/15minutes5xtraffic/` is `0–5 min`, `6–10 min`, `11–20 min`. The last slot is the one that moved, so the walkthrough covers 20 minutes.

`$4,900` is unchanged. The word `audit` is not used for this call. Older lines that say `audit` are about the Map's technical review (`Technical audit` on `/bofu-map/`, and `We'll audit them in the Map` on `/pricing/`). Those are not the free call.

No visible string said `Content Chat`. The booking URL is still `https://calendly.com/30minutechat/20-minute-content-chat`. The slug stays. The event's display name in Calendly should be `20 Minute BoFu Autopsy` (that rename is in Calendly, not in this repo). The contact embed already uses `hide_event_type_details=1`.

## Option A (not applied)

Leave every public sentence on 15 minutes. In Calendly, rename the event's display name to a 15-minute Autopsy and keep the same URL. Do not change `/15minutes5xtraffic/`.

## Option B pairs (applied)

Longer sentences were rewritten first so the product name did not double up (`Start with the free 20 Minute BoFu Autopsy:` rather than "Autopsy. It gets you your BoFu Autopsy").

| Was | Is |
| --- | --- |
| `15-min Autopsy`, `15-minute Autopsy`, `15-Minute Autopsy` | `20 Minute BoFu Autopsy` |
| `free 15-minute call`, `free 15-minute BoFu Autopsy` | `free 20 Minute BoFu Autopsy` |
| `Book a free 15-minute call for your BoFu Autopsy` | `Book the free 20 Minute BoFu Autopsy` |
| `Book My 15-Minute Autopsy` | `Book the 20 Minute BoFu Autopsy` |
| `THE FREE 15-MINUTE BOFU AUTOPSY` | `THE FREE 20 MINUTE BOFU AUTOPSY` |
| `15 minutes` when it was this call | `20 minutes` |
| `11–15 min` | `11–20 min` |
| `a quarter of an hour` | `twenty minutes` |
| `fifteen minutes` / `Fifteen minutes` / `fifteen-minute call` | `twenty minutes` or `the 20 Minute BoFu Autopsy` |

The same strings were updated in page titles, meta descriptions, Open Graph and Twitter tags, JSON-LD, `llms.txt`, FAQ answers, nav and footer labels, CTA buttons, `posts/*.md`, and the CTA copy in `scripts/build_blog.py`. The blog HTML is regenerated from those sources.

Phrases from the brief that were not on the site: `15-minute traffic check`, `Book your 15 minutes`.

## Left on purpose

These still match a search for `15-minute` or contain `15minutes`. They are URLs, not the call length.

- `/15minutes5xtraffic/` on every offer link, canonical, and sitemap entry. No redirect.
- `utm_campaign=15minutes5xtraffic` and the other existing utm parameters on those links.
- Blog URL `/blog/what-the-free-15-minute-call-includes/` (slug matches the markdown filename). The visible title is `What you leave the free 20 Minute BoFu Autopsy with`.
- `utm_campaign=blog_what-the-free-15-minute-call-includes`.
- Front-matter key `cta: 15minutes`. That key selects the Autopsy CTA. It is not visible.

## Not this call (unchanged)

| File | What it says | Why it stayed |
| --- | --- | --- |
| `posts/empathy-loops-beat-guessing-what-converts.md` | `Twenty minutes. The same three questions` | Buyer interviews, not the Autopsy |
| `posts/branding-research-not-gut-feel.md` | `Book three 20-minute calls with customers` | Customer research calls |
| `posts/content-technical-buyers-wont-dismiss.md` | `Thirty minutes is often enough` | An engineer review |
| `posts/name-the-problem-you-solve.md` | `the first ten minutes of every call` | A sales call that has to explain the product |
| `posts/sell-the-outcome-for-your-customers-customer.md` | `under ten minutes`, `under 45 minutes` | A customer's procedure, not our call |
| `bofu-map/index.html` | `45-minute readout` | The Map readout |
| `15minutes5xtraffic/index.html` | `a few minutes` | How long the pitch after the brief takes, not the length of the Autopsy |
| Post closings | `15 money pages and 15 supporting posts` | The 90-day build, not the call |
| `/15minutes5xtraffic/` guarantee | `8 of 15 agreed terms`, `$4,900` | Term count and the price claim |
