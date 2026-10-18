#!/usr/bin/env python3
"""Market pulse, trending cards and cheapest cards by rating, worked out from the live FC 27 price feed.

FUTBIN refuses GitHub's servers, so its market index and "hottest players" list can't be read here.
This script builds Ezzcoins' own versions from data/live-prices.json (every tradeable card's console
price) instead:

- data/market.json      Top 100 index, ICON index and the 84/85/86 floors, each with its 24-hour change,
                        plus a momentum score (share of cards worth 2,000+ coins rising in the last hour).
- data/trending.json    The cards worth 5,000+ coins whose price rose most over about a day.
- data/cheapest.json    The three cheapest tradeable cards at each rating from 81 to 91.
- data/market-index.json  Index baskets and hourly index points (kept in git; small).
- data/ut-positions.json  Ultimate Team positions of base cards, for scripts/build_players.py, so the
                        6 MB card metadata cache doesn't have to live in the repository.

Per-card price snapshots for momentum and trending live in data/.cache/ (restored by the workflow from
the Actions cache, never committed). Files are only rewritten when their content changes.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / ".cache"
SNAPS = CACHE / "price-snaps.json"

SNAP_MIN = 1000          # cards worth this much or more are kept in the hourly snapshots
MOMENTUM_MIN = 2000      # momentum counts cards worth at least this
TREND_MIN = 5000         # trending only lists cards worth at least this
BASKET_DAYS = 7          # baskets are re-formed weekly and chain-linked so the index stays continuous
POINT_DAYS = 8           # hourly index points kept


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(t):
    return t.isoformat().replace("+00:00", "Z")


def parse(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def read(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def write_if_changed(path, value, ignore=("updatedAt",)):
    """Write compact JSON only when something other than the ignored keys changed."""
    old = read(path, None)
    strip = lambda d: {k: v for k, v in d.items() if k not in ignore} if isinstance(d, dict) else d
    if old is not None and strip(old) == strip(value):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(path)
    return True


def card_info():
    """id -> {name, ovr, pos, version, url, base} from the base roster and the card catalogue."""
    info = {}
    roster = read(DATA / "players.json", {"cols": [], "rows": []})
    ci = {c: i for i, c in enumerate(roster.get("cols", []))}
    if {"id", "name", "ovr", "pos"} <= ci.keys():
        for r in roster["rows"]:
            info[int(r[ci["id"]])] = {"name": r[ci["name"]], "ovr": r[ci["ovr"]], "pos": r[ci["pos"]],
                                      "version": "Rare" if (r[ci["ovr"]] or 0) >= 75 else "", "base": True}
    market = read(DATA / "market-cards.json", {"cols": [], "rows": []})
    mi = {c: i for i, c in enumerate(market.get("cols", []))}
    if {"id", "name", "ovr", "pos", "version"} <= mi.keys():
        for r in market["rows"]:
            item = int(r[mi["id"]])
            base = info.get(item, {}).get("base", False)
            info[item] = {"name": r[mi["name"]], "ovr": r[mi["ovr"]], "pos": r[mi["pos"]], "version": r[mi["version"]] or "",
                          "url": r[mi["url"]] if "url" in mi else "", "base": base}
    return info


def basket_index(state, key, prices, pick, t):
    """Chain-linked price index over a fixed basket. pick(prices) -> ids for a new basket."""
    b = state.get(key)
    formed = parse(b["formedAt"]) if b else None
    have = [i for i in (b or {}).get("ids", {}) if prices.get(int(i))]
    if not b or not formed or t - formed > timedelta(days=BASKET_DAYS) or len(have) < 0.8 * len(b["ids"]):
        level = basket_value(b, prices) if b and have else 100.0
        ids = pick(prices)
        if not ids:
            return None
        state[key] = b = {"formedAt": iso(t), "level": round(level, 4), "ids": {str(i): prices[i] for i in ids}}
    return basket_value(b, prices)


def basket_value(b, prices):
    cur = base = 0
    for i, p0 in b["ids"].items():
        p = prices.get(int(i))
        if p and p0:
            cur += p
            base += p0
    return b["level"] * cur / base if base else None


def floor(prices, info, ovr):
    vals = sorted(p for i, p in prices.items() if info.get(i, {}).get("ovr") == ovr)[:3]
    return vals[len(vals) // 2] if vals else None  # the middle of the three cheapest, so one odd listing doesn't set it


def change(points, col, value, t, hours=24, min_hours=20):
    """Percent change against the point closest to `hours` ago (needs one at least `min_hours` old)."""
    if value is None:
        return None
    best = None
    for p in points:
        at = parse(p[0])
        if at and timedelta(hours=min_hours) <= t - at <= timedelta(hours=hours + 6) and p[col]:
            if best is None or abs((t - at) - timedelta(hours=hours)) < abs((t - parse(best[0])) - timedelta(hours=hours)):
                best = p
    return round((value / best[col] - 1) * 100, 2) if best else None


def snapshot_near(snaps, t, hours, min_hours):
    """The stored price snapshot closest to `hours` ago, at least `min_hours` old."""
    best = None
    for s in snaps:
        at = parse(s["t"])
        if at and t - at >= timedelta(hours=min_hours):
            if best is None or abs((t - at) - timedelta(hours=hours)) < abs((t - parse(best["t"])) - timedelta(hours=hours)):
                best = s
    return best


def momentum_label(m):
    return ("Prices are rising fast" if m >= 65 else "Prices are rising" if m >= 55 else "Prices are steady" if m > 45
            else "Prices are falling" if m > 35 else "Prices are falling fast")


def main():
    live = read(DATA / "live-prices.json", None)
    if not live or live.get("cols", [])[:2] != ["id", "console"]:
        print("market_extras: no live price feed, nothing to do")
        return
    t = now_utc()
    at = live.get("publishedAt", {}).get("console") or live.get("retrievedAt") or iso(t)
    prices = {int(r[0]): int(r[1]) for r in live["rows"] if r[1] and (len(r) < 4 or r[3] == 0)}
    info = card_info()
    is_icon = lambda i: "icon" in str(info.get(i, {}).get("version", "")).lower()

    # Index baskets and hourly points.
    state = read(DATA / "market-index.json", {})
    def top100(p):
        return sorted((i for i in p if i in info), key=lambda i: -p[i])[:100]
    def icons(p):
        return [i for i in p if info.get(i, {}).get("version") == "Base Icon"]
    idx100 = basket_index(state, "top100", prices, top100, t)
    icon_idx = basket_index(state, "icons", prices, icons, t)
    floors = {o: floor(prices, info, o) for o in (84, 85, 86)}
    points = [p for p in state.get("points", []) if parse(p[0]) and t - parse(p[0]) <= timedelta(days=POINT_DAYS)]
    last = parse(points[-1][0]) if points else None
    row = [iso(t), idx100, floors[84], floors[85], floors[86], icon_idx]
    if not last or t - last >= timedelta(minutes=55):
        points.append([v if not isinstance(v, float) else round(v, 2) for v in row])
    state["points"] = points

    # Momentum and trending from hourly per-card snapshots (Actions cache, not git).
    snaps = read(SNAPS, [])
    snaps = [s for s in snaps if parse(s.get("t")) and t - parse(s["t"]) <= timedelta(hours=30)]
    if not snaps or t - parse(snaps[-1]["t"]) >= timedelta(minutes=55):
        snaps.append({"t": iso(t), "p": {str(i): p for i, p in prices.items() if p >= SNAP_MIN}})
        write_if_changed(SNAPS, snaps, ignore=())
    hour_ago = snapshot_near(snaps, t, 1, 0.8)
    momentum = None
    if hour_ago:
        up = down = 0
        for i, p0 in hour_ago["p"].items():
            p = prices.get(int(i))
            if p and p0 >= MOMENTUM_MIN:
                if p > p0 * 1.01:
                    up += 1
                elif p < p0 * 0.99:
                    down += 1
        momentum = round(100 * up / (up + down), 1) if up + down >= 20 else 50.0

    market = {"updatedAt": iso(t), "at": at, "source": "Ezzcoins", "srcLabel": "Ezzcoins index",
              "note": "Ezzcoins' own index from live console prices of every tradeable card (FUTBIN's index can't be read automatically).",
              # FUTBIN's Index 84/85/86 can't be rebuilt; the floors are coin prices, under their own keys.
              "labels": {"idx100": "Top 100 index", "icons": "ICON index", "floor84": "Typical 84 low", "floor85": "Typical 85 low", "floor86": "Typical 86 low"},
              "idx100": round(idx100, 2) if idx100 else None, "idx100Chg": change(points, 1, idx100, t),
              "floor84": round(floors[84]) if floors[84] else None, "floor84Chg": change(points, 2, floors[84], t),
              "floor85": round(floors[85]) if floors[85] else None, "floor85Chg": change(points, 3, floors[85], t),
              "floor86": round(floors[86]) if floors[86] else None, "floor86Chg": change(points, 4, floors[86], t),
              "icons": round(icon_idx, 2) if icon_idx else None, "iconsChg": change(points, 5, icon_idx, t),
              "momentum": momentum, "momentumLabel": momentum_label(momentum) if momentum is not None else None}
    if idx100 is not None:
        write_if_changed(DATA / "market.json", market, ignore=("updatedAt", "at"))
    write_if_changed(DATA / "market-index.json", {**state, "updatedAt": iso(t)}, ignore=("updatedAt",))

    # Trending: biggest rises over about a day (or the longest window the snapshots cover, at least an hour).
    ref = snapshot_near(snaps, t, 24, 6) or snapshot_near(snaps, t, 24, 1)
    if ref:
        hours = round((t - parse(ref["t"])).total_seconds() / 3600)
        rises = []
        for i, p in prices.items():
            p0 = ref["p"].get(str(i))
            c = info.get(i)
            if c and p >= TREND_MIN and p0 and p > p0 * 1.03:
                rises.append((p / p0 - 1, i))
        rises.sort(reverse=True)
        cards = []
        for n, (r, i) in enumerate(rises[:24], 1):
            c = info[i]
            cards.append({"rank": n, "name": c["name"], "ovr": c["ovr"], "pos": c["pos"], "version": c["version"] or None,
                          "price": prices[i], "chg": round(r * 100, 1), "eaId": i, "url": c.get("url") or "", "fid": None, "src": "FUT.GG"})
        trending = {"updatedAt": iso(t), "at": at, "source": "Ezzcoins", "window": hours,
                    "label": f"Biggest price rises · {hours} h", "cards": cards}
        if cards:
            write_if_changed(DATA / "trending.json", trending, ignore=("updatedAt", "at"))

    # Cheapest tradeable cards at each rating (SBC fodder).
    ratings = {}
    for o in range(81, 92):
        cheap = sorted((p, i) for i, p in prices.items() if info.get(i, {}).get("ovr") == o)[:3]
        if cheap:
            ratings[str(o)] = [{"name": info[i]["name"], "ovr": o, "pos": info[i]["pos"], "version": info[i]["version"] or None,
                                "price": p, "eaId": i, "fid": None, "url": info[i].get("url") or ""} for p, i in cheap]
    if len(ratings) >= 4:
        write_if_changed(DATA / "cheapest.json", {"updatedAt": iso(t), "source": "FUT.GG", "at": at, "ratings": ratings},
                         ignore=("updatedAt", "at"))

    # Ultimate Team positions of base cards, for the daily rebuild of data/players.json.
    meta = read(DATA / "card-metadata.json", {})
    if meta:
        ut = {k: [r.get("ovr"), r.get("pos"), r["alt"]] for k, r in sorted(meta.items(), key=lambda kv: int(kv[0]))
              if not r.get("excluded") and not r.get("isSpecial") and str(r.get("baseId")) == k and isinstance(r.get("alt"), str)}
        old = read(DATA / "ut-positions.json", {}).get("positions", {})
        merged = {**old, **ut}
        if merged != old:
            write_if_changed(DATA / "ut-positions.json", {"updatedAt": iso(t), "positions": merged})

    print(f"market_extras: index {market['idx100']} ({market['idx100Chg']}%), momentum {momentum}, "
          f"trending {len(read(DATA / 'trending.json', {}).get('cards', []))}, cheapest {len(ratings)} ratings, {len(snaps)} snapshots")


if __name__ == "__main__":
    main()
