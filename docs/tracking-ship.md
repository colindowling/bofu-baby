# Ship GA4 and Search Console in one command

`assets/track.js` keeps the placeholder `G-XXXXXXXXXX` until you stage a real measurement ID. While that placeholder is in place, gtag is not loaded.

`scripts/set_tracking.py` is the only edit. Do not run it with a live ID until you mean to ship that ID. The checks in `scripts/test_set_tracking.py` use fake values in a temp directory.

```bash
python3 scripts/set_tracking.py --ga G-XXXXXXX
python3 scripts/set_tracking.py --gsc google1234abcd.html
python3 scripts/set_tracking.py --gsc YOUR_META_CONTENT_TOKEN
python3 scripts/set_tracking.py --ga G-XXXXXXX --gsc google1234abcd.html
```

`--ga` must match `G-` plus at least six letters or digits. The placeholder is rejected.

`--gsc` is one of:

- An HTML-file verification name such as `google1234abcd.html`. The script writes that file at the repo root. The body is one line: `google-site-verification: google1234abcd.html`. `scripts/build_blog.py` copies every root `google*.html` file into `_static/`, which is the directory App Platform publishes.
- Anything else that is a meta content token (letters, digits, `_`, `-`, 8 to 128 characters). The script stores it in `scripts/gsc-meta.txt`. The build injects `<meta name="google-site-verification" content="...">` into the head of every public HTML page and into `scripts/templates/post.html` and `scripts/templates/blog-index.html`, so the next `python3 scripts/build_blog.py` keeps the tag.

Passing a file removes a previous meta token. Passing a meta token removes previous `google*.html` verification files. The script then runs `scripts/build_blog.py` and prints a checklist.

Commit the result, including `_static/` and, for the meta method, `scripts/gsc-meta.txt`. This app does not run a build on App Platform. A push of `_static/` is what goes live.

In GA4 Admin, mark these key events once the real ID is loading: `book_call_scheduled`, `contact_form_submit`, `autopsy_request`, `book_call_click`.
