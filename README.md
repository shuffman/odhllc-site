# odhllc-site

The public web page for **ODH LLC** — the holding company that owns Garage
Buddy and Workout Buddy.

## Pages

| Path | File | Used for |
|---|---|---|
| `/` | `site/index.html` | Landing page — what the company is, what it owns |

## Serving

Static files in `site/`, published to **GitHub Pages** by
`.github/workflows/pages.yml` on every push to `main`. TLS is GitHub's
(Let's Encrypt), issued automatically for the custom domain.

`site/CNAME` pins the custom domain to `odhllc.com`. **Don't delete it** —
GitHub rewrites the repo's Pages domain setting from this file on each deploy,
so removing it unsets the custom domain.

## Adding a page

GitHub Pages has no `try_files`, so clean URLs come from directories, not
rewrites. A page at `/about` must live at `site/about/index.html` — a file at
`site/about.html` only answers on `/about.html`.

## Domain

`odhllc.com` — registered at DreamHost, DNS also at DreamHost (`ns1-3.dreamhost.com`).
Apex `A`/`AAAA` records point at GitHub's Pages anycast addresses; `www` is a
`CNAME` to `shuffman.github.io`.

## Related

- [`garage-buddy-site`](https://github.com/shuffman/garage-buddy-site) — garage-buddy.app
- [`workout-buddy-site`](https://github.com/shuffman/workout-buddy-site) — workout-buddy.me
