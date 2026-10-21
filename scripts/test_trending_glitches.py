#!/usr/bin/env python3
"""Trending must ignore one-off wrong prices from the feed (scripts/market_extras.py trending_rises).

Cases taken from what trending showed on 20-21 Oct 2026: a 90-rated card listed as +847% because one reading a day
earlier was far too low, and low-rated cards at 10,000 coins (+900%) for a single update.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import market_extras as mx  # noqa: E402

T = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
INFO = {i: {"name": str(i), "ovr": 80, "pos": "ST", "version": "Rare"} for i in range(1, 10)}


def snaps(series):
    """series: {card id: [price 26 h ago, 25 h ago, ..., 1 h ago]} -> hourly snapshots."""
    out = []
    for h in range(26, 0, -1):
        out.append({"t": mx.iso(T - timedelta(hours=h)), "p": {str(i): v[26 - h] for i, v in series.items() if v[26 - h]}})
    return out


steady = [255000] * 26
low_glitch = list(steady); low_glitch[2] = 27000          # one wrong reading 24 h ago
riser = [2000] * 12 + [6000] * 14                          # a real rise, 12 h ago, still holding
spike = [1000] * 26                                        # the current reading alone says 10,000
fresh_jump = [6000] * 25 + [6000]                          # jumps to 20,000 within the last hour
gentle = [10000] * 20 + [10600] * 6                        # +6% and holding
series = {1: steady, 2: low_glitch, 3: riser, 4: spike, 5: fresh_jump, 6: gentle}
now = {1: 256000, 2: 256000, 3: 6400, 4: 10000, 5: 20000, 6: 10600}

hours, rises = mx.trending_rises(now, snaps(series), T, INFO)
ids = [i for _, i in rises]
assert hours == 24, hours
assert 2 not in ids, rises                    # one low reading a day ago doesn't make a +847% riser
assert 4 not in ids, rises                    # a single 10,000-coin reading doesn't either
assert 5 not in ids, rises                    # a jump within the last hour waits for the next hourly reading
assert ids == [3, 6], rises                   # real, held rises still show, biggest first
assert abs(rises[0][0] - 2.2) < 1e-9 and abs(rises[1][0] - 0.06) < 1e-9, rises

# An hour later the jump has held, so it shows.
later = snaps({**series, 5: fresh_jump[1:] + [20000]})
_, rises = mx.trending_rises(now, later, T, INFO)
assert 5 in [i for _, i in rises], rises

# Cheap cards (under 5,000 coins now), unknown cards and cards with no reading a day ago never show.
_, rises = mx.trending_rises({3: 4000, 7: 9000}, snaps({3: riser, 7: [None] * 26}), T, INFO)
assert rises == [], rises

# Only an hour or two of snapshots: nothing to confirm with yet, the plain rise counts.
short = snaps(series)[-1:]
hours, rises = mx.trending_rises({6: 10600}, [{**short[0], "p": {"6": 10000}}], T, INFO)
assert hours == 1 and [i for _, i in rises] == [6], (hours, rises)
assert mx.trending_rises(now, [], T, INFO) == (None, [])

print("Trending ignores one-off wrong prices and keeps real risers")
