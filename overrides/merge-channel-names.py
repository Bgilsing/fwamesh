#!/usr/bin/env python3
"""Add hashtag channel names to CoreScope's hashChannels so it can decrypt (and count) them.

A hashtag channel's key is derived from its name, so CoreScope can read any channel it
knows the name of. Sources:
  * LOCAL below: Fort Wayne / NEIMesh channels.
  * Porchlight's shared catalogue of channel names seen in real use
    (https://github.com/mutiny19/porchlight-openhop-plugin), checked against its index's SHA-256.

Names are only added, never removed. Usage:
  overrides/merge-channel-names.py corescope-data/config.json [--no-porchlight]
then restart CoreScope:  docker compose restart corescope
"""
import gzip
import hashlib
import json
import os
import re
import sys
import urllib.request

LOCAL = ["#nei", "#fwrc", "#weather-alert", "#bot", "#test", "#jokes", "#porchlight"]
INDEX = "https://mutiny19.github.io/porchlight-openhop-plugin/names/index.json"
NAME = re.compile(r"^#[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fwamesh-merge-channel-names"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def porchlight_names():
    index = json.loads(fetch(INDEX))
    part = next(p for p in index["parts"] if p["name"] == "real")
    raw = fetch(INDEX.rsplit("/", 1)[0] + "/" + part["path"])
    if hashlib.sha256(raw).hexdigest() != part["sha256"]:
        sys.exit("Porchlight names: SHA-256 mismatch, not using them")
    lines = gzip.decompress(raw).decode().splitlines()
    return [n.strip() for n in lines if NAME.match(n.strip())]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    with open(path) as f:
        cfg = json.load(f)
    have = list(cfg.get("hashChannels") or [])
    seen = {n.lower() for n in have}
    new = [n for n in LOCAL + ([] if "--no-porchlight" in sys.argv else porchlight_names()) if n.lower() not in seen and not seen.add(n.lower())]
    cfg["hashChannels"] = have + new
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.chmod(tmp, os.stat(path).st_mode & 0o777)
    os.replace(tmp, path)
    print(f"{path}: added {len(new)} names, {len(cfg['hashChannels'])} total")


if __name__ == "__main__":
    main()
