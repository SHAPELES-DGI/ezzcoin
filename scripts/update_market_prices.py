#!/usr/bin/env python3
"""Collect FUT.GG's public FC 27 bulk prices. Never connects to an EA account.

Prices and status flags follow the public site's own CDN index/dynamic format.
The publication time belongs to the source feed, not each individual auction.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import itertools
import json
import subprocess
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from card_catalog import extract, publish
from futbin_prices import refresh as refresh_futbin

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COLS = ["id", "baseId", "name", "ovr", "pos", "version", "club", "league", "nation", "url"]


def utc(timestamp=None):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z") if timestamp else datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_json(url):
    request = Request(url, headers={"User-Agent": "Ezzcoins/1.0 (public FC27 price reader)", "Accept": "application/json"})
    # Do not retry access denials or attempt authentication / challenge workarounds.
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


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
        if any(type(s) is not int or s not in range(5) for s in platform["s"]):
            raise ValueError("Unrecognized card status")
    # Only state 0 is a transferable market card. Other prices can be SBC costs.
    return [[i, cp if cs == 0 and cp > 0 else None, pp if ps == 0 and pp > 0 else None, cs, ps]
            for i, cp, pp, cs, ps in zip(ids, console["p"], pc["p"], console["s"], pc["s"])]


def metadata_batch(ids):
    url = "https://www.fut.gg/api/fut/players/v2/27/?ids=" + ",".join(map(str, ids))
    result = subprocess.run(["curl", "-fsSL", "--max-time", "30", url], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("FC 27 metadata request failed: " + result.stderr.strip()[:160])
    payload = json.loads(result.stdout)
    records = []
    details = {}
    for p in payload.get("data", []):
        item = p.get("eaId")
        if item not in ids or str(p.get("game")) != "27":
            raise ValueError("Metadata response does not match the requested FC 27 item IDs")
        name = p.get("commonName") or " ".join(filter(None, [p.get("firstName"), p.get("lastName")])) or p.get("cardName")
        url = p.get("url", "")
        if not name or not isinstance(p.get("overall"), int) or not url.startswith("/players/"):
            raise ValueError("Invalid player metadata")
        records.append([item, p.get("basePlayerEaId"), name, p["overall"], p.get("position", ""), p.get("rarityName", ""),
                        (p.get("club") or {}).get("name", ""), (p.get("league") or {}).get("name", ""),
                        (p.get("nation") or {}).get("name", ""), "https://www.fut.gg" + url])
        details[str(item)] = extract(p)
    time.sleep(0.3)
    return records, details


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-batches", type=int, default=16)
    parser.add_argument("--workers", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--futbin-pages", type=int, default=12)
    parser.add_argument("--futbin-player-pages", type=int, default=20)
    args = parser.parse_args()
    manifest = get_json("https://r2.fut.gg/27/manifest.json")
    names = ["player-prices-index", "player-prices-ps5-dyn", "player-prices-pc-dyn"]
    urls = {n: f"https://r2.fut.gg/27/{n}.v{manifest['_version']}.{manifest[n]}.json" for n in names}
    with ThreadPoolExecutor(max_workers=3) as pool:
        blobs = list(pool.map(get_json, urls.values()))
    rows = decode(*blobs)
    published = {p: utc(manifest["_published_at"][n]) for p, n in [("console", names[1]), ("pc", names[2])]}
    now = datetime.now(timezone.utc)
    for stamp in published.values():
        age = (now - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds()
        if age < -300 or age > 86400:
            raise ValueError("Source publication time is missing, future-dated or more than a day old")
    roster = json.loads((DATA / "players.json").read_text())
    base_ids = {int(row[roster["cols"].index("id")]) for row in roster["rows"]}
    card_path = DATA / "market-cards.json"
    cached = json.loads(card_path.read_text()) if card_path.exists() else {"cols": COLS, "rows": [], "unresolved": []}
    if cached["cols"] != COLS:
        raise ValueError("Unknown metadata cache format")
    cards = {row[0]: row for row in cached["rows"]}
    metadata_path = DATA / "card-metadata.json"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    unresolved = set(cached.get("unresolved", []))
    needed = sorted({row[0] for row in rows} - base_ids - cards.keys())
    # Retry unresolved source IDs after new IDs, so source gaps cannot starve new cards.
    checked_date = cached.get("unresolvedCheckedAt", "")[:10]
    if checked_date == utc()[:10]:
        needed = [item for item in needed if item not in unresolved]
    needed.sort(key=lambda item: (item in unresolved, item))
    exact_ids = json.loads((DATA / "card-ids.json").read_text())
    home_cards = json.loads((DATA / "newcards.json").read_text()).get("cards", [])
    home_ids = [int(exact_ids.get(str(c.get("gid") or c.get("fid"))) or c.get("eaId") or c.get("gid") or 0) for c in home_cards]
    # First discover new feed IDs; then enrich cards already shown on Home, then the rest.
    legend_ids = [item for item, row in cards.items()
                  if "icon" in row[5].lower() or "hero" in row[5].lower() or "hall of fut" in row[5].lower() or "fut gallery" in row[5].lower()
                  or row[7] in ("Icons", "Heroes")]
    enrich = legend_ids + home_ids + sorted((item for item in cards if item > 16777216), reverse=True)
    needed = list(dict.fromkeys(needed + [item for item in enrich if item and
                        (str(item) not in metadata or metadata[str(item)].get("checkedAt", "")[:10] != utc()[:10])]))
    batches = [needed[i:i + 30] for i in range(0, min(len(needed), max(0, args.metadata_batches) * 30), 30)]
    errors = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(metadata_batch, batch): batch for batch in batches}
        for n, future in enumerate(as_completed(jobs), 1):
            batch = jobs[future]
            try:
                records, details = future.result()
                metadata.update(details)
                cards.update({row[0]: row for row in records})
                unresolved.update(set(batch) - {row[0] for row in records})
                unresolved.difference_update(row[0] for row in records)
                print(f"Metadata {n}/{len(batches)}: {len(records)}/{len(batch)} matched", flush=True)
            except Exception as error:
                errors.append(str(error))
                print(f"Metadata {n}/{len(batches)} unavailable: {error}", flush=True)
                if isinstance(error, HTTPError) and error.code in (401, 403, 429):
                    for job in jobs:
                        job.cancel()
                    break
    known = base_ids | cards.keys()
    quote_metadata, futbin_coverage = refresh_futbin(DATA, rows, home_cards,
                            pages=args.futbin_pages, player_pages=args.futbin_player_pages)
    coverage = {"feedCards": len(rows), "namedCards": sum(r[0] in known for r in rows),
                "consolePriced": sum(r[1] is not None for r in rows), "pcPriced": sum(r[2] is not None for r in rows),
                "unresolvedCards": sum(r[0] not in known for r in rows)}
    output = {"game": "FC 27", "source": "FUT.GG", "sourceUrl": "https://www.fut.gg/", "retrievedAt": utc(),
              "primarySource": "FUTBIN", "fallbackSource": "FUT.GG", "quoteMetadata": quote_metadata,
              "primaryCoverage": futbin_coverage,
              "publishedAt": published, "priceType": "lowestBuyNow", "coverage": coverage,
              "cols": ["id", "console", "pc", "consoleState", "pcState"], "rows": rows,
              "statusLabels": {"0": "Market card", "1": "SBC", "2": "Objective", "3": "No market price", "4": "Token reward"},
              "sourceFiles": urls}
    checked_at = utc() if batches else cached.get("unresolvedCheckedAt")
    write_json(card_path, {"source": "FUT.GG", "updatedAt": utc(), "cols": COLS, "unresolvedCheckedAt": checked_at,
                           "rows": sorted(cards.values(), key=lambda row: row[0]), "unresolved": sorted(unresolved)})
    write_json(DATA / "live-prices.json", output)
    write_json(metadata_path, metadata)
    added = publish(DATA, metadata, {r[0]: r for r in rows}, published["console"], quote_metadata)
    print(json.dumps({"FUTBIN": futbin_coverage}), flush=True)
    print(f"Automatic card catalog: {added} new cards; {len(metadata)} exact artwork records", flush=True)
    print(json.dumps({**coverage, "publishedAt": published, "metadataErrors": errors}), flush=True)


if __name__ == "__main__":
    main()
