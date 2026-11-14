# Contact form

The form on `/contact/` posts to Formspree. There is no App Platform function and no API key in this repo.

## Paste the form id

One place: the `action` on `#contact-form` in `contact/index.html`.

```html
action="https://formspree.io/f/FORMSPREE_FORM_ID"
```

Replace `FORMSPREE_FORM_ID` with the id from the Formspree form (the last path segment of the endpoint). Do not add the id anywhere else. `assets/contact.js` reads `form.action`.

Then rebuild and commit the page and `_static/`:

```bash
python3 scripts/build_blog.py
```

## What the form sends

With JavaScript, the page `fetch`es that action and sends `Accept: application/json`, so success and errors stay on the page. It fills two hidden fields before the request:

- `_subject` is exactly `BoFu Baby — <name> — <email>` (em dashes)
- `_replyto` is the work email

`_gotcha` is Formspree's honeypot. Leave it in the form.

Without JavaScript the browser does a normal POST to the same action. The fields still submit. `_subject` and `_replyto` stay empty, and the work-email check does not run.

## Inbox

In Formspree, set the form's notification address to `colin@colindowling.com`. That address is not in the public site. Formspree delivers to the inbox on the form, not to an address in this repo.

## Work-email block

The browser blocks free-mail domains before the request: gmail.com, googlemail.com, outlook.com, hotmail.com, live.com, msn.com, yahoo.com, ymail.com, me.com, icloud.com, and mac.com, plus subdomains of those, and regional variants such as yahoo.co.uk, hotmail.co.uk, outlook.*, and live.*. The inline error is "Please use your work email."

Formspree's free-tier spam filtering does not enforce this domain blocklist. There is no server-side copy of the list. A submission that skips JavaScript, or a client that ignores the check, can still reach the inbox.

A successful send fires the existing `contact_form_submit` event from `assets/track.js` (`window.bbTrack`). The form is marked `data-track-on="success"`, so a blocked or failed attempt does not count.
