#!/usr/bin/env python3
"""Minimal Cloudflare API client reading creds from ~/.keys.yaml.

Defaults to the `cloudflare-dns` block. Use that one — the `cloudflare-admin`
block is an **R2 object-storage token** despite its name (it carries
`s3_access_id` / `s3_access_key`), and holds account and zone *read* only. It
cannot touch DNS: `/zones` succeeds while `/zones/{id}/dns_records` returns
`10000 Authentication error`, which reads like a broken key but is the wrong
key. Override with `CF_BLOCK=<name>` if that ever changes.

Neither block's token can create zones (`com.cloudflare.api.account.zone.create`
is not granted), so new sites must be added in the Cloudflare dashboard first.

No PyYAML on this box, so the block is parsed with a tiny scanner - the entry is
flat `key: value` pairs under a top-level heading.

Usable as a library or CLI:
    python3 cf.py verify
    python3 cf.py zones
    python3 cf.py add-zone <name>
    python3 cf.py records <zone-name>
"""
import os, sys, json, urllib.request, urllib.error

BASE = "https://api.cloudflare.com/client/v4"
KEYS = os.path.expanduser("~/.keys.yaml")


def creds(block=None):
    block = block or os.environ.get("CF_BLOCK", "cloudflare-dns")
    out, inside = {}, False
    with open(KEYS) as f:
        for line in f:
            if line.startswith(block + ":"):
                inside = True
                continue
            if inside:
                if line.strip() and not line[0].isspace():
                    break
                if ":" in line:
                    k, _, v = line.strip().partition(":")
                    out[k.strip()] = v.strip()
    if "api_key" not in out:
        raise SystemExit(f"no api_key under {block} in {KEYS}")
    return out


C = creds()


def call(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + C["api_key"])
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)


def ok(d):
    return d.get("success") is True


def zone_id(name):
    d = call("GET", f"/zones?name={name}")
    res = d.get("result") or []
    return res[0]["id"] if res else None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        d = call("GET", "/user/tokens/verify")
        print(json.dumps(d, indent=2)[:900])
    elif cmd == "zones":
        d = call("GET", "/zones?per_page=50")
        if not ok(d):
            print(json.dumps(d, indent=2)[:900]); return
        for z in d["result"]:
            print(f"{z['name']:32} {z['status']:10} {','.join(z.get('name_servers') or [])}")
        if not d["result"]:
            print("(no zones)")
    elif cmd == "add-zone":
        name = sys.argv[2]
        d = call("POST", "/zones",
                 {"name": name, "account": {"id": C["account_id"]}, "type": "full"})
        if ok(d):
            z = d["result"]
            print(f"OK   {name}  status={z['status']}  ns={','.join(z['name_servers'])}")
        else:
            print(f"FAIL {name}  {json.dumps(d.get('errors'))}")
    elif cmd == "records":
        zid = zone_id(sys.argv[2])
        if not zid:
            print("zone not found"); return
        d = call("GET", f"/zones/{zid}/dns_records?per_page=100")
        for r in d.get("result", []):
            proxied = "proxied" if r.get("proxied") else "dns-only"
            print(f"{r['type']:6} {r['name']:32} {r['content']:24} {proxied}")


if __name__ == "__main__":
    main()
