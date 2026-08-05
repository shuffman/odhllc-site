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

The custom domain (`odhllc.com`) lives in the **repo's Pages setting**, not in
the repo contents:

```sh
gh api -X PUT repos/shuffman/odhllc-site/pages -f cname=odhllc.com
```

`site/CNAME` is kept as documentation and is **inert for Actions-based
deploys** — verified 2026-08-05: three successful deploys with the file present
left the Pages `cname` setting at `null` until it was set explicitly via the
API. (The file *is* honoured by the legacy branch build, which is where the
"just commit a CNAME" advice comes from.)

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
