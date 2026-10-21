#!/usr/bin/env python3
"""The small slice of the player list and the card-picture list that the home page's first screen needs.

The home page shows three rows of cards (new cards, most watched, trending). Loading the whole player list
(data/players.json, about 800 KB compressed) and every card picture address (data/card-renders.json, about
550 KB) just for those rows made a first visit about 1.8 MB. This writes data/home-cards.json with only the
players and card pictures those rows can show; the full files still load as soon as a visitor opens another
tab, searches, or a row shows a card that isn't in this slice (card-art.js notices and loads the rest).

Written by the market workflow after the price, trending and desk steps. Standard library only.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
DATA = ROOT / "data"


def read(name, fallback):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def tokens(name):
    plain = unicodedata.normalize("NFD", str(name or "")).encode("ascii", "ignore").decode().lower()
    return set(re.findall(r"[a-z0-9]+", plain))


def fid_of(url):
    m = re.search(r"/player/(\d+)", str(url or ""))
    return int(m.group(1)) if m else None


def build():
    roster = read("players.json", {"cols": [], "rows": []})
    renders = read("card-renders.json", {})
    card_ids = read("card-ids.json", {})
    trending = read("trending.json", {}).get("cards", [])
    watched = read("prices.json", {}).get("players", {})
    top = read("topprices.json", {}).get("players", {})
    specials = read("newcards.json", {}).get("cards", []) + read("legends.json", {}).get("cards", [])
    if not roster.get("rows") or not renders:
        return None

    # Card picture keys, the way the home page looks them up: the item, the item's card-ids mapping and "f:" + item.
    items = set()
    for c in specials:                                         # looked up by "gid", or by FUT.GG "fid"
        for key in (c.get("gid"), c.get("fid"), c.get("eaId"), c.get("baseId")):
            if key not in (None, ""):
                items.add(int(key))
    for c in trending:
        if c.get("eaId"):
            items.add(int(c["eaId"]))
    for k in watched:
        items.add(int(k))
    for c in read("snapshot.json", {}).get("meta", []):        # the desk's cheap meta cards (ezzcoins-upgrade.js)
        if c.get("eaId"):
            items.add(int(c["eaId"]))

    # Players the rows can name: the watched ones, trending base cards, and trending matches by FUT.GG id or name.
    ids = {int(k) for k in watched}
    want_fids, names = set(), []
    for c in trending:
        if c.get("eaId"):
            ids.add(int(c["eaId"]))
        f = c.get("fid") if c.get("fid") not in (None, "") else fid_of(c.get("url"))
        if f is not None:
            want_fids.add(int(f))
        names.append((tokens(c.get("name")), c.get("ovr")))
    for k, p in top.items():
        if fid_of(p.get("url")) in want_fids or any(t and (t <= tokens(p.get("name")) or tokens(p.get("name")) <= t) and p.get("ovr") == o for t, o in names):
            ids.add(int(k))
            items.add(int(k))
    ci = {c: i for i, c in enumerate(roster["cols"])}
    rows = []
    for r in roster["rows"]:
        i, own = r[ci["id"]], tokens(r[ci["name"]]) | tokens(r[ci["full"]] if "full" in ci else "")
        if i in ids or any(t and (t <= own or own <= t) and r[ci["ovr"]] == o for t, o in names):
            rows.append(r)
            items.add(int(i))

    keys = set()
    for i in items:
        keys.update({str(i), "f:" + str(i)})
        if str(i) in card_ids:
            keys.add(str(card_ids[str(i)]))
    found = {k: renders[k] for k in sorted(keys) if k in renders}
    checked = sorted(k for k in keys if k not in renders and not k.startswith("f:"))
    return {"updatedAt": read("trending.json", {}).get("updatedAt") or roster.get("updatedAt"),
            "cols": roster["cols"], "rows": rows, "renders": found, "none": checked}


def main():
    out = build()
    if not out:
        print("home_cards: player list or card pictures missing, nothing written")
        return
    path = DATA / "home-cards.json"
    text = json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    strip = lambda s: re.sub(r'"updatedAt":"[^"]*"', "", s)
    if strip(old) != strip(text):
        path.write_text(text, encoding="utf-8")
    print(f"home_cards: {len(out['rows'])} players, {len(out['renders'])} card pictures, {len(text) // 1024} KB")


if __name__ == "__main__":
    main()
