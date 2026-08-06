#!/usr/bin/env python3
"""Point Cloudflare zones at GitHub Pages.

Converges each zone to exactly the GitHub Pages record set at the apex and www:
four A, four AAAA, and a CNAME for www. Everything is created DNS-only
(proxied=False) - a proxied record breaks GitHub's HTTP-01 challenge, so the
Let's Encrypt certificate never issues.

Only A/AAAA/CNAME records at the apex and www are touched. MX, TXT, and any
other name are left alone, so mail and verification records survive.

    python3 cf_pages_dns.py <zone> [<zone>...] [--apply]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("CF_BLOCK", "cloudflare-dns")
import cf

A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
AAAA = ["2606:50c0:8000::153", "2606:50c0:8001::153",
        "2606:50c0:8002::153", "2606:50c0:8003::153"]
TARGET = "shuffman.github.io"
MANAGED = {"A", "AAAA", "CNAME"}


def desired(zone):
    return ([(zone, "A", v) for v in A] +
            [(zone, "AAAA", v) for v in AAAA] +
            [(f"www.{zone}", "CNAME", TARGET)])


def run(zone, apply):
    zid = cf.zone_id(zone)
    if not zid:
        print(f"!! {zone}: zone not found"); return False
    got = cf.call("GET", f"/zones/{zid}/dns_records?per_page=200").get("result", [])

    names = {zone, f"www.{zone}"}
    want = set(desired(zone))
    have = {(r["name"], r["type"], r["content"]): r for r in got}

    # Delete only managed types at apex/www that aren't wanted, or are proxied.
    stale = [r for k, r in have.items()
             if r["name"] in names and r["type"] in MANAGED
             and (k not in want or r.get("proxied"))]
    missing = [t for t in want
               if t not in have or have[t].get("proxied")]

    print(f"--- {zone} ({len(got)} records) ---")
    for r in stale:
        tag = " [proxied]" if r.get("proxied") else ""
        print(f"  DEL  {r['type']:5} {r['name']:26} {r['content']}{tag}")
        if apply:
            d = cf.call("DELETE", f"/zones/{zid}/dns_records/{r['id']}")
            if not d.get("success"):
                print(f"       FAILED: {d.get('errors')}")
    for name, rtype, content in missing:
        print(f"  ADD  {rtype:5} {name:26} {content}")
        if apply:
            d = cf.call("POST", f"/zones/{zid}/dns_records",
                        {"type": rtype, "name": name, "content": content,
                         "ttl": 1, "proxied": False,
                         "comment": "GitHub Pages"})
            if not d.get("success"):
                print(f"       FAILED: {d.get('errors')}")
    if not stale and not missing:
        print("  (already converged)")
    return True


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    zones = [a for a in sys.argv[1:] if not a.startswith("--")]
    for z in zones:
        run(z, apply)
    print("\n" + ("APPLIED" if apply else "DRY RUN - pass --apply to write"))
