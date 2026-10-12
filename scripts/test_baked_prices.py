#!/usr/bin/env python3
"""Checks the rules for the price written into each player page's HTML."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")]
import build_pages as b  # noqa: E402

b.LIVE = {1: (700, 0), 2: (14000, 0), 3: (10500, 0), 4: (None, 1), 5: (None, 0)}
b.LIVE_OK = True
b.OLD_PRICES = {"a/": 1000, "b/": 10000, "c/": 10000}
assert b.baked_price("a/", 1) == (1000, None), "small coin moves keep the old price"
assert b.baked_price("b/", 2) == (14000, None), "big moves update the page"
assert b.baked_price("c/", 3) == (10000, None), "moves within 20% keep the old price"
assert b.baked_price("d/", 4) == (None, "SBC card · not tradeable")
assert b.baked_price("e/", 5) == (None, "No listings right now.")
assert b.baked_price("f/", 99) == (None, "No console price right now.")
b.LIVE[247090 + 50331648] = (4900, 0)
assert b.baked_price("g/", 247090) == (4900, None), "a transferred player's new base item gives his price"
assert b.baked_price("h/", 247090 + 50331648) == (4900, None)
b.LIVE_OK = False
assert b.baked_price("b/", 2) == (10000, None), "an unusable feed keeps every old price"
print("Baked page prices: thresholds, states and feed fallback pass")
