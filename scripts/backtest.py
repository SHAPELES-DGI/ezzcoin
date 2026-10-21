#!/usr/bin/env python3
"""Paper trading: every call the desk's price-move strategies would have made over the recorded prices, graded
the way real calls are. scripts/desk.py switches a strategy off while its paper calls lose after tax.

The data is the price history the site records (data/price-history/, restored from the "history" branch in the
market workflow): console prices of about 3,000 cards, hourly for the last 7 days and daily for 30. So every
run re-tests each strategy on the market as it has been lately, and one that stops working (or starts working)
is noticed within days instead of after a string of public misses.

Each strategy is replayed with the same rules as the desk's live calls (scripts/desk.py candidates):
- rebound (buy the dip), slide (sell the slide) and fade (sell the spike): one paper call at most every 6 hours,
  the biggest qualifying move each time, never the same card twice in 7 days, graded 48 hours later;
- weekend (buy before the weekend): the desk's pick on Tuesday, Wednesday and Thursday evening, graded on
  Friday evening.
Buys pay the 5% tax on the resale; a sell call is a hit when the price is lower at check time.

Usage: python3 scripts/backtest.py   (prints the paper record; standard library only)
"""
import bisect
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOUR = 3600
MOVE_STRATEGIES = ("rebound", "slide", "fade")
SPACING = 6 * HOUR            # one paper call per strategy at most every 6 hours
SAME_CARD = 7 * 86400         # the desk never calls the same card twice in 7 days
HOLD = 48 * HOUR
CONFIRM_GAP = 0.15            # the current price must agree with the reading an hour earlier within 15%
MIN_PRICE = 10000


def load(folder):
    """{card id: [(time, console price), ...] oldest first} from the price-history shards."""
    series = {}
    for path in sorted(Path(folder).glob("[0-9][0-9].json")):
        try:
            items = json.loads(path.read_text(encoding="utf-8")).get("items", {})
        except (OSError, ValueError):
            continue
        for k, v in items.items():
            pts = sorted((int(a), int(p)) for a, p in v.get("console", []) if p)
            if pts:
                series[int(k)] = pts
    return series


class Prices:
    def __init__(self, series):
        self.series = series
        self.times = {i: [a for a, _ in pts] for i, pts in series.items()}

    def at(self, i, ts, tol):
        """The recorded price nearest to ts, if one is within tol seconds."""
        times = self.times.get(i)
        if not times:
            return None
        k = bisect.bisect_left(times, ts)
        best = None
        for j in (k - 1, k):
            if 0 <= j < len(times) and abs(times[j] - ts) <= tol and (best is None or abs(times[j] - ts) < abs(times[best] - ts)):
                best = j
        return self.series[i][best][1] if best is not None else None

    def base(self, i, ts):
        """The price about a day before ts: the middle of the readings 22 to 26 hours earlier, so one wrong
        reading can't make a move."""
        times = self.times.get(i) or []
        lo, hi = bisect.bisect_left(times, ts - 26 * HOUR), bisect.bisect_right(times, ts - 22 * HOUR)
        xs = sorted(p for _, p in self.series[i][lo:hi])
        return xs[len(xs) // 2] if xs else None


def buy_result(entry, exit_):
    res = (math.floor(exit_ * 0.95) - entry) / entry * 100
    return round(res, 1), res > 0


def sell_result(entry, exit_):
    return round((entry - exit_) / entry * 100, 1), exit_ < entry


def move_signals(px, info, hour_ts, meta_ok):
    """{strategy: [(size, card, price)]} of moves that qualify at this hour, as the desk's live rules see them."""
    out = {k: [] for k in MOVE_STRATEGIES}
    for i in px.series:
        p = px.at(i, hour_ts, 20 * 60)
        if not p or p < MIN_PRICE:
            continue
        p1 = px.at(i, hour_ts - HOUR, 25 * 60)
        if not p1 or abs(p / p1 - 1) > CONFIRM_GAP:
            continue
        p0 = px.base(i, hour_ts)
        if not p0:
            continue
        pct, earlier = (p / p0 - 1) * 100, (p1 / p0 - 1) * 100
        if pct <= -10 and earlier <= pct / 2 and meta_ok(i):
            out["rebound"].append((-pct, i, p))
            out["slide"].append((-pct, i, p))
        elif pct >= 15 and earlier >= pct / 2 and p0 >= 5000 and (info.get(i, {}).get("ovr") or 0) >= 80:
            out["fade"].append((pct, i, p))
    return out


def paper_calls(series, info, t, week=None):
    """Paper calls per strategy: [{"at", "item", "entry", "exit", "result", "hit"}], oldest first.
    week: (phase, next_weekday, UK time zone) from scripts/desk.py, for the weekend strategy."""
    px = Prices(series)
    meta_ok = lambda i: (info.get(i, {}).get("meta") or 0) >= max(84, (info.get(i, {}).get("ovr") or 0))
    now = int(t.timestamp())
    first = min((pts[0][0] for pts in series.values()), default=now)
    calls = {k: [] for k in (*MOVE_STRATEGIES, "weekend")}
    last_call = {k: -10 ** 12 for k in MOVE_STRATEGIES}
    used = {k: {} for k in MOVE_STRATEGIES}
    # Hourly readings exist for the last 7 days only; earlier days hold one reading each.
    start = max(first, now - 7 * 86400) + 26 * HOUR
    for h in range(start - start % HOUR, now - HOLD + 1, HOUR):
        due = [k for k in MOVE_STRATEGIES if h - last_call[k] >= SPACING]
        if not due:
            continue
        signals = move_signals(px, info, h, meta_ok)
        for k in due:
            for size, i, p in sorted(signals[k], reverse=True):
                if h - used[k].get(i, -10 ** 12) < SAME_CARD:
                    continue
                x = px.at(i, h + HOLD, 2 * HOUR)
                if not x:
                    continue
                res, hit = (buy_result if k == "rebound" else sell_result)(p, x)
                calls[k].append({"at": h, "item": i, "entry": p, "exit": x, "result": res, "hit": hit})
                used[k][i], last_call[k] = h, h
                break
    if week:
        calls["weekend"] = weekend_calls(px, info, t, first, meta_ok, *week)
    return calls


def weekend_calls(px, info, t, first, meta_ok, phase, next_weekday, uk_zone):
    """The desk's weekend pick on each Tuesday, Wednesday and Thursday evening (20:00 UK) in the record, sold on
    Friday at 20:00 UK. Older days hold one reading each, so a reading within 5 hours counts."""
    out = []
    now = int(t.timestamp())
    day = datetime.fromtimestamp(first, timezone.utc).date()
    while True:
        uk = datetime(day.year, day.month, day.day, 20, tzinfo=uk_zone).astimezone(timezone.utc)
        day += timedelta(days=1)
        ts = int(uk.timestamp())
        if ts > now:
            break
        check = next_weekday(uk, 4, 20)
        if not (timedelta(hours=24) <= check - uk <= timedelta(hours=72)) or phase(uk) not in ("midweek", "prefriday", "rewards"):
            continue
        cts = int(check.timestamp())
        if cts > now:
            continue
        tol = HOUR if now - ts <= 7 * 86400 else 5 * HOUR
        pool = []
        for i in px.series:
            c = info.get(i, {})
            if not (c.get("base") and meta_ok(i)):
                continue
            p = px.at(i, ts, tol)
            if not p or not 8000 <= p <= 150000:
                continue
            p1 = px.at(i, ts - HOUR, 25 * 60)
            if p1 and abs(p / p1 - 1) > CONFIRM_GAP:
                continue
            pool.append((-(c["meta"] - 6 * math.log10(p)), i, p))
        for _, i, p in sorted(pool):
            x = px.at(i, cts, HOUR if now - cts <= 7 * 86400 else 5 * HOUR)
            if x:
                res, hit = buy_result(p, x)
                out.append({"at": ts, "item": i, "entry": p, "exit": x, "result": res, "hit": hit})
                break
    return out


def summary(calls):
    """{strategy: {"n", "hit", "avg", "from", "to"}} for strategies with paper calls."""
    out = {}
    for k, cs in calls.items():
        if cs:
            out[k] = {"n": len(cs), "hit": sum(c["hit"] for c in cs), "avg": round(sum(c["result"] for c in cs) / len(cs), 1),
                      "from": iso(cs[0]["at"]), "to": iso(cs[-1]["at"])}
    return out


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    import desk
    t = desk.now_utc()
    mk = desk.Market(t)
    calls = paper_calls(load(desk.DATA / "price-history"), mk.info, t, (desk.phase, desk.next_weekday, desk.UK))
    for k, s in summary(calls).items():
        print(f"{k:8} {s['n']:3} paper calls, {s['hit']} hit, {s['avg']:+.1f}% average after tax ({s['from'][:10]} to {s['to'][:10]})")


if __name__ == "__main__":
    main()
