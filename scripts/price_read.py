#!/usr/bin/env python3
"""Ezzcoins' own price read for every tracked card, worked out once a day from the prices Ezzcoins recorded.

Reads the 64 price-history files (data/price-history/NN.json, written by scripts/record_price_history.py: hourly
prices for seven days, daily prices for thirty) and writes data/price-read.json, which scripts/build_pages.py
writes into each player page as plain sentences, so the pages carry Ezzcoins' own numbers, not just a price.

"items" maps each EA item id to [console, PC]; each is null or a row in the order of "cols":
  n, days      hourly prices used from the last 7 days, and on how many UK days
  lo, hi, avg  lowest, highest and average price of the last 7 days
  p10, p90     the low and high end of the usual 7-day range (10% of hours were cheaper / dearer)
  flip         coins left per card after EA's 5% tax, buying at p10 and selling at p90 (can be negative)
  last         the newest recorded price
  trend        % change from the first day of the 7 days to the last day (medians, so one odd reading can't set it)
  lo30, hi30   lowest and highest price of the last 30 days
  swing        typical % gap between a day's highest and lowest price (median over full UK days), or null; swingDays
  cheap, dear  [UK hour, days, of days] or null: the time of day the card was usually cheapest / dearest, only when it held on
               most days. Each price is compared with the card's median over the 24 hours around it, so a card that
               rose all week doesn't look "cheapest at midnight".

A single price that is far off the readings on both sides of it (a glitched or mispriced listing) is left out, and
the newest price is left out if it is far off the readings before it (it can't be confirmed yet).

Runs in the market workflow after the price history is restored. It works the read out once per UK day (the file's
"day"); later runs that day do nothing, so the player pages change once a day, not on every price refresh.

Usage: python3 scripts/price_read.py [--force]   (standard library only)
"""
import json
import math
import statistics
import sys
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UK = ZoneInfo("Europe/London")
WEEK, MONTH, HOUR = 7 * 86400, 30 * 86400, 3600
GLITCH = 0.30            # a price this far (30%) off the readings on both sides of it is left out
MIN_POINTS, MIN_DAYS = 48, 3   # hourly prices (and UK days) needed before a card gets a read
FULL_DAY = 18            # hourly prices a UK day needs to count for the daily swing and time-of-day pattern
PATTERN_DAYS = 5         # days of data a time-of-day pattern needs ...
PATTERN_SHARE = 0.7      # ... it held on at least 70% of them ...
PATTERN_SPREAD = 0.04    # ... and the cheapest and dearest times differ by at least 4% on average


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def tax_flip(buy, sell):
    """Coins left after EA keeps 5% of the sale (rounded down), like scripts/desk.py grades calls."""
    return math.floor(sell * 0.95) - buy


def ladder(n):
    """Round to EA's transfer market price steps, so averages read like real prices."""
    step = 10 if n < 1000 else 100 if n < 10000 else 250 if n < 50000 else 500 if n < 100000 else 1000
    return int(round(n / step) * step)


def clean(points):
    """Drop lone glitches: prices far off both neighbouring sides; the newest only if far off the ones before it."""
    keep = []
    for i, (t, p) in enumerate(points):
        before = [q for _, q in points[max(0, i - 3):i]]
        after = [q for _, q in points[i + 1:i + 4]]
        sides = [statistics.median(s) for s in (before, after) if len(s) >= 2]
        if sides and all(abs(p - m) / m > GLITCH for m in sides):
            continue
        keep.append((t, p))
    return keep


def rank(values, share):
    """The observed price below which `share` of the readings fall (nearest rank), so it is a real market price."""
    s = sorted(values)
    return s[min(len(s) - 1, max(0, math.ceil(share * len(s)) - 1))]


def time_pattern(week):
    """(cheap, dear): [UK hour, days it held, days with data] or None. Uses 3-hour windows centred on each hour."""
    times = [t for t, _ in week]
    by_hour, by_day = {}, {}
    for t, p in week:
        lo, hi = bisect_left(times, t - 12 * HOUR), bisect_right(times, t + 12 * HOUR)
        if hi - lo < 16:                                   # needs most of the surrounding day
            continue
        d = p / statistics.median(q for _, q in week[lo:hi]) - 1
        local = datetime.fromtimestamp(t, UK)
        by_hour.setdefault(local.hour, []).append(d)
        by_day.setdefault(local.date(), {}).setdefault(local.hour, []).append(d)
    days = [hours for hours in by_day.values() if len(hours) >= FULL_DAY]
    if len(days) < PATTERN_DAYS:
        return None, None
    window = lambda h: [(h + k) % 24 for k in (-1, 0, 1)]
    avg = {}
    for h in range(24):
        vals = [d for k in window(h) for d in by_hour.get(k, [])]
        if len(vals) >= 6:
            avg[h] = statistics.mean(vals)
    if len(avg) < 20:
        return None, None
    lo_h, hi_h = min(avg, key=avg.get), max(avg, key=avg.get)
    if avg[hi_h] - avg[lo_h] < PATTERN_SPREAD:
        return None, None

    def held(h, below):
        seen = good = 0
        for hours in days:
            vals = [d for k in window(h) for d in hours.get(k, [])]
            if vals:
                seen += 1
                m = statistics.mean(vals)
                good += (m < 0) if below else (m > 0)
        return [h, good, seen] if seen >= PATTERN_DAYS and good >= PATTERN_SHARE * seen else None

    return held(lo_h, True), held(hi_h, False)


def read_platform(points, now):
    """The read for one card on one platform, or None when there aren't enough recorded prices yet."""
    points = sorted((int(t), int(p)) for t, p in points if p and p > 0 and now - MONTH <= t <= now + 300)
    month = clean(points)
    week = [(t, p) for t, p in month if t >= now - WEEK]
    day_of = lambda t: datetime.fromtimestamp(t, UK).date()
    week_days = {day_of(t) for t, _ in week}
    if len(week) < MIN_POINTS or len(week_days) < MIN_DAYS:
        return None
    prices = [p for _, p in week]
    first = [p for t, p in week if t < week[0][0] + 86400]
    final = [p for t, p in week if t > week[-1][0] - 86400]
    per_day = {}
    for t, p in week:
        per_day.setdefault(day_of(t), []).append(p)
    swings = [(max(v) - min(v)) / statistics.median(v) for v in per_day.values() if len(v) >= FULL_DAY]
    p10, p90 = rank(prices, 0.1), rank(prices, 0.9)
    cheap, dear = time_pattern(week)
    out = {"n": len(week), "days": len(week_days), "lo": min(prices), "hi": max(prices),
           "avg": ladder(statistics.mean(prices)), "p10": p10, "p90": p90, "flip": tax_flip(p10, p90),
           "last": week[-1][1], "trend": round((statistics.median(final) / statistics.median(first) - 1) * 100, 1),
           "lo30": min(p for _, p in month), "hi30": max(p for _, p in month),
           "swing": round(statistics.median(swings) * 100, 1) if swings else None, "swingDays": len(swings),
           "cheap": cheap, "dear": dear}
    return out


COLS = ["n", "days", "lo", "hi", "avg", "p10", "p90", "flip", "last", "trend", "lo30", "hi30", "swing", "swingDays",
        "cheap", "dear"]


def unpack(row):
    """One platform's read from data/price-read.json as a dict (the file stores rows to stay small)."""
    return dict(zip(COLS, row)) if row else None


def build(folder, now):
    items = {}
    for path in sorted(Path(folder).glob("[0-9][0-9].json")):
        for item, platforms in json.loads(path.read_text()).get("items", {}).items():
            reads = [read_platform(platforms.get(platform) or [], now) for platform in ("console", "pc")]
            if any(reads):
                items[item] = [[r[k] for k in COLS] if r else None for r in reads]
    return {"game": "FC 27", "asOf": iso(now), "day": datetime.fromtimestamp(now, UK).date().isoformat(),
            "platforms": ["console", "pc"], "cols": COLS, "items": items}


def main():
    now = datetime.now(timezone.utc).timestamp()
    out = DATA / "price-read.json"
    today = datetime.fromtimestamp(now, UK).date().isoformat()
    try:
        done = json.loads(out.read_text()).get("day") == today
    except (OSError, ValueError):
        done = False
    if done and "--force" not in sys.argv:
        print("Price read: already worked out today")
        return
    shards = list((DATA / "price-history").glob("[0-9][0-9].json"))
    if len(shards) != 64:
        print(f"Price read: price history incomplete ({len(shards)} of 64 files), kept the old read")
        return
    data = build(DATA / "price-history", now)
    if len(data["items"]) < 500:                       # something went wrong upstream: keep yesterday's read
        print(f"Price read: only {len(data['items'])} cards, kept the old read")
        return
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    tmp.replace(out)
    patterns = sum(1 for c, _ in data["items"].values() if c and c[COLS.index("cheap")])
    print(f"Price read: {len(data['items'])} cards ({patterns} with a cheapest time of day on console)")


if __name__ == "__main__":
    main()
