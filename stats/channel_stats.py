#!/usr/bin/env python3
"""Rank the channels FWA Mesh observers hear, for the landing page.

Every INTERVAL seconds this reads CoreScope's public API and writes OUT (JSON):
messages in the last 7 days and 24 hours, distinct senders, and when each channel
was last heard. Counts are unique messages, not observer receptions. It's the same
idea as Porchlight's "busiest channels", but built from every observer feeding the
site instead of from one repeater.

Standard library only. Settings come from environment variables (see below).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = os.environ.get("CORESCOPE_API", "http://corescope:3000").rstrip("/")
OUT = os.environ.get("OUT", "/out/channels.json")
INTERVAL = int(os.environ.get("INTERVAL", "600"))
WINDOW_DAYS = int(os.environ.get("WINDOW_DAYS", "7"))
PAGE = 500
MAX_PAGES = int(os.environ.get("MAX_PAGES", "10"))  # caps work per channel at 5000 messages


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "fwamesh-channel-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def channel_stats(ch, now):
    since7 = now - timedelta(days=WINDOW_DAYS)
    since1 = now - timedelta(days=1)
    n7 = n1 = 0
    senders, senders1 = set(), set()
    oldest = None
    complete = False
    path = "/api/channels/" + urllib.parse.quote(ch["hash"], safe="") + "/messages"
    for page in range(MAX_PAGES):
        d = get(f"{path}?limit={PAGE}&offset={page * PAGE}")
        msgs = d.get("messages") or []
        for m in msgs:
            t = ts(m["timestamp"])
            oldest = t if oldest is None or t < oldest else oldest
            if t >= since7:
                n7 += 1
                if m.get("sender"):
                    senders.add(m["sender"])
                if t >= since1:
                    n1 += 1
                    if m.get("sender"):
                        senders1.add(m["sender"])
        # Pages run newest to oldest; stop once a page reaches past the window or the data ends.
        if len(msgs) < PAGE or (page + 1) * PAGE >= d.get("total", 0):
            complete = True
            break
        if msgs and min(ts(m["timestamp"]) for m in msgs) < since7:
            break
    return {
        "messages7d": n7,
        "messages24h": n1,
        "senders7d": len(senders),
        "senders24h": len(senders1),
        "capped": not complete and oldest is not None and oldest >= since7,
        # Only known when we've read the channel's whole history.
        "firstHeard": oldest.isoformat().replace("+00:00", "Z") if complete and oldest else None,
    }


def build():
    now = datetime.now(timezone.utc)
    since7 = now - timedelta(days=WINDOW_DAYS)
    rows = []
    for ch in get("/api/channels").get("channels", []):
        if ch.get("encrypted") or not ch.get("lastActivity") or ts(ch["lastActivity"]) < since7:
            continue
        s = channel_stats(ch, now)
        if not s["messages7d"]:
            continue
        name = ch.get("name") or ch["hash"]
        first = s.pop("firstHeard")
        rows.append({
            "name": name,
            "hash": ch["hash"],
            "lastHeard": ch["lastActivity"],
            "firstHeard": first,
            **s,
        })
    # "New" only means something once the site has more history than the window.
    starts = [ts(r["firstHeard"]) for r in rows if r["firstHeard"]]
    history = bool(starts) and min(starts) < since7 - timedelta(days=1)
    for r in rows:
        r["new"] = history and bool(r["firstHeard"]) and ts(r.pop("firstHeard")) >= since7
        r.pop("firstHeard", None)
    rows.sort(key=lambda r: (-r["messages7d"], -r["senders7d"], r["name"]))
    return {
        "generated": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "windowDays": WINDOW_DAYS,
        "channels": rows,
    }


def write(data):
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    os.replace(tmp, OUT)


def main():
    once = "--once" in sys.argv
    while True:
        try:
            data = build()
            write(data)
            print(f"{data['generated']} wrote {len(data['channels'])} channels", flush=True)
        except Exception as e:  # keep the last good file and try again next round
            print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} error: {e!r}", file=sys.stderr, flush=True)
            if once:
                sys.exit(1)
        if once:
            return
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
