#!/usr/bin/env python3
"""Migrate oregondiversifiedholdings.com into Cloudflare as a redirect-only zone.

Converges the Cloudflare zone to:
  - 7 MX  -> Google Workspace          (PRESERVED - mail must not break)
  - 5 CNAME -> ghs.googlehosted.com    (PRESERVED - calendar/docs/mail/sites/start)
  - ftp, ssh A -> DreamHost            (PRESERVED - shell/file access)
  - apex + www -> 192.0.2.1, PROXIED   (redirect target; RFC 5737 test address,
                                        never actually contacted because
                                        Cloudflare's edge answers first)
  - a 301 redirect rule -> https://odhllc.com, path and query preserved

The apex/www A records MUST be proxied: redirect rules only run on proxied
traffic. Everything else MUST be DNS-only.

    python3 odh_migrate.py            # dry run
    python3 odh_migrate.py --apply
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("CF_BLOCK", "cloudflare-dns")
import cf

ZONE = "oregondiversifiedholdings.com"
DEST = "https://odhllc.com"
REDIRECT_IP = "192.0.2.1"

MX = [(10, "ASPMX.L.GOOGLE.COM"), (20, "ALT1.ASPMX.L.GOOGLE.COM"),
      (20, "ALT2.ASPMX.L.GOOGLE.COM"), (30, "ASPMX2.GOOGLEMAIL.COM"),
      (30, "ASPMX3.GOOGLEMAIL.COM"), (30, "ASPMX4.GOOGLEMAIL.COM"),
      (30, "ASPMX5.GOOGLEMAIL.COM")]
GOOGLE_CNAMES = ["calendar", "docs", "mail", "sites", "start"]
DREAMHOST_A = {"ftp": "173.236.243.67", "ssh": "173.236.243.67"}


def desired():
    out = []
    for pref, host in MX:
        out.append({"type": "MX", "name": ZONE, "content": host,
                    "priority": pref, "proxied": False})
    for sub in GOOGLE_CNAMES:
        out.append({"type": "CNAME", "name": f"{sub}.{ZONE}",
                    "content": "ghs.googlehosted.com", "proxied": False})
    for sub, ip in DREAMHOST_A.items():
        out.append({"type": "A", "name": f"{sub}.{ZONE}", "content": ip,
                    "proxied": False})
    for name in (ZONE, f"www.{ZONE}"):
        out.append({"type": "A", "name": name, "content": REDIRECT_IP,
                    "proxied": True})
    return out


def key(r):
    k = (r["name"].rstrip("."), r["type"], r["content"].rstrip(".").upper())
    return k + ((r.get("priority"),) if r["type"] == "MX" else ())


def run(apply):
    zid = cf.zone_id(ZONE)
    if not zid:
        print(f"!! zone {ZONE} does not exist in Cloudflare yet - add the site "
              f"in the dashboard first")
        return 1

    have = cf.call("GET", f"/zones/{zid}/dns_records?per_page=200").get("result", [])
    hmap = {key(r): r for r in have}
    want = desired()
    wkeys = {key(r) for r in want}

    print(f"--- {ZONE} (zone {zid[:8]}…, {len(have)} records present) ---")

    for r in want:
        cur = hmap.get(key(r))
        if cur and bool(cur.get("proxied")) == r["proxied"]:
            print(f"  ok   {r['type']:5} {r['name']:44} {r['content']}")
            continue
        verb = "FIX " if cur else "ADD "
        proxy = "proxied" if r["proxied"] else "dns-only"
        print(f"  {verb} {r['type']:5} {r['name']:44} {r['content']} [{proxy}]")
        if not apply:
            continue
        body = {k: v for k, v in r.items() if k != "proxied"}
        body["ttl"] = 1
        body["proxied"] = r["proxied"]
        body["comment"] = "migrated from DreamHost"
        if cur:
            d = cf.call("PATCH", f"/zones/{zid}/dns_records/{cur['id']}", body)
        else:
            d = cf.call("POST", f"/zones/{zid}/dns_records", body)
        if not d.get("success"):
            print(f"        FAILED: {json.dumps(d.get('errors'))[:160]}")

    # Anything imported that we don't want (e.g. the old apex A at DreamHost).
    for k, r in hmap.items():
        if k not in wkeys and r["type"] in {"A", "AAAA", "CNAME"}:
            print(f"  DEL  {r['type']:5} {r['name']:44} {r['content']}")
            if apply:
                d = cf.call("DELETE", f"/zones/{zid}/dns_records/{r['id']}")
                if not d.get("success"):
                    print(f"        FAILED: {json.dumps(d.get('errors'))[:160]}")

    # 301 redirect rule at the edge.
    print("\n--- redirect rule ---")
    rule = {
        "rules": [{
            "action": "redirect",
            "description": f"{ZONE} -> odhllc.com (301)",
            "expression": (f'(http.host eq "{ZONE}") or '
                           f'(http.host eq "www.{ZONE}")'),
            "action_parameters": {"from_value": {
                "status_code": 301,
                "target_url": {"expression":
                               f'concat("{DEST}", http.request.uri.path)'},
                "preserve_query_string": True}},
        }]
    }
    print(f"  301 {ZONE} + www.{ZONE}  ->  {DEST}<path>  (query preserved)")
    if apply:
        d = cf.call("PUT",
                    f"/zones/{zid}/rulesets/phases/"
                    f"http_request_dynamic_redirect/entrypoint", rule)
        if d.get("success"):
            print("  OK   redirect rule installed")
        else:
            print(f"  FAILED: {json.dumps(d.get('errors'))[:220]}")
            print("  (needs Zone -> Config or Dynamic Redirect edit on the token)")
    return 0


if __name__ == "__main__":
    sys.exit(run("--apply" in sys.argv))
