#!/usr/bin/env python3
"""Ezzcoins' automatic trading desk: the market read, trade calls and their grading, with no AI involved.

Runs in the market workflow after the price scripts and writes:
- data/snapshot.json  verdict, moves, fodder board, SBCs, movers, cheap meta cards, calendar, news
- data/history.json   a point (84/85/86 floors and Top 100 index) at most every 10 minutes
- data/ledger.json    tracked trade calls, graded automatically, and the lessons learned from them
- data/prices.json    the 25 most-watched cards (from the site's public watchlists)
- data/topprices.json every base card rated 84+

Everything comes from Ezzcoins' own data: the live console price feed (data/live-prices.json), the
index, trending and cheapest-card files from scripts/market_extras.py, the SBC list from
scripts/update_sbcs.py, new cards from the card catalogue and EA's ratings (data/players.json).

How the desk learns: every call follows one of a few written strategies. Each graded call adds a
lesson and is added to lifetime totals (data/ledger.json "record" and "strategies"), which survive
the trimming of old calls. A strategy is judged on its last 12 graded calls, so one that stops
working later in the season is caught: with 3+ of them and under 50% hits or a negative average
result after tax, it is paused (no new calls) for 7 days and then gets one retest at low
confidence. Strategies are tried in order of their expected result after tax (the recent average,
pulled toward 0% while there are few calls), and one with 70%+ hits and a positive average is
called at high confidence. "strategyBoard" in the ledger is the public scoreboard.

Paper trading (scripts/backtest.py): every run replays the price-move and weekend strategies on the prices
recorded over the last days and grades those paper calls like real ones. A strategy whose paper calls hit half
the time or less, or lose after tax, is switched off ("off" on the scoreboard) until the market changes, so it can't
pile up public misses first. A strategy with no real calls yet ("slide") must pass its paper test before it is
used.

Reliability: a call is only made when two price readings about an hour apart agree, so a single
glitched or mispriced listing can't trigger one, and a day-long move is measured from the middle of the
readings around a day ago, so one wrong old reading can't create a move either.

Daily drop: every evening the desk records how the 84/85/86 floors and the Top 100 index moved from
just before EA's 6 PM UK content drop to about 8 PM (data/ledger.json "dropLog"), and the snapshot's
"dailyDrop" turns the recent record into timing advice. Fridays (promo nights) are measured apart.

Usage: python3 scripts/desk.py   (standard library only)
"""
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import meta  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UK = ZoneInfo("Europe/London")
DESK_TZ = ZoneInfo("Europe/Zurich")  # calendar day for the daily call count
SCORES = {81: 280, 82: 340, 83: 410, 84: 830, 85: 2100, 86: 4100, 87: 5500, 88: 8300, 89: 11000, 90: 14000, 91: 19000}
FEED_FRESH = timedelta(minutes=60)   # older feeds don't set or grade prices
CALLS_PER_DAY = 2
CALL_GAP = timedelta(hours=3)        # time between the day's two calls
PAUSE = timedelta(days=7)
RECENT = 12                          # graded calls per strategy that decide pausing and confidence
PRIOR = 3                            # expected result is pulled toward 0% as if there were 3 break-even calls
CONFIRM_GAP = 15                     # % a price may differ from the reading an hour earlier and still agree
TAX_BREAK_EVEN = 100 / 95 * 100 - 100  # a resale must rise 5.26% just to cover the 5% tax
KEEP_CALLS, KEEP_LESSONS, KEEP_POINTS, KEEP_DROPS = 60, 40, 500, 42
FEED = {"label_src": "Ezzcoins price feed", "url": "https://ezzcoins.com/prices.html"}
SITE_SOURCES = [{"title": "Ezzcoins price feed (FUT.GG data)", "url": "https://ezzcoins.com/prices.html"},
                {"title": "EA SPORTS FC 27 ratings", "url": "https://www.ea.com/games/ea-sports-fc/ratings"}]
WATCHLISTS = "https://firestore.googleapis.com/v1/projects/ezzcoin-d5316/databases/(default)/documents/watchlists?pageSize=300"

STRATEGIES = {
    "weekend": {"name": "Buy before the weekend",
                "why": "meta cards are bought for Champions weekend, so they often rise from midweek to Friday evening"},
    "rebound": {"name": "Buy the dip",
                "why": "a playable card that fell sharply in a day often recovers part of the fall within two days"},
    "fade": {"name": "Sell the spike",
             "why": "a card that jumped in a day often gives part of the jump back within two days"},
    "slide": {"name": "Sell the slide",
              "why": "a playable card that fell sharply in a day often keeps falling for another two days"},
    "rewards": {"name": "Rivals rewards dip",
                "why": "Rivals rewards flood the market with fodder on Thursday morning, and SBC demand lifts it again by the weekend"},
    "drop": {"name": "Buy before the 6 PM drop",
             "why": "this fodder rating has risen after most recent 6 PM content drops by more than the 5% tax"},
}
ORDER = ["rewards", "drop", "weekend", "rebound", "slide", "fade"]
BACKTESTED = {"rebound": 10, "slide": 10, "fade": 10, "weekend": 3}   # paper calls needed before the test counts
NEEDS_TEST = {"slide"}                # never used without a passing paper test


# ---------------------------------------------------------------- helpers

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse(s):
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def tok(t):
    """A time token the site shows in the viewer's own time zone."""
    t = (t + timedelta(seconds=30)).replace(second=0, microsecond=0)
    return "{{t:" + t.astimezone(UK).isoformat() + "}}"


def coins(n):
    return f"{int(round(n)):,}"


def short(n):
    return f"{n / 1e6:.2f}".rstrip("0").rstrip(".") + "M" if n >= 1e6 else f"{n / 1e3:.1f}".rstrip("0").rstrip(".") + "K" if n >= 1e3 else str(int(n))


def read(name, fallback):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def write(name, value):
    path = DATA / name
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(path)


def strip_name(value):
    """The public site must never carry the owner's name."""
    text = json.dumps(value, ensure_ascii=False)
    if "Danyel" not in text:
        return value
    return json.loads(text.replace("Danyel's", "a").replace("Danyel", "a tip"))


# ---------------------------------------------------------------- market data

class Market:
    def __init__(self, t):
        self.t = t
        live = read("live-prices.json", {})
        cols = {c: i for i, c in enumerate(live.get("cols", []))}
        self.published = parse((live.get("publishedAt") or {}).get("console")) or parse(live.get("retrievedAt"))
        self.fresh = bool(self.published and t - self.published <= FEED_FRESH and len(live.get("rows", [])) >= 1000)
        self.prices, self.state = {}, {}
        if {"id", "console", "consoleState"} <= cols.keys():
            for r in live["rows"]:
                i = int(r[cols["id"]])
                self.state[i] = r[cols["consoleState"]]
                if r[cols["consoleState"]] == 0 and (r[cols["console"]] or 0) > 0:
                    self.prices[i] = int(r[cols["console"]])
        self.info = self._info()
        self.market = read("market.json", {})
        self.cheapest = read("cheapest.json", {}).get("ratings", {})
        self.trending = read("trending.json", {}).get("cards", [])
        snaps = read(".cache/price-snaps.json", [])
        self.snaps = snaps
        self.day_ago = self._snap_near(snaps, 24, 6)
        self.hour_ago = self._snap_near(snaps, 1, 0.5)
        self.hist = [p for p in read("history.json", {}).get("points", []) if parse(p.get("t"))]

    def _info(self):
        info = {}
        roster = read("players.json", {"cols": [], "rows": []})
        ci = {c: i for i, c in enumerate(roster.get("cols", []))}
        for r in roster.get("rows", []):
            g = lambda c: r[ci[c]] if c in ci else None
            s = [g(f"s{k}") for k in range(1, 7)]
            m = meta(g("pos") or "", g("alt") or "", s, g("sm"), g("wf"), g("psp") or "")
            info[int(g("id"))] = {"name": g("name"), "ovr": g("ovr"), "pos": g("pos"), "version": "Rare" if (g("ovr") or 0) >= 75 else "",
                                  "base": True, "meta": next(iter(m.values())) if m else None,
                                  "metaPos": next(iter(m)) if m else g("pos")}
        cards = read("market-cards.json", {"cols": [], "rows": []})
        mi = {c: i for i, c in enumerate(cards.get("cols", []))}
        for r in cards.get("rows", []):
            i = int(r[mi["id"]])
            old = info.get(i, {})
            info[i] = {**old, "name": r[mi["name"]], "ovr": r[mi["ovr"]], "pos": r[mi["pos"]], "version": r[mi["version"]] or old.get("version", ""),
                       "base": old.get("base", False), "meta": old.get("meta"), "metaPos": old.get("metaPos", r[mi["pos"]])}
        for c in read("newcards.json", {}).get("cards", []):
            item = c.get("eaId")
            if not item or not isinstance(c.get("stats"), list) or len(c["stats"]) != 6:
                continue
            m = meta(c.get("pos") or "", c.get("alt") or "", c["stats"], c.get("sm"), c.get("wf"), c.get("ps") or "")
            if m and int(item) in info:
                info[int(item)].update({"meta": next(iter(m.values())), "metaPos": next(iter(m))})
        return info

    def _snap_near(self, snaps, hours, min_hours):
        best = None
        for s in snaps:
            at = parse(s.get("t"))
            if at and self.t - at >= timedelta(hours=min_hours):
                if best is None or abs((self.t - at) - timedelta(hours=hours)) < abs((self.t - parse(best["t"])) - timedelta(hours=hours)):
                    best = s
        return best

    def label(self, i):
        c = self.info.get(i, {})
        ver = c.get("version") or ""
        return f'{c.get("name", "Card " + str(i))} {c.get("ovr", "")}' + (f" {ver}" if ver and ver != "Rare" else "")

    def floor(self, ovr):
        cards = self.cheapest.get(str(ovr)) or []
        return cards[0]["price"] if cards else None

    def base_24h(self, i):
        """The card's price about a day ago: the middle of the readings within 2.5 hours of the day-old snapshot,
        so one wrong reading then can't make a move now."""
        day = self.day_ago or {}
        p0 = day.get("p", {}).get(str(i))
        if not p0:
            return None
        if not hasattr(self, "_around"):
            at = parse(day.get("t"))
            self._around = [x for x in getattr(self, "snaps", []) if at and parse(x.get("t")) and abs(parse(x["t"]) - at) <= timedelta(hours=2.5)]
        xs = sorted(int(x["p"][str(i)]) for x in self._around if x.get("p", {}).get(str(i)))
        return xs[len(xs) // 2] if xs else int(p0)

    def earlier(self, i):
        """The card's price in the snapshot from about an hour ago, if there is one."""
        p = (self.hour_ago or {}).get("p", {}).get(str(i))
        return int(p) if p else None

    def steady(self, i):
        """True when the current price and the reading about an hour earlier agree within CONFIRM_GAP%."""
        p, p1 = self.prices.get(i), self.earlier(i)
        return bool(p and p1 and abs(p / p1 - 1) * 100 <= CONFIRM_GAP)

    def move_confirmed(self, i, pct):
        """A day-long move is real if the hour-old reading already showed at least half of it and the
        current price agrees with that reading. One glitched listing can't pass both."""
        p0 = self.base_24h(i)
        p1 = self.earlier(i)
        if not (p0 and p1 and self.steady(i)):
            return False
        earlier_pct = (p1 / p0 - 1) * 100
        return earlier_pct <= pct / 2 if pct < 0 else earlier_pct >= pct / 2

    def floor_steady(self, ovr, gap=25):
        """True when the cheapest card at this rating agrees with the previous 84/85/86 reading (8-90 minutes old)."""
        now, key = self.floor(ovr), f"f{ovr}"
        for p in reversed(self.hist):
            age = self.t - parse(p["t"])
            if age < timedelta(minutes=8):
                continue
            if age > timedelta(minutes=90) or not p.get(key):
                return False
            return bool(now and abs(now / p[key] - 1) * 100 <= gap)
        return False

    def moves_24h(self, min_price=5000):
        """(pct, coin change, id) for cards worth min_price+ against the snapshot from about a day ago."""
        if not self.day_ago:
            return []
        out = []
        for k in self.day_ago["p"]:
            p, p0 = self.prices.get(int(k)), self.base_24h(int(k))
            if p and p0 and max(p, p0) >= min_price:
                out.append(((p / p0 - 1) * 100, p - p0, int(k)))
        return out


# ---------------------------------------------------------------- weekly cycle

def next_weekday(t, weekday, hour, minute=0):
    """Next time (after t) on a UK weekday (Mon=0) at a UK clock time."""
    local = t.astimezone(UK)
    day = local.date() + timedelta(days=(weekday - local.weekday()) % 7)
    cand = datetime(day.year, day.month, day.day, hour, minute, tzinfo=UK)
    if cand <= local:
        day += timedelta(days=7)
        cand = datetime(day.year, day.month, day.day, hour, minute, tzinfo=UK)
    return cand.astimezone(timezone.utc)


def phase(t):
    """Where the FUT week is, in UK time."""
    local = t.astimezone(UK)
    wd, h = local.weekday(), local.hour + local.minute / 60
    if wd == 3 and 8 <= h < 14:
        return "rewards"     # Rivals rewards just paid out
    if wd == 3 or (wd == 4 and h < 12):
        return "prefriday"
    if wd in (4, 5) or (wd == 6 and h < 18):
        return "weekend"
    if wd == 6 or (wd == 0 and h < 12):
        return "sunday"
    return "midweek"


# ---------------------------------------------------------------- daily 6 PM drop

DROP_HOUR = 18                      # EA's daily content drop, UK time
DROP_MIN = 5                        # recorded drops of a kind before the desk gives timing advice
DROP_KEYS = {"f84": "84s", "f85": "85s", "f86": "86s", "i100": "Top 100 index"}


def drop_time(day):
    return datetime(day.year, day.month, day.day, DROP_HOUR, tzinfo=UK).astimezone(timezone.utc)


def readings():
    """(time, values) for the 84/85/86 floors and the Top 100 index: the desk's 10-minute points plus
    market_extras' hourly points, oldest first."""
    pts = []
    for p in read("history.json", {}).get("points", []):
        at = parse(p.get("t"))
        if at:
            pts.append((at, {k: p.get(k) for k in DROP_KEYS}))
    for row in read("market-index.json", {}).get("points", []):
        at = parse(row[0]) if row else None
        if at and len(row) >= 5:
            pts.append((at, {"i100": row[1], "f84": row[2], "f85": row[3], "f86": row[4]}))
    pts.sort(key=lambda p: p[0])
    return pts


def nearest(pts, aim, lo, hi):
    inside = [p for p in pts if lo <= p[0] <= hi]
    return min(inside, key=lambda p: abs(p[0] - aim)) if inside else None


def drop_log(ledger, t, pts=None):
    """Record, once per evening, how prices moved from just before 6 PM UK to about 8 PM."""
    log = ledger.setdefault("dropLog", [])
    have = {d.get("date") for d in log}
    pts = readings() if pts is None else pts
    today = t.astimezone(UK).date()
    for back in range(14):
        day = today - timedelta(days=back)
        drop = drop_time(day)
        if day.isoformat() in have or t < drop + timedelta(hours=3):
            continue
        before = nearest(pts, drop - timedelta(minutes=15), drop - timedelta(minutes=90), drop - timedelta(minutes=1))
        after = nearest(pts, drop + timedelta(hours=2), drop + timedelta(minutes=90), drop + timedelta(hours=3))
        if not before or not after:
            continue
        chg = {}
        for k in DROP_KEYS:
            a, b = before[1].get(k), after[1].get(k)
            if k == "i100" and a == b:
                continue  # an index to two decimals never sits still for two hours: the reading was stale
            if a and b and abs(b / a - 1) < 0.5:  # a bigger jump is a basket rebase or a bad reading
                chg[k] = round((b / a - 1) * 100, 1)
        if chg:
            log.append({"date": day.isoformat(), "weekday": day.weekday(), "before": iso(before[0]), "after": iso(after[0]), "chg": chg})
    log.sort(key=lambda d: d["date"])
    ledger["dropLog"] = log[-KEEP_DROPS:]
    return ledger["dropLog"]


def drop_stats(log, friday, keys):
    """Average move across the last 14 recorded drops of one kind (Friday promo nights or the rest)."""
    rows = [d for d in log if (d.get("weekday") == 4) == friday][-14:]
    vals = []
    for d in rows:
        v = [d["chg"][k] for k in keys if k in d.get("chg", {})]
        if v:
            vals.append(sum(v) / len(v))
    n = len(vals)
    return {"n": n, "avg": round(sum(vals) / n, 1) if n else None,
            "up": sum(1 for v in vals if v > 1), "down": sum(1 for v in vals if v < -1)}


def drop_advice(s, what, drop):
    """Turn a drop record into a tone and a sentence. Times are tokens the site shows in local time."""
    n, avg, up, down = s["n"], s["avg"], s["up"], s["down"]
    if n < DROP_MIN:
        return {**s, "tone": "watch", "text": f"Still measuring: {n} drop{'' if n == 1 else 's'} of this kind recorded so far. Advice starts after {DROP_MIN}."}
    buy_by, sell_from = tok(drop - timedelta(minutes=15)), tok(drop + timedelta(minutes=90))
    if avg >= 2 and up >= 0.6 * n:
        tax = (" That beats the 5% tax on average." if avg > TAX_BREAK_EVEN
               else " That is less than the 5% tax, so use it to time cards you need anyway, not to flip.")
        return {**s, "tone": "buy", "text": f"{what} rose after {up} of the last {n} drops ({avg:+.1f}% on average): buy what you need before {buy_by}, sell spares from {sell_from}.{tax}"}
    if avg <= -2 and down >= 0.6 * n:
        return {**s, "tone": "hold", "text": f"{what} fell after {down} of the last {n} drops ({avg:+.1f}% on average): sell spares before {buy_by} and buy after {sell_from}."}
    return {**s, "tone": "watch", "text": f"{what} had no steady move around the last {n} drops ({up} up, {down} down, {avg:+.1f}% on average): no timing edge."}


def daily_drop(log, t):
    today = t.astimezone(UK).date()
    drop = drop_time(today)
    prev = drop if drop <= t else drop_time(today - timedelta(days=1))
    nxt = drop if drop > t else drop_time(today + timedelta(days=1))
    friday = nxt.astimezone(UK).weekday() == 4
    fodder = drop_advice(drop_stats(log, friday, ("f84", "f85", "f86")), "84 to 86 fodder", nxt)
    meta = drop_advice(drop_stats(log, friday, ("i100",)), "The Top 100 index (expensive meta cards)", nxt)
    recent = [{"date": d["date"], "friday": d.get("weekday") == 4, "chg": d["chg"]} for d in log[-7:]][::-1]
    return {"nextAt": iso(nxt), "prevAt": iso(prev), "friday": friday,
            "group": "Friday promo drops" if friday else "Weekday drops",
            "measured": len(log), "fodder": fodder, "meta": meta, "recent": recent,
            "method": "Change from the last reading before 6 PM UK to the one nearest 8 PM UK, from Ezzcoins' own price feed. "
                      "Fridays, when promos usually land, are measured separately from other days."}


# ---------------------------------------------------------------- ledger: grading

def strategy_record(calls):
    rec = {}
    for c in calls:
        k = c.get("strategy")
        if k and c.get("status") in ("hit", "miss"):
            r = rec.setdefault(k, {"hit": 0, "miss": 0, "last": None})
            r[c["status"]] += 1
            g = parse(c.get("gradedAt"))
            if g and (r["last"] is None or g > r["last"]):
                r["last"] = g
    return rec


GRADED_FIELDS = ("strategy", "tone", "status", "result", "entry", "exit", "exitRecordedAt", "madeAt", "gradedAt")


def merge_graded(into, other):
    """Join two stores of graded calls (id -> how it was graded). When both hold a call, its first grading wins."""
    for cid, g in (other or {}).items():
        if not isinstance(g, dict) or g.get("status") not in ("hit", "miss"):
            continue
        mine = into.get(cid)
        if mine is None or (g.get("gradedAt") or "~") < (mine.get("gradedAt") or "~"):
            into[cid] = g
    return into


def settle_known_calls(ledger):
    """A call that is already in the graded store keeps that grade, even if an older copy of
    data/ledger.json still shows it open: it is never graded (or counted) a second time."""
    graded = ledger.get("graded") or {}
    for c in ledger.get("calls", []):
        g = graded.get(c.get("id"))
        if g and c.get("status") in ("pending", "open", "hit", "miss"):
            c.update({k: g[k] for k in ("status", "result", "entry", "exit", "exitRecordedAt", "gradedAt") if g.get(k) is not None})
            c["counted"] = True


def tally(ledger):
    """Lifetime totals, rebuilt on every run from ledger["graded"]: one entry per graded call, keyed by its id.
    Old calls are trimmed from the list but stay in the graded store, so the track record never forgets,
    and a call can't be counted twice, even when another writer puts back an older data/ledger.json."""
    graded = ledger.get("graded")
    if not isinstance(graded, dict):
        graded = ledger["graded"] = {}
    for c in ledger.get("calls", []):
        if c.get("status") in ("hit", "miss") and c.get("id"):
            if c["id"] not in graded:
                graded[c["id"]] = {k: c.get(k) for k in GRADED_FIELDS}
            c["counted"] = True
    rec = {"hit": 0, "miss": 0, "sum": 0.0, "buyN": 0, "buySum": 0.0, "since": None}
    stats = {}
    for cid, g in sorted(graded.items(), key=lambda kv: (kv[1].get("gradedAt") or kv[1].get("madeAt") or "", kv[0])):
        res = g.get("result") if isinstance(g.get("result"), (int, float)) else 0.0
        hit = g.get("status") == "hit"
        rec["hit" if hit else "miss"] += 1
        rec["sum"] = round(rec["sum"] + res, 2)
        if g.get("tone") == "buy":
            rec["buyN"] += 1
            rec["buySum"] = round(rec["buySum"] + res, 2)
        if g.get("madeAt") and (not rec["since"] or g["madeAt"] < rec["since"]):
            rec["since"] = g["madeAt"]
        k = g.get("strategy")
        if k:
            s = stats.setdefault(k, {"hit": 0, "miss": 0, "sum": 0.0, "recent": [], "last": None})
            s["hit" if hit else "miss"] += 1
            s["sum"] = round(s["sum"] + res, 2)
            s["recent"] = (s["recent"] + [[cid, res, hit]])[-RECENT:]
            when = g.get("gradedAt") or g.get("madeAt")
            if when and (not s["last"] or when > s["last"]):
                s["last"] = when
    ledger["record"] = rec
    ledger["strategies"] = stats
    return rec


def paper_passes(test, need):
    """True/False once a strategy has enough paper calls (hits more than half the time and wins after tax), else None.
    Exactly half is a coin flip: a strategy at 7 of 14 once switched on and off between runs."""
    if not need or not test or test.get("n", 0) < need:
        return None
    return test["hit"] / test["n"] > 0.5 and test["avg"] > 0


def standing(s, t, key=None, test=None):
    """How a strategy stands now, from its lifetime totals, its last RECENT graded calls and its paper test."""
    s = s or {}
    hit, miss = s.get("hit", 0), s.get("miss", 0)
    recent = s.get("recent") or []
    rn = len(recent)
    rhit = sum(1 for r in recent if r[2])
    rsum = sum(r[1] for r in recent)
    ravg = rsum / rn if rn else None
    bad = rn >= 3 and (rhit / rn < 0.5 or ravg < 0)
    last = parse(s.get("last")) if s.get("last") else None
    paused = bool(bad and last and t - last < PAUSE)
    status = "new" if not rn else "paused" if paused else "retest" if bad else "active"
    conf = "low" if bad else "high" if (rn >= 3 and rhit / rn >= 0.7 and ravg > 0) else "medium"
    passes = paper_passes(test, BACKTESTED.get(key))
    expected = rsum / (rn + PRIOR)
    if passes is False or (passes is None and key in NEEDS_TEST):
        status, conf, paused = "off", "low", False
    elif passes:
        w = min(test["n"], 6)        # a passing paper test counts like up to 6 extra calls
        expected = (rsum + test["avg"] * w) / (rn + w + PRIOR)
    return {"hit": hit, "miss": miss, "n": hit + miss, "avg": round(s.get("sum", 0) / (hit + miss), 1) if hit + miss else None,
            "recentN": rn, "recentHit": rhit, "recentAvg": round(ravg, 1) if ravg is not None else None,
            "expected": expected, "status": status, "confidence": conf,
            "pausedUntil": iso(last + PAUSE) if paused else None,
            "test": {f: test[f] for f in ("n", "hit", "avg")} if test and key in BACKTESTED else None}


def strategy_board(ledger, t):
    """The public scoreboard: every strategy, its record and whether the desk is using it."""
    stats, tests = ledger.get("strategies", {}), ledger.get("backtest", {}).get("strategies", {})
    board = []
    for k in ORDER:
        st = standing(stats.get(k), t, k, tests.get(k))
        board.append({"key": k, "name": STRATEGIES[k]["name"], "why": STRATEGIES[k]["why"],
                      **{f: st[f] for f in ("hit", "miss", "avg", "recentN", "recentHit", "recentAvg", "status", "confidence", "pausedUntil", "test")}})
    rank = {"active": 0, "retest": 1, "new": 2, "paused": 3, "off": 4}
    board.sort(key=lambda b: (rank[b["status"]], -(b["recentAvg"] or 0), ORDER.index(b["key"])))
    return board


def ref_price(mk, ref):
    """Current price for a call's ref, or None if Ezzcoins can't read it."""
    if not mk.fresh or not isinstance(ref, dict):
        return None
    if ref.get("kind") == "item" and ref.get("eaId"):
        return mk.prices.get(int(ref["eaId"]))
    if ref.get("kind") == "floor" and ref.get("ovr") and ref.get("source") in ("Ezzcoins price feed", "FUT.GG"):
        return mk.floor(int(ref["ovr"]))
    return None  # FUTBIN page refs can't be read automatically


def result_of(call, entry, exit_):
    if call.get("rule") == "sell_lower":
        res = (entry - exit_) / entry * 100
        return round(res, 1), exit_ < entry
    res = (math.floor(exit_ * 0.95) - entry) / entry * 100
    return round(res, 1), res > 0


def grade(mk, ledger, t):
    lessons = ledger.setdefault("lessons", [])
    graded = []
    for c in ledger.get("calls", []):
        st = c.get("status")
        if st == "pending" and parse(c.get("entryAt")) and parse(c["entryAt"]) <= t:
            p = ref_price(mk, c.get("ref"))
            if p:
                c.update({"entry": p, "entryRecordedAt": iso(mk.published), "status": "open"})
            elif t - parse(c["entryAt"]) > timedelta(hours=12):
                c.update({"status": "void", "note": (c.get("note", "") + f" Voided {iso(t)}: entry price unreadable 12 hours past due.").strip()})
        elif st == "open" and parse(c.get("checkAt")) and parse(c["checkAt"]) <= t:
            p = ref_price(mk, c.get("ref"))
            late = t - parse(c["checkAt"])
            if p and late <= timedelta(hours=6) and c.get("entry"):
                res, hit = result_of(c, c["entry"], p)
                c.update({"exit": p, "exitRecordedAt": iso(mk.published), "result": res, "gradedAt": iso(t), "status": "hit" if hit else "miss"})
                graded.append(c)
            elif late > timedelta(hours=12):
                c.update({"status": "void", "note": (c.get("note", "") + f" Voided {iso(t)}: exit price unreadable 12 hours past due.").strip()})
    tally(ledger)
    stats = ledger.get("strategies", {})
    for c in graded:
        k = c.get("strategy")
        st = standing(stats.get(k), t)
        record = (f'{STRATEGIES[k]["name"]} is now {st["hit"]} of {st["n"]}'
                  + (f', averaging {st["avg"]:+.1f}% after tax.' if st["avg"] is not None else ".")) if k in STRATEGIES else ""
        move = f'{coins(c["entry"])} → {coins(c["exit"])}'
        if c["status"] == "hit":
            text = f'Hit: {c["title"]} ({move}, {c["result"]:+.1f}%). It worked because {STRATEGIES[k]["why"]}. {record}' if k in STRATEGIES \
                else f'Hit: {c["title"]} ({move}, {c["result"]:+.1f}%).'
        else:
            paused = k in STRATEGIES and st["status"] == "paused"
            text = (f'Miss: {c["title"]} ({move}, {c["result"]:+.1f}%). The idea that {STRATEGIES[k]["why"]} did not hold this time. {record}'
                    + (" Its recent calls lose after tax, so the strategy is paused for 7 days." if paused else "")) if k in STRATEGIES \
                else f'Miss: {c["title"]} ({move}, {c["result"]:+.1f}%).'
        c["lesson"] = text
        lessons.append({"date": iso(t), "text": text, "kind": c["status"], "callId": c["id"]})
    keep = [l for l in lessons if l.get("kind") == "tip" and l.get("status") == "proven"]
    rest = [l for l in lessons if l not in keep]
    ledger["lessons"] = sorted(keep + rest[-max(0, KEEP_LESSONS - len(keep)):], key=lambda l: l.get("date", ""))
    return graded


# ---------------------------------------------------------------- ledger: new calls

def candidates(mk, t, used, log=()):
    """Possible calls now, as (strategy, call fields). Every price a call relies on must agree with the
    reading about an hour earlier, so one glitched listing can't trigger a call."""
    out = []
    ph = phase(t)
    meta_ok = lambda i: (mk.info.get(i, {}).get("meta") or 0) >= max(84, (mk.info.get(i, {}).get("ovr") or 0))

    # Buy before the weekend: Tuesday evening to Thursday, check Friday 20:00 UK.
    check = next_weekday(t, 4, 20)
    if timedelta(hours=24) <= check - t <= timedelta(hours=72) and ph in ("midweek", "prefriday", "rewards"):
        pool = [i for i, p in mk.prices.items() if 8000 <= p <= 150000 and mk.info.get(i, {}).get("base") and meta_ok(i) and i not in used
                and mk.steady(i)]
        pool.sort(key=lambda i: -(mk.info[i]["meta"] - 6 * math.log10(mk.prices[i])))
        if pool:
            i = pool[0]
            out.append(("weekend", {"tone": "buy", "rule": "buy_after_tax", "item": i, "checkAt": check,
                                    "title": f"Buy {mk.label(i)} for the weekend, sell by Friday evening",
                                    "why": f'meta rating {mk.info[i]["meta"]} at {mk.info[i]["metaPos"]} for {coins(mk.prices[i])} coins'}))

    moves = mk.moves_24h(10000)
    # Buy the dip: a playable card worth 10K+ that fell 10%+ in a day.
    dips = sorted((m for m in moves if m[0] <= -10 and meta_ok(m[2]) and m[2] not in used and mk.prices.get(m[2], 0) >= 10000
                   and mk.move_confirmed(m[2], m[0])), key=lambda m: m[0])
    if dips:
        pct, _, i = dips[0]
        out.append(("rebound", {"tone": "buy", "rule": "buy_after_tax", "item": i, "checkAt": t + timedelta(hours=48),
                                "title": f"Buy {mk.label(i)} after its {abs(pct):.0f}% fall, sell in two days",
                                "why": f"down {abs(pct):.1f}% in about a day"}))

    # Sell the slide: the same falls, the opposite bet (it runs only while its paper calls win).
    if dips:
        pct, _, i = dips[0]
        out.append(("slide", {"tone": "sell", "rule": "sell_lower", "item": i, "checkAt": t + timedelta(hours=48),
                              "title": f"Sell {mk.label(i)} after its {abs(pct):.0f}% fall, expect it lower in two days",
                              "why": f"down {abs(pct):.1f}% in about a day"}))

    # Sell the spike: a card worth 10K+ that rose 15%+ in a day.
    spikes = sorted((m for m in moves if m[0] >= 15 and m[2] not in used and mk.prices.get(m[2], 0) >= 10000
                     and mk.prices[m[2]] - m[1] >= 5000 and (mk.info.get(m[2], {}).get("ovr") or 0) >= 80
                     and mk.move_confirmed(m[2], m[0])), key=lambda m: -m[0])
    if spikes:
        pct, _, i = spikes[0]
        out.append(("fade", {"tone": "sell", "rule": "sell_lower", "item": i, "checkAt": t + timedelta(hours=48),
                             "title": f"Sell {mk.label(i)} after its {pct:.0f}% jump, expect it lower in two days",
                             "why": f"up {pct:.1f}% in about a day"}))

    # Rivals rewards dip: Thursday morning, buy the cheapest 86 (not 81-84, which sit at a hard floor).
    # Needs two agreeing floor readings: a one-reading dump after the payout once reverted within the hour.
    f86 = mk.floor(86)
    if ph == "rewards" and f86 and f86 > 1000 and mk.floor_steady(86):
        out.append(("rewards", {"tone": "buy", "rule": "buy_after_tax", "floor": 86, "checkAt": next_weekday(t, 5, 12),
                                "title": "Buy 86-rated fodder after Rivals rewards, sell or use by Saturday",
                                "why": f"the cheapest 86 is {coins(f86)} coins"}))

    # Buy before the 6 PM drop: only for a rating that rose after at least 70% of the last 4+ recorded
    # drops of the same kind, by more than the tax on average. Bought 15 min to 2 h before, checked at 8 PM.
    drop = drop_time(t.astimezone(UK).date())
    if log and timedelta(minutes=15) <= drop - t <= timedelta(hours=2):
        friday = drop.astimezone(UK).weekday() == 4
        best = None
        for o in (84, 85, 86):
            s = drop_stats(log, friday, (f"f{o}",))
            if s["n"] >= 4 and s["avg"] > TAX_BREAK_EVEN + 0.7 and s["up"] >= 0.7 * s["n"] and mk.floor(o) and mk.floor_steady(o):
                if best is None or s["avg"] > best[1]["avg"]:
                    best = (o, s)
        if best:
            o, s = best
            out.append(("drop", {"tone": "buy", "rule": "buy_after_tax", "floor": o, "checkAt": drop + timedelta(hours=2),
                                 "title": f"Buy {o}-rated fodder before the 6 PM drop, sell after 8 PM",
                                 "why": f"{o}s rose after {s['up']} of the last {s['n']} {'Friday' if friday else 'weekday'} drops, {s['avg']:+.1f}% on average"}))
    return out


def rewards_slot_open(t):
    """True on the desk's Thursday until the Rivals rewards window closes (Thursday 14:00 UK time).
    The desk's day is Zurich time, so it starts an hour before Thursday begins in the UK."""
    if t.astimezone(DESK_TZ).weekday() != 3:
        return False
    local = t.astimezone(UK)
    return local.weekday() == 2 or (local.weekday() == 3 and local.hour < 14)


def make_calls(mk, ledger, t):
    if not mk.fresh:
        return None
    calls = ledger.setdefault("calls", [])
    today = t.astimezone(DESK_TZ).date()
    made_today = [c for c in calls if parse(c.get("madeAt")) and parse(c["madeAt"]).astimezone(DESK_TZ).date() == today]
    if len(made_today) >= CALLS_PER_DAY:
        return None
    if made_today and t - max(parse(c["madeAt"]) for c in made_today) < CALL_GAP:
        return None
    used = {int(c["ref"]["eaId"]) for c in calls if (c.get("ref") or {}).get("eaId") and parse(c.get("madeAt")) and t - parse(c["madeAt"]) < timedelta(days=7)}
    used_strategies = {c.get("strategy") for c in made_today}
    stats, tests = ledger.get("strategies", {}), ledger.get("backtest", {}).get("strategies", {})
    # Keep one of Thursday's calls for the Rivals rewards dip. Calls made overnight once used up both
    # of the day's calls hours before the payout, so the desk couldn't buy the dump that followed.
    keep_slot = (rewards_slot_open(t) and "rewards" not in used_strategies and len(made_today) >= CALLS_PER_DAY - 1)

    # Try strategies in order of their expected result after tax: a proven strategy first, an untested one
    # (expected 0%) next, and one being retested after a pause last.
    options = []
    for k, f in candidates(mk, t, used, ledger.get("dropLog", [])):
        st = standing(stats.get(k), t, k, tests.get(k))
        if st["status"] in ("paused", "off") or k in used_strategies or (keep_slot and k != "rewards"):
            continue
        options.append((-st["expected"], ORDER.index(k), k, f, st))
    if not options:
        return None
    options.sort(key=lambda o: o[:2])
    _, _, k, f, st = options[0]
    conf, n = st["confidence"], st["n"]
    entry = mk.prices.get(f["item"]) if "item" in f else mk.floor(f["floor"])
    if not entry:
        return None
    if "item" in f:
        i = f["item"]
        c = mk.info.get(i, {})
        ref = {"label": f"{mk.label(i)} · console", "source": FEED["label_src"], "url": FEED["url"], "kind": "item",
               "eaId": i, "name": c.get("name"), "version": c.get("version") or "", "ovr": c.get("ovr")}
    else:
        ref = {"label": f"Cheapest {f['floor']} · console", "source": FEED["label_src"], "url": FEED["url"], "kind": "floor", "ovr": f["floor"]}
    slug = (ref.get("name") or f"{f.get('floor')}floor").lower()
    slug = "".join(ch if ch.isalnum() else "-" for ch in slug).strip("-")[:24]
    picked = f["why"] if k == "drop" else f"it is {f['why']}"
    record = (f'This strategy is {st["hit"]} of {n} so far, averaging {st["avg"]:+.1f}% after tax. ' if n
              else "This is the strategy's first tracked call. ")
    if st["status"] == "retest":
        record += "It was paused after losing calls, so this is a low-confidence retest. "
    call = {"id": f"c-{today.isoformat()}-{k}-{slug}", "madeAt": iso(t), "tone": f["tone"], "title": f["title"], "confidence": conf,
            "ref": ref, "rule": f["rule"], "strategy": k, "entryAt": iso(t), "entry": entry, "entryRecordedAt": iso(mk.published),
            "checkAt": iso(f["checkAt"]), "exit": None, "status": "open", "result": None, "confirmed": True,
            "note": (f'{STRATEGIES[k]["name"]}: {STRATEGIES[k]["why"]}. Picked because {picked}. '
                     + "Two price readings about an hour apart agree on this price. " + record
                     + ("It sells and buys back, so the 5% tax is counted." if f["rule"] == "buy_after_tax" else "A sell call is a hit if the price is lower at check time."))}
    if any(x["id"] == call["id"] for x in calls):
        call["id"] += "-" + t.strftime("%H%M")
    calls.append(call)
    ledger["calls"] = calls[-KEEP_CALLS:]
    return call


# ---------------------------------------------------------------- snapshot

def fodder_board(mk):
    out = []
    for o in range(81, 92):
        p = mk.floor(o)
        if p:
            out.append({"ovr": o, "price": p, "score": SCORES[o]})
    return out


def sbc_list(t):
    data = read("sbcsolutions.json", {}).get("sbcs") or {}
    items = list(data.values()) if isinstance(data, dict) else list(data)
    live = []
    for s in items:
        end = parse(s.get("endTime"))
        if (end and end <= t) or s.get("category") == 5 or str(s.get("name", "")).startswith("Intro to"):
            continue  # expired, or a permanent beginner set / re-roll
        live.append(s)
    # Player and upgrade SBCs first, then by cost.
    live.sort(key=lambda s: ({1: 0, 2: 1}.get(s.get("category"), 2), -(parse(s.get("added")) or datetime(2000, 1, 1, tzinfo=timezone.utc)).timestamp()))
    out = []
    for s in live[:8]:
        end = parse(s.get("endTime"))
        expires = ""
        if end:
            left = end - t
            expires = tok(end) if left <= timedelta(hours=48) else f"About {round(left.total_seconds() / 86400)} days left"
        added = parse(s.get("added"))
        new = added and t - added <= timedelta(hours=24)
        out.append({"name": s.get("name"), "cost": short(s["cost"]) if s.get("cost") else "–", "expires": expires,
                    "note": ("New today. " if new else "") + (s.get("note") or "")})
    return out, live


def movers(mk):
    # Cards worth 5,000+ that stayed above 2,000 and are rated 75+: leaves out listing glitches on cheap cards.
    m = [x for x in mk.moves_24h(5000) if min(mk.prices[x[2]], mk.prices[x[2]] - x[1]) >= 2000 and (mk.info.get(x[2], {}).get("ovr") or 0) >= 75]
    fall = sorted((x for x in m if x[0] <= -3), key=lambda x: x[0])[:8]
    rise = sorted((x for x in m if x[0] >= 3), key=lambda x: -x[0])[:8]
    fmt = lambda x: {"name": mk.info.get(x[2], {}).get("name"), "version": mk.info.get(x[2], {}).get("version") or "",
                     "ovr": mk.info.get(x[2], {}).get("ovr"), "pct": round(x[0], 2),
                     "price": ("+" if x[1] > 0 else "−") + coins(abs(x[1])) + " coins", "eaId": x[2]}
    return [fmt(x) for x in fall if mk.info.get(x[2])], [fmt(x) for x in rise if mk.info.get(x[2])]


def meta_cards(mk):
    """The best meta rating in each price band among tradeable base cards."""
    out, seen = [], set()
    for cap in (3000, 6000, 12000, 25000, 50000, 100000, 200000, 400000):
        pool = [i for i, p in mk.prices.items() if p <= cap and mk.info.get(i, {}).get("base") and mk.info[i].get("meta") and i not in seen]
        if not pool:
            continue
        i = max(pool, key=lambda i: (mk.info[i]["meta"], -mk.prices[i]))
        seen.add(i)
        c = mk.info[i]
        out.append({"name": c["name"], "ovr": c["ovr"], "pos": c["metaPos"], "price": mk.prices[i], "eaId": i, "priceState": 0,
                    "at": iso(mk.published), "src": "FUT.GG", "priceAt": iso(mk.published),
                    "note": f'Meta {c["meta"]} at {c["metaPos"]}: the best Ezzcoins meta rating for up to {short(cap)}'})
    return out


def verdict(mk, ph):
    m = mk.market
    idx, chg, mom = m.get("idx100"), m.get("idx100Chg"), m.get("momentum")
    if mom is None or idx is None:
        return {"tone": "watch", "label": "Waiting for data", "headline": "The market read is waiting for enough price data.",
                "detail": "Ezzcoins' index needs a few hourly readings before it can say which way prices move."}
    chg = chg or 0
    if mom >= 55 and chg > 0:
        tone, label, head = "sell", "Prices rising", "Card prices are rising: sell spare cards into the rise and keep the ones you play."
    elif mom <= 45 or chg < -2:
        tone, label, head = "hold", "Prices falling", "Card prices are falling: hold your coins and buy only cards you will play."
    else:
        tone, label, head = "watch", "Steady market", "Card prices are steady: no strong move either way right now."
    f = {o: mk.floor(o) for o in (84, 85, 86)}
    cyc = {"rewards": "Rivals rewards just paid out, so fodder supply is high this morning.",
           "prefriday": "Champions weekend starts Friday, when demand for meta cards usually peaks.",
           "weekend": "It is Champions weekend, when meta cards usually sell best.",
           "sunday": "The weekend is ending, and prices usually ease into Monday.",
           "midweek": "Midweek is usually the quietest time to buy cards for the weekend."}[ph]
    detail = (f"Ezzcoins' Top 100 index is {idx:.1f} ({chg:+.1f}% in a day) and momentum is {mom:.0f}: "
              f"{(m.get('momentumLabel') or '').lower() or 'mixed'}. "
              + (f"84s cost {coins(f[84])}, 85s {coins(f[85])} and 86s {coins(f[86])}. " if all(f.values()) else "")
              + cyc)
    return {"tone": tone, "label": label, "headline": head, "detail": detail}


def fodder_move(board):
    rows = [r for r in board if 84 <= r["ovr"] <= 88]
    if len(rows) < 3:
        return None
    rows.sort(key=lambda r: r["price"] / r["score"])
    a, b = rows[0], rows[1]
    worst = rows[-1]
    return {"tone": "watch", "confidence": "medium", "when": "Every update",
            "title": f"Fodder: {a['ovr']}s are the best value per point, {worst['ovr']}s the dearest",
            "detail": (f"Cheapest prices: " + ", ".join(f"{r['ovr']}s {coins(r['price'])} ({r['price'] / r['score']:.2f} coins per Item Score point)" for r in sorted(rows, key=lambda r: r['ovr']))
                       + f". For SBCs that ask for an Item Score, {a['ovr']}s then {b['ovr']}s fill it cheapest. Use fodder in SBCs rather than trading it: selling costs the 5% tax.")}


def cycle_move(t, ph):
    rewards = next_weekday(t, 3, 7, 59)
    friday = next_weekday(t, 4, 18)
    if ph == "rewards":
        return {"tone": "buy", "confidence": "low", "when": f"Until {tok(next_weekday(t, 3, 14))}",
                "title": "Rivals rewards just paid out: buy SBC fodder now, not later",
                "detail": "Rewards add fodder to the market on Thursday morning, which usually makes it cheapest then. Buy what your SBCs need now; selling it again costs the 5% tax."}
    if ph == "prefriday":
        return {"tone": "buy", "confidence": "low", "when": f"Until {tok(friday)}",
                "title": "Buy cards you want for Champions before Friday evening",
                "detail": "Demand for meta cards usually peaks when Champions weekend starts, so buying the cards you will play earlier is usually cheaper."}
    if ph == "weekend":
        return {"tone": "sell", "confidence": "low", "when": f"Until {tok(next_weekday(t, 6, 18))}",
                "title": "Champions weekend: sell spare meta cards, keep the ones you play",
                "detail": "Meta cards usually sell best during the weekend. Selling and rebuying cards you play costs the 5% tax and a higher weekend price."}
    if ph == "sunday":
        return {"tone": "watch", "confidence": "low", "when": f"Until {tok(next_weekday(t, 0, 12))}",
                "title": "Weekend is ending: wait before buying",
                "detail": f"Prices usually ease as the weekend ends and players sell their squads. The next Rivals rewards come {tok(rewards)}."}
    return {"tone": "watch", "confidence": "low", "when": f"Until {tok(rewards)}",
            "title": "Quiet midweek: plan your weekend squad now",
            "detail": f"Midweek is usually the cheapest time to buy cards you will play at the weekend. The next Rivals rewards come {tok(rewards)} and add fodder supply."}


def call_move(mk, c):
    p = ref_price(mk, c["ref"])
    now_txt = f" Now {coins(p)}." if p else ""
    return {"tone": c["tone"], "confidence": c["confidence"], "ledgerId": c["id"], "title": c["title"], "when": f"Check {tok(parse(c['checkAt']))}",
            "detail": f"Tracked call: in at {coins(c['entry'])} coins.{now_txt} {c.get('note', '')}".strip()}


def news_items(mk, sbcs_live, fallers, risers, board, t):
    news = []
    m = mk.market
    if m.get("idx100") is not None:
        news.append({"kind": "data", "source": "Ezzcoins", "title": f"Top 100 index {m['idx100']:.1f} ({(m.get('idx100Chg') or 0):+.1f}% in a day)",
                     "detail": (f"Momentum {m['momentum']:.0f}: {(m.get('momentumLabel') or '').lower()}. " if m.get('momentum') is not None else "")
                     + f"ICON index {m.get('icons') or '–'} ({(m.get('iconsChg') or 0):+.1f}%)."})
    if board:
        news.append({"kind": "data", "source": "Ezzcoins", "title": "Fodder prices",
                     "detail": ", ".join(f"{r['ovr']}s {coins(r['price'])}" for r in board if 84 <= r["ovr"] <= 89) + "."})
    if fallers:
        news.append({"kind": "data", "source": "Ezzcoins", "title": "Biggest falls in the last day",
                     "detail": "; ".join(f"{f['name']} {f['ovr']} {f['version']} {f['pct']:.1f}% ({f['price']})".replace("  ", " ") for f in fallers[:3]) + "."})
    if risers:
        news.append({"kind": "data", "source": "Ezzcoins", "title": "Biggest rises in the last day",
                     "detail": "; ".join(f"{f['name']} {f['ovr']} {f['version']} +{f['pct']:.1f}% ({f['price']})".replace("  ", " ") for f in risers[:3]) + "."})
    new_sbcs = [s for s in sbcs_live if parse(s.get("added")) and t - parse(s["added"]) <= timedelta(hours=24)]
    if new_sbcs:
        news.append({"kind": "official", "source": "Ezzcoins", "title": f"{len(new_sbcs)} new SBC{'s' if len(new_sbcs) > 1 else ''} today",
                     "detail": "; ".join(f"{s['name']} ({short(s['cost'])})" if s.get("cost") else s["name"] for s in new_sbcs[:5]) + "."})
    cards = [c for c in read("newcards.json", {}).get("cards", []) if parse(c.get("createdAt") or c.get("added")) and t - parse(c.get("createdAt") or c.get("added")) <= timedelta(hours=24)]
    if cards:
        cards.sort(key=lambda c: -(c.get("ovr") or 0))
        news.append({"kind": "official", "source": "Ezzcoins", "title": f"{len(cards)} new special card{'s' if len(cards) > 1 else ''} in the last day",
                     "detail": "Including " + ", ".join(f"{c['name']} {c['ovr']} {c.get('version') or ''}".strip() for c in cards[:4]) + "."})
    return news[:6]


def events(prev, t):
    out = []
    rewards = next_weekday(t, 3, 7, 59)
    totw = next_weekday(t, 2, 18)
    out.append({"date": rewards.astimezone(UK).isoformat(), "title": "Rivals rewards", "impact": "supply", "confirmed": True,
                "detail": "Weekly Rivals rewards are paid out; expect more fodder and tradeable cards on the market."})
    out.append({"date": totw.astimezone(UK).isoformat(), "title": "Team of the Week", "impact": "supply", "confirmed": True,
                "detail": "The new Team of the Week goes into packs."})
    mine = {"Rivals rewards", "Team of the Week"}
    for e in prev.get("events", []):
        d = parse(e.get("date"))
        if d and d > t - timedelta(hours=12) and e.get("title") not in mine and e.get("confirmed"):
            out.append(e)
    out.sort(key=lambda e: parse(e["date"]))
    return out


def drops(prev, t):
    out = []
    for d in prev.get("drops", []):
        seen = parse(d.get("reportedAt") or d.get("firstSeen"))
        if not seen:
            continue
        if d.get("expected") == "Live now" and t - seen > timedelta(days=2):
            continue
        if d.get("official") and t - parse(d.get("firstSeen") or iso(seen)) <= timedelta(days=21):
            out.append(d)
        elif not d.get("official") and t - seen <= timedelta(days=14):
            out.append(d)
    titles = {d["title"] for d in out}
    cards = read("newcards.json", {}).get("cards", [])
    recent = {}
    for c in cards:
        made = parse(c.get("createdAt") or c.get("added"))
        if made and c.get("version") and t - made <= timedelta(days=2):
            recent.setdefault(c["version"], []).append((made, c))
    older = {c.get("version") for c in cards if parse(c.get("createdAt") or c.get("added")) and t - parse(c.get("createdAt") or c.get("added")) > timedelta(days=2)}
    for ver, items in recent.items():
        title = f"{ver} cards are live"
        if ver in older or title in titles or len(items) < 3:
            continue
        items.sort(key=lambda x: -(x[1].get("ovr") or 0))
        out.append({"title": title, "detail": f"{len(items)} new {ver} cards, including " + ", ".join(f"{c['name']} {c['ovr']}" for _, c in items[:4]) + ".",
                    "sheriff": False, "ftr": False, "official": True, "status": "confirmed", "expected": "Live now",
                    "reportedAt": iso(min(m for m, _ in items)), "firstSeen": iso(t), "sources": []})
    return out


# ---------------------------------------------------------------- watched and top cards

def watched_ids():
    counts, url = {}, WATCHLISTS
    for _ in range(20):
        req = urllib.request.Request(url, headers={"User-Agent": "Ezzcoins desk"})
        with urllib.request.urlopen(req, timeout=20) as r:
            page = json.loads(r.read().decode("utf-8"))
        for doc in page.get("documents", []):
            vals = (((doc.get("fields") or {}).get("ids") or {}).get("arrayValue") or {}).get("values") or []
            for v in {int(x["integerValue"]) for x in vals if str(x.get("integerValue", "")).isdigit()}:
                counts[v] = counts.get(v, 0) + 1
        token = page.get("nextPageToken")
        if not token:
            break
        url = WATCHLISTS + "&pageToken=" + urllib.parse.quote(token)
    return counts


def item_for(key, card_ids, newcards):
    if key < 1000000000:
        return key
    k = key - 1000000000
    if str(k) in card_ids:
        return int(card_ids[str(k)])
    for c in newcards:
        if str(c.get("gid")) == str(k) or str(c.get("fid")) == str(k):
            return int(c["eaId"]) if c.get("eaId") else None
    return k


def update_watched(mk, t):
    stamp = DATA / ".cache" / "watchlists-at.json"   # Actions cache: read the watchlists about once an hour
    last = parse(read(".cache/watchlists-at.json", {}).get("at"))
    if last and t - last < timedelta(minutes=50):
        return
    try:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.write_text(json.dumps({"at": iso(t)}))
    except OSError:
        pass
    try:
        counts = watched_ids()
    except Exception as err:  # noqa: BLE001 - keep the previous list if Firestore can't be read
        print("desk: watchlists unreadable, kept the previous list:", str(err)[:120])
        return
    old = read("prices.json", {"players": {}})
    prev = old.get("players", {})
    top = sorted(counts, key=lambda i: (-counts[i], str(i) not in prev, i))[:25]
    if not top:
        return
    card_ids = read("card-ids.json", {})
    newcards = read("newcards.json", {}).get("cards", []) + read("legends.json", {}).get("cards", [])
    players = {}
    for key in top:
        e = dict(prev.get(str(key), {}))
        item = item_for(key, card_ids, newcards)
        c = mk.info.get(item or -1, {})
        e.setdefault("name", c.get("name") or "Card")
        e.setdefault("ovr", c.get("ovr"))
        e.setdefault("version", "" if key < 1000000000 else (c.get("version") or ""))
        p = mk.prices.get(item) if item else None
        if p and mk.fresh:
            if e.get("price") != p:
                e["prev"] = e.get("price")
            hist = e.get("hist") or []
            if not hist or t - (parse(hist[-1][0]) or t) >= timedelta(minutes=55):
                hist.append([iso(mk.published), p])
            e.update({"price": p, "at": iso(mk.published), "src": "FUT.GG", "eaId": item, "priceState": 0, "hist": hist[-48:]})
        if e.get("price"):
            players[str(key)] = e
    if players and players != prev:
        write("prices.json", {"updatedAt": iso(t), "source": "FUT.GG", "players": players})


def update_top(mk, t):
    old = read("topprices.json", {"players": {}})
    prev = old.get("players", {})
    targets = {i: c for i, c in mk.info.items() if c.get("base") and (c.get("ovr") or 0) >= 84}
    players = {}
    for i, c in targets.items():
        e = dict(prev.get(str(i), {"name": c["name"], "ovr": c["ovr"]}))
        p = mk.prices.get(i)
        if p and mk.fresh and e.get("price") != p:
            e.update({"prev": e.get("price"), "price": p, "at": iso(mk.published), "src": "FUT.GG", "eaId": i, "priceState": 0})
        if e.get("price"):
            players[str(i)] = e
    if players != prev:
        write("topprices.json", {"updatedAt": iso(t), "source": "FUT.GG", "minOvr": 84, "players": players})


# ---------------------------------------------------------------- keeping the desk's own calls

BACKUP = ".cache/desk-ledger.json"  # Actions cache, not git


def restore_own_calls(ledger):
    """Put back the desk's graded calls, open calls, lessons and drop log if another writer replaced
    data/ledger.json. The lifetime totals aren't copied: tally() rebuilds them from the graded store."""
    saved = read(BACKUP, {})
    if not isinstance(ledger.get("graded"), dict):
        ledger["graded"] = {}
    before = len(ledger["graded"])
    merge_graded(ledger["graded"], saved.get("graded"))
    merge_graded(ledger["graded"], {c["id"]: {k: c.get(k) for k in GRADED_FIELDS} for c in saved.get("calls", [])
                                    if c.get("id") and c.get("status") in ("hit", "miss")})
    if len(ledger["graded"]) > before:
        print(f"desk: restored {len(ledger['graded']) - before} graded calls from the backup")
    if saved.get("dropLog") and len(saved["dropLog"]) > len(ledger.get("dropLog") or []):
        ledger["dropLog"] = saved["dropLog"]
        print("desk: restored dropLog from the backup")
    have = {c.get("id") for c in ledger.get("calls", [])}
    lost = [c for c in saved.get("calls", []) if c.get("strategy") and c.get("id") not in have]
    if lost:
        ids = {c["id"] for c in lost}
        ledger.setdefault("calls", []).extend(lost)
        ledger["calls"].sort(key=lambda c: c.get("madeAt") or "")
        texts = {l.get("text") for l in ledger.setdefault("lessons", [])}
        ledger["lessons"] += [l for l in saved.get("lessons", []) if l.get("callId") in ids and l.get("text") not in texts]
        print(f"desk: restored {len(lost)} of its own calls")
    settle_known_calls(ledger)


def backup_own_calls(ledger):
    try:
        (DATA / ".cache").mkdir(parents=True, exist_ok=True)
        (DATA / BACKUP).write_text(json.dumps(ledger, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- paper test

def paper_test(mk, ledger, t):
    """Re-test the price-move and weekend strategies on the recorded prices (scripts/backtest.py). Keeps the last
    result for up to a day when this run has no price history (the workflow skips it if it can't be restored)."""
    import backtest
    try:
        series = backtest.load(DATA / "price-history")
        result = backtest.summary(backtest.paper_calls(series, mk.info, t, (phase, next_weekday, UK))) if series else {}
    except Exception as error:  # a broken test must never stop the desk
        print(f"desk: paper test failed: {error}")
        result = {}
    old = ledger.get("backtest") or {}
    if result:
        ledger["backtest"] = {"at": iso(t), "strategies": result}
    elif not (parse(old.get("at")) and t - parse(old["at"]) <= timedelta(days=1)):
        ledger.pop("backtest", None)
    return ledger.get("backtest")


# ---------------------------------------------------------------- main

def main():
    t = now_utc()
    mk = Market(t)
    if not mk.prices:
        print("desk: no live price feed, nothing written")
        return
    prev = read("snapshot.json", {})
    ledger = read("ledger.json", {"calls": [], "lessons": []})
    restore_own_calls(ledger)
    graded = grade(mk, ledger, t)
    paper_test(mk, ledger, t)
    log = drop_log(ledger, t)
    new_call = make_calls(mk, ledger, t)
    tally(ledger)
    ledger["strategyBoard"] = strategy_board(ledger, t)
    ph = phase(t)
    board = fodder_board(mk) or prev.get("fodder", [])
    sbcs, sbcs_live = sbc_list(t)
    fallers, risers = movers(mk)
    if not mk.day_ago:  # no day-old price snapshot in this run's cache: keep the last movers for a few hours
        fresh = parse(prev.get("updatedAt")) and t - parse(prev["updatedAt"]) <= timedelta(hours=6)
        fallers, risers = (prev.get("fallers", []), prev.get("risers", [])) if fresh else ([], [])

    open_calls = sorted((c for c in ledger["calls"] if c.get("status") == "open" and c.get("strategy")), key=lambda c: c["madeAt"], reverse=True)[:2]
    moves = [call_move(mk, c) for c in open_calls]
    moves.append(cycle_move(t, ph))
    fm = fodder_move(board)
    if fm:
        moves.append(fm)
    if fallers:
        moves.append({"tone": "watch", "confidence": "low", "when": "Next few updates",
                      "title": f"{fallers[0]['name']} and other {('falling ' if len(fallers) > 1 else '')}cards: wait for the fall to flatten",
                      "detail": "Biggest falls in the last day: " + "; ".join(f"{f['name']} {f['ovr']} {f['version']} {f['pct']:.1f}%".replace("  ", " ") for f in fallers[:4])
                      + ". Buy only cards you will play, and wait for two steady updates before buying."})
    ending = [s for s in sbcs_live if parse(s.get("endTime")) and parse(s["endTime"]) - t <= timedelta(hours=24) and s.get("category") in (1, 2)]
    if ending and len(moves) < 6:
        s = ending[0]
        moves.append({"tone": "watch", "confidence": "medium", "when": f"Until {tok(parse(s['endTime']))}",
                      "title": f"{s['name']} SBC ends soon",
                      "detail": f"It costs about {short(s['cost'])} coins to complete. Compare that with what you get before you build." if s.get("cost") else "Compare its cost with what you get before you build."})
    moves = moves[:6]

    m = mk.market
    snap = {
        "updatedAt": iso(t), "source": "automatic", "platform": "console",
        "verdict": verdict(mk, ph),
        "index": {"idx100": m.get("idx100"), "idx100Chg": m.get("idx100Chg"), "momentum": m.get("momentum"), "momentumLabel": m.get("momentumLabel"),
                  "idx84": None, "idx85": None, "idx86": None, "icons": m.get("icons"),
                  "note": f"Ezzcoins' own index from live console prices, read at {tok(parse(m.get('at')) or t)}."},
        "fodder": board, "moves": moves, "sbcs": sbcs, "drops": drops(prev, t), "fallers": fallers, "risers": risers,
        "meta": meta_cards(mk) or prev.get("meta", []), "news": news_items(mk, sbcs_live, fallers, risers, board, t),
        "events": events(prev, t), "corrections": prev.get("corrections", [])[:15], "sources": SITE_SOURCES,
        "dailyDrop": daily_drop(log, t),
        "pricesUpdatedAt": iso(mk.published) if mk.published else prev.get("pricesUpdatedAt"),
    }
    write("snapshot.json", strip_name(snap))
    write("ledger.json", strip_name(ledger))
    backup_own_calls(ledger)

    hist = read("history.json", {"points": []})
    pts = hist.get("points", [])
    last = parse(pts[-1]["t"]) if pts else None
    if (not last or t - last >= timedelta(minutes=10)) and m.get("floor84"):
        pts.append({"t": iso(t), "f84": m.get("floor84"), "f85": m.get("floor85"), "f86": m.get("floor86"), "i100": m.get("idx100")})
        write("history.json", {"points": pts[-KEEP_POINTS:]})

    update_watched(mk, t)
    update_top(mk, t)
    print(f"desk: {phase(t)} · verdict {snap['verdict']['tone']} · {len(moves)} moves · {len(sbcs)} SBCs · "
          f"graded {len(graded)} · new call: {new_call['title'] if new_call else 'none'} · {len(log)} drops measured · "
          f"feed {'fresh' if mk.fresh else 'stale'}")


if __name__ == "__main__":
    main()
