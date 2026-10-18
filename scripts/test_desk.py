#!/usr/bin/env python3
"""Checks the automatic desk's grading, tax maths, lessons and strategy pausing."""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk  # noqa: E402

t = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


class FakeMarket:
    fresh = True
    published = t - timedelta(minutes=5)
    prices = {1: 11000, 2: 9000}
    cheapest = {"86": [{"price": 4500}]}

    def floor(self, ovr):
        return self.cheapest[str(ovr)][0]["price"]


def call(i, rule, item, entry, strategy="rebound"):
    return {"id": f"c{i}", "madeAt": desk.iso(t - timedelta(days=2)), "title": f"Call {i}", "rule": rule, "strategy": strategy,
            "ref": {"kind": "item", "eaId": item}, "entry": entry, "entryAt": desk.iso(t - timedelta(days=2)),
            "checkAt": desk.iso(t - timedelta(minutes=10)), "status": "open"}


mk = FakeMarket()
ledger = {"calls": [call(1, "buy_after_tax", 1, 10000), call(2, "buy_after_tax", 2, 10000), call(3, "sell_lower", 2, 10000, "fade")], "lessons": []}
graded = desk.grade(mk, ledger, t)
c1, c2, c3 = ledger["calls"]
assert (c1["status"], c1["result"]) == ("hit", 4.5), c1          # floor(11000*0.95)=10450 -> +4.5%
assert (c2["status"], c2["result"]) == ("miss", -14.5), c2       # floor(9000*0.95)=8550 -> -14.5%
assert (c3["status"], c3["result"]) == ("hit", 10.0), c3         # sold 10000, now 9000 -> hit
assert len(ledger["lessons"]) == 3 and ledger["lessons"][1]["kind"] == "miss"

# Floor refs read the cheapest card at that rating.
assert desk.ref_price(mk, {"kind": "floor", "ovr": 86, "source": "Ezzcoins price feed"}) == 4500
# FUTBIN page refs can't be read automatically.
assert desk.ref_price(mk, {"kind": "player", "url": "https://www.futbin.com/27/player/1"}) is None

# Three graded calls under 50% hits pause a strategy.
calls = [dict(call(i, "buy_after_tax", 1, 1), status=s, gradedAt=desk.iso(t)) for i, s in enumerate(["miss", "miss", "hit"])]
rec = desk.strategy_record(calls)["rebound"]
assert (rec["hit"], rec["miss"]) == (1, 2)

# Weekly cycle in UK time.
assert desk.phase(datetime(2026, 10, 15, 8, 30, tzinfo=timezone.utc)) == "rewards"     # Thu 09:30 BST
assert desk.phase(datetime(2026, 10, 16, 18, 0, tzinfo=timezone.utc)) == "weekend"     # Fri evening
assert desk.phase(datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)) == "midweek"     # Tue
assert desk.next_weekday(t, 3, 7, 59) == datetime(2026, 10, 15, 6, 59, tzinfo=timezone.utc)   # Thu 07:59 BST
assert desk.next_weekday(datetime(2026, 10, 27, tzinfo=timezone.utc), 3, 7, 59) == datetime(2026, 10, 29, 7, 59, tzinfo=timezone.utc)  # GMT
print("Desk: grading, tax, lessons, strategy record and weekly cycle pass")

# ---------------------------------------------------------------- lifetime totals and learning
# Lifetime totals count each graded call once and survive the 60-call trim.
led = {"calls": [dict(call(i, "buy_after_tax", 1, 1), status=s, result=r, tone="buy", gradedAt=desk.iso(t - timedelta(hours=10 - i)))
                 for i, (s, r) in enumerate([("hit", 6.0), ("hit", 2.0), ("miss", -20.0)])]}
desk.tally(led)
desk.tally(led)                                                     # running twice adds nothing
assert (led["record"]["hit"], led["record"]["miss"], led["record"]["sum"]) == (2, 1, -12.0), led["record"]
led["calls"] = []                                                   # trimmed: the totals remain
desk.tally(led)
s = led["strategies"]["rebound"]
assert (s["hit"], s["miss"], len(s["recent"])) == (2, 1, 3)

# 2 of 3 hits but a -4% average after tax: paused, even though the hit rate is over 50%.
st = desk.standing(s, t)
assert st["status"] == "paused" and st["confidence"] == "low" and st["avg"] == -4.0, st
# After 7 days without a graded call it gets one low-confidence retest.
assert desk.standing(s, t + timedelta(days=8))["status"] == "retest"
# 3 of 3 hits with a positive average: high confidence, ranked by expected result.
good = {"hit": 3, "miss": 0, "sum": 9.0, "recent": [["a", 3.0, True]] * 3, "last": desk.iso(t)}
g = desk.standing(good, t)
assert g["status"] == "active" and g["confidence"] == "high" and abs(g["expected"] - 1.5) < 1e-9, g
assert desk.standing(None, t)["status"] == "new" and desk.standing(None, t)["expected"] == 0
board = desk.strategy_board({"strategies": {"rebound": s, "fade": good}}, t)
assert [b["key"] for b in board][0] == "fade" and board[-1]["key"] == "rebound" and len(board) == len(desk.STRATEGIES)

# A wiped ledger gets its graded calls and drop log back from the backup, and the totals are rebuilt from them.
def g(i, status, result, strategy="fade", hours=0):
    return {"strategy": strategy, "tone": "sell", "status": status, "result": result,
            "madeAt": desk.iso(t - timedelta(days=3)), "gradedAt": desk.iso(t - timedelta(hours=hours + i))}

saved = {"graded": {f"b{i}": g(i, "hit" if i < 5 else "miss", 2.0) for i in range(7)},
         "dropLog": [{"date": "2026-10-01"}], "calls": []}
orig = desk.read
desk.read = lambda name, fb: saved if name == desk.BACKUP else orig(name, fb)
wiped = {"calls": [], "lessons": [], "record": {"hit": 1, "miss": 0}}
desk.restore_own_calls(wiped)
desk.tally(wiped)
assert (wiped["record"]["hit"], wiped["record"]["miss"]) == (5, 2) and wiped["strategies"]["fade"]["hit"] == 5, wiped["record"]
assert len(wiped["dropLog"]) == 1

# Another writer puts back an older data/ledger.json every hour: inflated totals, and a call that is
# already graded shown as open again. The call is never graded or counted twice.
done = dict(call(9, "sell_lower", 2, 10000, "fade"), status="miss", result=-12.7, exit=11270, gradedAt=desk.iso(t - timedelta(hours=1)))
saved = {"graded": {"c9": {k: done.get(k) for k in desk.GRADED_FIELDS}}, "calls": [done]}
desk.read = lambda name, fb: saved if name == desk.BACKUP else orig(name, fb)
for run in range(5):
    stale = {"calls": [dict(call(9, "sell_lower", 2, 10000, "fade"))], "lessons": [],
             "record": {"hit": 79, "miss": 142}, "strategies": {"fade": {"hit": 1, "miss": 7, "sum": -67.6, "recent": [], "last": None}}}
    desk.restore_own_calls(stale)
    newly = desk.grade(mk, stale, t)
    desk.tally(stale)
    assert newly == [] and stale["calls"][0]["status"] == "miss" and stale["calls"][0]["result"] == -12.7, stale["calls"][0]
    assert (stale["record"]["hit"], stale["record"]["miss"]) == (0, 1), stale["record"]
    assert (stale["strategies"]["fade"]["miss"], len(stale["strategies"]["fade"]["recent"])) == (1, 1)
    assert stale["lessons"] == []                                   # no second lesson for the same call
desk.read = orig

# The same call id graded twice in the store's two sources keeps its first grading.
store = {"x": {"status": "miss", "result": -14.1, "gradedAt": "2026-10-17T23:00:00Z"}}
desk.merge_graded(store, {"x": {"status": "miss", "result": -12.7, "gradedAt": "2026-10-17T23:30:00Z"}})
assert store["x"]["result"] == -14.1

# ---------------------------------------------------------------- two readings must agree
class ConfirmMarket(desk.Market):
    def __init__(self):
        self.t = t
        self.prices = {7: 8000, 8: 8000, 9: 20000}
        self.day_ago = {"p": {"7": 10000, "8": 10000, "9": 10000}}
        self.hour_ago = {"p": {"7": 8300, "8": 10000, "9": 19500}}
        self.cheapest = {"86": [{"price": 4000}]}
        self.hist = [{"t": desk.iso(t - timedelta(minutes=20)), "f86": 4100}]

cm = ConfirmMarket()
assert cm.move_confirmed(7, -20)          # fell 17% an hour ago too, and now agrees with that reading
assert not cm.move_confirmed(8, -20)      # an hour ago it hadn't moved: one reading only
assert cm.move_confirmed(9, 100) and not cm.move_confirmed(9, -10)
assert cm.steady(9) and not cm.steady(8)
assert cm.floor_steady(86)
cm.hist = [{"t": desk.iso(t - timedelta(minutes=20)), "f86": 750}]   # the post-payout dump reading
assert not cm.floor_steady(86)
cm.hist = [{"t": desk.iso(t - timedelta(hours=3)), "f86": 4000}]     # too old to confirm
assert not cm.floor_steady(86)

# ---------------------------------------------------------------- daily 6 PM drop
def pts_for(day, before, after, utc_offset):
    drop = datetime(day.year, day.month, day.day, 18 - utc_offset, tzinfo=timezone.utc)
    return [(drop - timedelta(minutes=20), {"f84": before, "f85": before, "f86": before, "i100": 100.0}),
            (drop + timedelta(minutes=125), {"f84": after, "f85": after, "f86": after, "i100": 100.0})]

from datetime import date
pts = []
for i, d in enumerate([date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8), date(2026, 10, 12), date(2026, 10, 13)]):
    pts += pts_for(d, 1000, 1100 if i != 3 else 1000, 1)                   # BST: 6 PM UK is 17:00 UTC
lg = {}
log = desk.drop_log(lg, datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc), pts)
assert [d["date"] for d in log] == ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-12", "2026-10-13"], log
assert log[0]["chg"]["f85"] == 10.0 and "i100" not in log[0]["chg"]      # a flat index reading is stale, not a move
assert desk.drop_log(lg, datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc), pts) == log   # recorded once
# Tonight's drop isn't recorded until 9 PM UK, when the 8 PM reading exists.
assert len(desk.drop_log({}, datetime(2026, 10, 13, 18, 30, tzinfo=timezone.utc), pts)) == 5
# GMT after the clocks change: 6 PM UK is 18:00 UTC.
gmt = desk.drop_log({}, datetime(2026, 10, 27, 22, 0, tzinfo=timezone.utc), pts_for(date(2026, 10, 27), 1000, 1050, 0))
assert gmt and gmt[0]["chg"]["f84"] == 5.0

st = desk.drop_stats(log, False, ("f84", "f85", "f86"))
assert (st["n"], st["up"], st["down"]) == (6, 5, 0) and st["avg"] == 8.3, st
adv = desk.drop_advice(st, "Fodder", datetime(2026, 10, 14, 17, 0, tzinfo=timezone.utc))
assert adv["tone"] == "buy" and "beats the 5% tax" in adv["text"] and "{{t:" in adv["text"], adv
assert desk.drop_advice({"n": 2, "avg": 9.0, "up": 2, "down": 0}, "Fodder", t)["tone"] == "watch"
assert desk.drop_stats(log, True, ("f84",))["n"] == 0                     # Fridays are measured apart

# The drop strategy: 85s rose after 5 of 6 weekday drops by 8.3% on average, so it is offered 1 hour before 6 PM.
dm = ConfirmMarket()
dm.t = datetime(2026, 10, 14, 16, 0, tzinfo=timezone.utc)                  # Wed 5 PM BST
dm.cheapest = {"84": [{"price": 1000}], "85": [{"price": 1000}], "86": [{"price": 1000}]}
dm.hist = [{"t": desk.iso(dm.t - timedelta(minutes=15)), "f84": 1000, "f85": 1000, "f86": 1000}]
dm.prices, dm.info, dm.day_ago = {}, {}, None
offer = [c for c in desk.candidates(dm, dm.t, set(), log) if c[0] == "drop"]
assert offer and offer[0][1]["floor"] in (84, 85, 86) and offer[0][1]["checkAt"] == datetime(2026, 10, 14, 19, 0, tzinfo=timezone.utc), offer
assert not [c for c in desk.candidates(dm, dm.t, set(), log[:3]) if c[0] == "drop"]   # too few drops measured

dd = desk.daily_drop(log, datetime(2026, 10, 13, 18, 30, tzinfo=timezone.utc))
assert dd["prevAt"] == "2026-10-13T17:00:00Z" and dd["nextAt"] == "2026-10-14T17:00:00Z" and not dd["friday"]
print("Desk: lifetime totals, strategy pausing by result, two-reading checks and the 6 PM drop record pass")

