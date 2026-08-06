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
panel, and the API has no command to do that — its key exposes only
`dns-add_record`, `dns-list_records` and `dns-remove_record`. Cloudflare's API
manages records outright, so all three site domains live there now.

**All records must stay DNS-only (grey cloud).** A proxied record breaks
GitHub's HTTP-01 challenge, so the Let's Encrypt certificate never issues — and
because `.app` is HSTS-preloaded, no certificate there means unreachable rather
than merely insecure.

## DNS tooling

This repo carries the DNS scripts for **all three** site domains, not just its
own — they're one concern and splitting them three ways would be worse.

| Script | What it does |
|---|---|
| `scripts/cf.py` | Minimal Cloudflare API client; reads `~/.keys.yaml`. Also a CLI: `python3 scripts/cf.py zones` |
| `scripts/cf_pages_dns.py` | Converges a zone's apex + `www` to the GitHub Pages record set. Idempotent; leaves MX/TXT alone |
| `scripts/odh_migrate.py` | Pending migration of `oregondiversifiedholdings.com` — see below |
| `scripts/odh_zone_snapshot.txt` | Rollback reference: that domain's 16 DreamHost records as of 2026-08-04 |

```sh
python3 scripts/cf_pages_dns.py odhllc.com garage-buddy.app workout-buddy.me
python3 scripts/cf_pages_dns.py odhllc.com --apply
```

Use the **`cloudflare-dns`** key. The `cloudflare-admin` block is an R2
object-storage token despite the name and cannot touch DNS — it fails with
`10000 Authentication error`, which looks like a broken key but is the wrong
one. Neither key can *create* zones, so a new site must be added in the
Cloudflare dashboard before these scripts can manage it.

## Pending: oregondiversifiedholdings.com

`scripts/odh_migrate.py` is written and dry-run tested but **not applied**. It
turns that domain into a 301 redirect to `odhllc.com` while preserving its live
Google Workspace mail — 7 MX records and 5 `ghs.googlehosted.com` CNAMEs.

Blocked on adding the site in the Cloudflare dashboard. Then:

1. Run `python3 scripts/odh_migrate.py` (dry run) and check the plan.
2. `--apply`, then **verify all 7 MX records exist in Cloudflare**.
3. Only then change nameservers at DreamHost. Records first, delegation second —
   reversing that order bounces mail during the gap.

The redirect rule needs `Zone → Config` on the token; the "Edit zone DNS"
template doesn't grant it, and the script reports plainly if it's rejected.

## Related

- [`garage-buddy-site`](https://github.com/shuffman/garage-buddy-site) — garage-buddy.app
- [`workout-buddy-site`](https://github.com/shuffman/workout-buddy-site) — workout-buddy.me
