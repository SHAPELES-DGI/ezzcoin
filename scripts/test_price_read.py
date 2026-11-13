"""Tests for scripts/price_read.py: glitches, enough data, tax, time-of-day patterns, trend and the file format."""
import json
import math
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import price_read as pr  # noqa: E402

UK = ZoneInfo("Europe/London")
NOW = int(datetime(2026, 11, 13, 9, 0, tzinfo=UK).timestamp())


def hourly(price_at, hours=7 * 24):
    """One price per hour for the last `hours` hours: price_at(timestamp) -> price."""
    return [[NOW - h * 3600, price_at(NOW - h * 3600)] for h in range(hours, 0, -1)]


class PriceReadTests(unittest.TestCase):
    def test_lone_glitch_dropped_real_move_kept(self):
        pts = [(i, 1000) for i in range(10)] + [(10, 5000)] + [(i, 1000) for i in range(11, 20)]
        self.assertNotIn((10, 5000), pr.clean(pts))
        shift = [(i, 1000) for i in range(10)] + [(i, 2000) for i in range(10, 20)]
        self.assertEqual(pr.clean(shift), shift)          # a real jump to a new level stays
        newest = [(i, 1000) for i in range(10)] + [(10, 2000)]
        self.assertNotIn((10, 2000), pr.clean(newest))     # unconfirmed newest price is left out

    def test_needs_enough_recorded_prices(self):
        self.assertIsNone(pr.read_platform(hourly(lambda t: 1000, hours=30), NOW))
        self.assertIsNotNone(pr.read_platform(hourly(lambda t: 1000), NOW))

    def test_tax_and_ladder(self):
        self.assertEqual(pr.tax_flip(10000, 11000), math.floor(11000 * 0.95) - 10000)   # 450
        self.assertLess(pr.tax_flip(1000, 1050), 0)                                      # a 5% rise loses to the tax
        self.assertEqual(pr.ladder(163_412), 163_000)
        self.assertEqual(pr.ladder(12_380), 12_500)

    def test_evening_dip_is_found(self):
        dip = lambda t: 9000 if datetime.fromtimestamp(t, UK).hour in (19, 20, 21) else 10000
        r = pr.read_platform(hourly(dip), NOW)
        self.assertIsNotNone(r["cheap"])
        self.assertIn(r["cheap"][0], (19, 20, 21))
        self.assertGreaterEqual(r["cheap"][1], 0.7 * r["cheap"][2])
        self.assertEqual((r["lo"], r["hi"]), (9000, 10000))
        self.assertEqual(r["flip"], pr.tax_flip(r["p10"], r["p90"]))

    def test_steady_rise_has_no_fake_cheap_hour(self):
        rise = lambda t: int(10000 * (1 + 0.3 * (t - (NOW - 7 * 86400)) / (7 * 86400)))
        r = pr.read_platform(hourly(rise), NOW)
        self.assertIsNone(r["cheap"])
        self.assertIsNone(r["dear"])
        self.assertGreater(r["trend"], 20)

    def test_flat_card(self):
        r = pr.read_platform(hourly(lambda t: 650), NOW)
        self.assertEqual((r["lo"], r["hi"], r["swing"], r["trend"]), (650, 650, 0.0, 0.0))
        self.assertIsNone(r["cheap"])
        self.assertLess(r["flip"], 0)

    def test_file_format(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "05.json").write_text(json.dumps({"items": {
                "69": {"console": hourly(lambda t: 2000), "pc": hourly(lambda t: 2500, hours=20)},
                "133": {"console": [[NOW - 3600, 900]]}}}))
            data = pr.build(folder, NOW)
            self.assertEqual(set(data["items"]), {"69"})                      # too little data: no read at all
            console, pc = data["items"]["69"]
            self.assertIsNone(pc)
            self.assertEqual(pr.unpack(console)["avg"], 2000)
            self.assertEqual(len(console), len(data["cols"]))
            self.assertEqual(data["day"], "2026-11-13")


if __name__ == "__main__":
    unittest.main()
