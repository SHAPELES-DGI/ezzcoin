#!/usr/bin/env python3
"""Checks the weekly recap's week bounds, glitch-proof movers and written summary."""
import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk  # noqa: E402
import weekly_recap as wr  # noqa: E402

# Weeks run Monday to Sunday in UK time, across the October clock change.
a, b = wr.bounds(date(2026, 10, 19))
assert a == datetime(2026, 10, 18, 23, 0, tzinfo=timezone.utc) and b == datetime(2026, 10, 26, 0, 0, tzinfo=timezone.utc), (a, b)
assert wr.label(date(2026, 10, 12)) == "12–18 October 2026" and wr.label(date(2026, 10, 26)) == "26 October–1 November 2026"
assert wr.week_start(date(2026, 10, 18)) == date(2026, 10, 12)

# Movers: the first and last three readings must agree, so a one-off mispriced listing is ignored.
a, b = wr.bounds(date(2026, 10, 12))
hours = lambda start, prices: [[int((start + timedelta(hours=i)).timestamp()), p] for i, p in enumerate(prices)]
items = {
    "1": {"console": hours(a + timedelta(hours=2), [20000, 20500, 20000]) + hours(b - timedelta(hours=4), [24000, 24500, 24000])},   # +20%
    "2": {"console": hours(a + timedelta(hours=2), [10000, 650, 700]) + hours(b - timedelta(hours=4), [700, 650, 700])},           # glitch at the start
    "3": {"console": hours(a + timedelta(hours=2), [50000, 50000, 50000]) + hours(b - timedelta(hours=4), [40000, 40000, 40500])}, # -20%
    "4": {"console": hours(a + timedelta(hours=2), [5000, 5000, 5000]) + hours(b - timedelta(hours=4), [9000, 9000, 9000])},       # too cheap
}
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp) / "price-history"
    folder.mkdir()
    (folder / "00.json").write_text(json.dumps({"items": items}))
    old = desk.DATA
    desk.DATA = Path(tmp)
    try:
        rise, fall = wr.movers(a, b, {1: {}, 2: {}, 3: {}, 4: {}})
    finally:
        desk.DATA = old
assert [r[1] for r in rise] == [1] and rise[0][0] == 20.0, rise
assert [r[1] for r in fall] == [3] and fall[0][0] == -20.0, fall

# The summary is written from the numbers.
d = {"partial": False, "floors": {"f84": (700, 900, 28.6), "f85": (1800, 2500, 38.9), "f86": (4800, 5000, 4.2), "i100": (100, 99.8, -0.2)},
     "rise": rise, "fall": fall, "info": {1: {"name": "Alpha", "ovr": 85}, 3: {"name": "Beta", "ovr": 88}},
     "new": [("Future Stars", 4, [])], "calls": [{"status": "hit"}, {"status": "miss"}, {"status": "hit"}],
     "drops": [{"chg": {"f84": 5.0, "f85": 2.0}}, {"chg": {"f84": -3.0}}]}
text = " ".join(wr.summary(d))
for part in ("SBC fodder got dearer: 84s 700 → 900", "barely moved (-0.2%)", "Alpha 85 rose the most (+20.0%)", "Beta 88 fell the most (-20.0%)",
             "4 new special cards arrived, mostly Future Stars", "2 of the 3 trade calls graded this week hit", "Fodder rose after 1 of 2 evening drops"):
    assert part in text, (part, text)
print("Weekly recap: week bounds, glitch-proof movers and summary pass")
