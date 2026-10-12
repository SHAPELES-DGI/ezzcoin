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
