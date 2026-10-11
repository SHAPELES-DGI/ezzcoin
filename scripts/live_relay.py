#!/usr/bin/env python3
"""Ezzcoins live price relay.

Watches FUT.GG's public FC 27 price manifest (the same CDN files fut.gg's own pages load).
Whenever FUT.GG publishes new prices, it rewrites live-prices.json in the exact format the
Ezzcoins site already reads, so visitors get new prices within about a minute.
Never connects to an EA account and never retries past an access denial.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import itertools
import json
import os
import sys
import time

import requests

MANIFEST = "https://r2.fut.gg/27/manifest.json"
FILES = ["player-prices-index", "player-prices-ps5-dyn", "player-prices-pc-dyn"]
OUT = "/opt/ezzcoins/public/live-prices.json"
CHECK_EVERY = 20   # seconds between manifest checks (the manifest is about 2 KB)
RETRY = 60         # wait after an ordinary error
BACKOFF = 900      # wait 15 minutes after an access denial or rate limit

s = requests.Session()
s.headers.update({"User-Agent": "Ezzcoins/1.0 (public FC27 price reader)", "Accept": "application/json"})


class Denied(Exception):
    pass


def utc(timestamp=None):
    when = datetime.fromtimestamp(timestamp, timezone.utc) if timestamp else datetime.now(timezone.utc)
    return when.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_json(url):
    response = s.get(url, timeout=30)
    if response.status_code in (401, 403, 429):
        raise Denied(f"{url} -> HTTP {response.status_code}")
    response.raise_for_status()
    return response.json()


def decode(index, console, pc):
    ids = list(itertools.accumulate([index["id0"]] + index["d"]))
    if index.get("v") != 2 or console.get("v") != 2 or pc.get("v") != 2:
        raise ValueError("Unrecognized upstream price format")
    if len(ids) < 15000 or len(ids) != len(set(ids)) or any(type(i) is not int or i <= 0 for i in ids):
        raise ValueError("Incomplete or invalid FC 27 item index")
    for platform in (console, pc):
        if len(platform["p"]) != len(ids) or len(platform["s"]) != len(ids):
            raise ValueError("Price/index length mismatch")
        if any(type(p) is not int or p < 0 or p > 15000000 for p in platform["p"]):
            raise ValueError("Invalid coin value")
        if any(type(st) is not int or st not in range(5) for st in platform["s"]):
            raise ValueError("Unrecognized card status")
    # Only status 0 is a transferable market card. Other prices can be SBC costs.
    return [[i, cp if cs == 0 and cp > 0 else None, pp if ps == 0 and pp > 0 else None, cs, ps]
            for i, cp, pp, cs, ps in zip(ids, console["p"], pc["p"], console["s"], pc["s"])]


def publish(manifest):
    urls = {n: f"https://r2.fut.gg/27/{n}.v{manifest['_version']}.{manifest[n]}.json" for n in FILES}
    with ThreadPoolExecutor(max_workers=3) as pool:
        blobs = list(pool.map(get_json, urls.values()))
    rows = decode(*blobs)
    stamps = manifest["_published_at"]
    published = {"console": utc(stamps["player-prices-ps5-dyn"]), "pc": utc(stamps["player-prices-pc-dyn"])}
    now = time.time()
    for key in ("player-prices-ps5-dyn", "player-prices-pc-dyn"):
        age = now - stamps[key]
        if age < -300 or age > 86400:
            raise ValueError("Source publication time is missing, future-dated or more than a day old")
    output = {"game": "FC 27", "source": "FUT.GG", "sourceUrl": "https://www.fut.gg/", "retrievedAt": utc(),
              "relay": "api.ezzcoins.com", "quoteMetadata": {}, "publishedAt": published,
              "priceType": "lowestBuyNow",
              "coverage": {"feedCards": len(rows), "consolePriced": sum(r[1] is not None for r in rows),
                           "pcPriced": sum(r[2] is not None for r in rows)},
              "cols": ["id", "console", "pc", "consoleState", "pcState"], "rows": rows,
              "statusLabels": {"0": "Market card", "1": "SBC", "2": "Objective", "3": "No market price", "4": "Token reward"},
              "sourceFiles": urls}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    temporary = OUT + ".tmp"
    with open(temporary, "w") as handle:
        json.dump(output, handle, ensure_ascii=False, separators=(",", ":"))
    os.replace(temporary, OUT)
    return output


def main():
    once = "--once" in sys.argv
    last = None
    while True:
        try:
            manifest = get_json(MANIFEST)
            key = (manifest.get("_version"),) + tuple(manifest.get(n) for n in FILES)
            if key != last:
                output = publish(manifest)
                last = key
                c = output["coverage"]
                print(f"{time.strftime('%H:%M:%S')} published {c['feedCards']} cards "
                      f"({c['consolePriced']} console / {c['pcPriced']} PC priced), "
                      f"FUT.GG time {output['publishedAt']['console']}", flush=True)
            if once:
                break
            time.sleep(CHECK_EVERY)
        except Denied as error:
            print(f"{time.strftime('%H:%M:%S')} DENIED, pausing 15 min: {error}", flush=True)
            if once:
                sys.exit(1)
            time.sleep(BACKOFF)
        except Exception as error:
            print(f"{time.strftime('%H:%M:%S')} PROBLEM, keeping last prices: {error}", flush=True)
            if once:
                sys.exit(1)
            time.sleep(RETRY)


if __name__ == "__main__":
    main()
