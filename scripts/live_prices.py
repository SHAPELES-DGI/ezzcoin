#!/usr/bin/env python3
"""Fast lane: publish FUT.GG's newest public FC 27 prices for the `live` branch.

Started every few minutes by the Ezzcoins server. Reads FUT.GG's public price manifest and
downloads the three price files only when FUT.GG has published new ones since the last run.
Writes live-prices.json (same format as data/live-prices.json) and a small stamp.json into --out.
With --check DIR it also writes DIR/check.json on every run that reached FUT.GG, new prices or not,
so the site can show when Ezzcoins last checked (the `check` branch).
Never connects to an EA account and never retries past an access denial.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

from update_market_prices import decode, get_json, utc

MANIFEST = "https://r2.fut.gg/27/manifest.json"
FILES = ["player-prices-index", "player-prices-ps5-dyn", "player-prices-pc-dyn"]
STAMP_URL = "https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/live/stamp.json"


def last_sources():
    """sourceFiles from the previous run, or None when unknown (then publish anyway)."""
    try:
        request = Request(f"{STAMP_URL}?t={int(time.time())}", headers={"User-Agent": "Ezzcoins/1.0 (live branch check)"})
        with urlopen(request, timeout=15) as response:
            return json.load(response).get("sourceFiles")
    except Exception:
        return None


def build(manifest):
    urls = {n: f"https://r2.fut.gg/27/{n}.v{manifest['_version']}.{manifest[n]}.json" for n in FILES}
    with ThreadPoolExecutor(max_workers=3) as pool:
        blobs = list(pool.map(get_json, urls.values()))
    rows = decode(*blobs)
    stamps = manifest["_published_at"]
    now = time.time()
    for key in ("player-prices-ps5-dyn", "player-prices-pc-dyn"):
        age = now - stamps[key]
        if age < -300 or age > 86400:
            raise ValueError("Source publication time is missing, future-dated or more than a day old")
    published = {"console": utc(stamps["player-prices-ps5-dyn"]), "pc": utc(stamps["player-prices-pc-dyn"])}
    return {"game": "FC 27", "source": "FUT.GG", "sourceUrl": "https://www.fut.gg/", "retrievedAt": utc(),
            "lane": "live", "quoteMetadata": {}, "publishedAt": published, "priceType": "lowestBuyNow",
            "coverage": {"feedCards": len(rows), "consolePriced": sum(r[1] is not None for r in rows),
                         "pcPriced": sum(r[2] is not None for r in rows)},
            "cols": ["id", "console", "pc", "consoleState", "pcState"], "rows": rows,
            "statusLabels": {"0": "Market card", "1": "SBC", "2": "Objective", "3": "No market price", "4": "Token reward"},
            "sourceFiles": urls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="directory for live-prices.json and stamp.json")
    parser.add_argument("--check", help="directory for check.json, the time of this successful check")
    args = parser.parse_args()
    manifest = get_json(MANIFEST)
    urls = {n: f"https://r2.fut.gg/27/{n}.v{manifest['_version']}.{manifest[n]}.json" for n in FILES}
    if args.check:
        stamps = manifest.get("_published_at", {})
        check = {"checkedAt": utc(), "sourcePublishedAt": {k: utc(stamps[f]) for k, f in (("console", "player-prices-ps5-dyn"), ("pc", "player-prices-pc-dyn")) if f in stamps}}
        Path(args.check).mkdir(parents=True, exist_ok=True)
        (Path(args.check) / "check.json").write_text(json.dumps(check, separators=(",", ":")) + "\n")
    if last_sources() == urls:
        print("FUT.GG has not published new prices since the last run; nothing to publish", flush=True)
        return
    output = build(manifest)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "live-prices.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n")
    stamp = {k: output[k] for k in ("retrievedAt", "publishedAt", "coverage", "sourceFiles")}
    (out / "stamp.json").write_text(json.dumps(stamp, separators=(",", ":")) + "\n")
    c = output["coverage"]
    print(f"Published {c['feedCards']} cards ({c['consolePriced']} console / {c['pcPriced']} PC priced), "
          f"FUT.GG time {output['publishedAt']['console']}", flush=True)


if __name__ == "__main__":
    main()
