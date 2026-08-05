# odhllc-site

The public web page for **ODH LLC** — Oregon Diversified Holdings LLC, the
holding company that owns Garage Buddy and Workout Buddy.

`odhllc.com` is the short domain for the same entity as
`oregondiversifiedholdings.com`, which is separately registered and currently
points at DreamHost shared hosting.

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

**Set the domain AFTER DNS points at GitHub.** Setting it first makes validation
fail, and GitHub then never requests a certificate — `https_certificate` stays
absent and HTTPS serves the wrong cert. Re-`PUT`ting the same value doesn't help;
clear it and set it again:

```sh
echo '{"cname":null}' | gh api -X PUT repos/shuffman/odhllc-site/pages --input -
gh api -X PUT repos/shuffman/odhllc-site/pages -f cname=odhllc.com
gh api -X PUT repos/shuffman/odhllc-site/pages -F https_enforced=true   # once approved
```

## Adding a page

GitHub Pages has no `try_files`, so clean URLs come from directories, not
rewrites. A page at `/about` must live at `site/about/index.html` — a file at
`site/about.html` only answers on `/about.html`.

## Domain

`odhllc.com` — **registered at DreamHost, DNS at Cloudflare**
(`rene.ns.cloudflare.com` / `susan.ns.cloudflare.com`). Apex `A`/`AAAA` records
point at GitHub's Pages anycast addresses; `www` is a `CNAME` to
`shuffman.github.io`.

DNS moved off DreamHost 2026-08-04: DreamHost's DNS API returns `no_such_zone`
for newly registered domains until the zone is provisioned by hand in their
panel, and the API has no command to do that. Cloudflare's API can create zones
and records outright, so all three site domains live there now.

**All records must stay DNS-only (grey cloud).** A proxied record breaks
GitHub's HTTP-01 challenge, so the Let's Encrypt certificate never issues.

Records are managed by `scratchpad/cf_pages_dns.py` (idempotent — it converges
the apex and `www` to the GitHub Pages set and leaves MX/TXT alone).

## Related

- [`garage-buddy-site`](https://github.com/shuffman/garage-buddy-site) — garage-buddy.app
- [`workout-buddy-site`](https://github.com/shuffman/workout-buddy-site) — workout-buddy.me
