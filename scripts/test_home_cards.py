#!/usr/bin/env python3
"""data/home-cards.json must hold every player and card picture the home page's first screen looks up
(scripts/home_cards.py), so a first visit doesn't need the full player list or card-picture list."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home_cards  # noqa: E402

URL = "https://game-assets.fut.gg/cdn-cgi/image/quality=85,format=auto,width=300/2027/futgg-player-item-card/27-{}.ab12.webp"
files = {
    "players.json": {"cols": ["id", "name", "full", "ovr"], "rows": [[1, "Chris Mueller", "Christopher Mueller", 62],
                                                                    [2, "Other Player", "", 80], [3, "Theo Hernández", "", 82],
                                                                    [4, "Pau Cubarsí", "", 86]]},
    "card-renders.json": {str(i): {"url": URL.format(i)} for i in (1, 3, 4, 50, 70, 900)} | {"f:60": {"url": URL.format(60)}},
    "card-ids.json": {"60": 900},
    "trending.json": {"updatedAt": "2026-10-21T12:00:00Z", "cards": [
        {"name": "Chris Mueller", "ovr": 62, "eaId": 1},
        {"name": "Theo Hernandez", "ovr": 82, "eaId": 99}]},          # matched by name and rating, not by id
    "prices.json": {"players": {"4": {"name": "Pau Cubarsí"}}},
    "topprices.json": {"players": {}},
    "newcards.json": {"cards": [{"gid": 50, "eaId": 50, "baseId": 2, "name": "X"}]},
    "legends.json": {"cards": [{"gid": None, "fid": 60, "name": "Y"}]},
    "snapshot.json": {"meta": [{"eaId": 70}]},
}
with tempfile.TemporaryDirectory() as tmp:
    home_cards.DATA = Path(tmp)
    for name, value in files.items():
        (Path(tmp) / name).write_text(json.dumps(value))
    out = home_cards.build()
    ids = sorted(r[0] for r in out["rows"])
    assert ids == [1, 3, 4], ids                        # trending by id and by name, and the most watched
    assert {"1", "3", "4", "50", "70", "f:60", "900"} <= out["renders"].keys(), out["renders"].keys()
    assert "99" in out["none"] and "2" in out["none"]  # looked up, no picture: the page must not load the full list for it
    assert out["cols"] == files["players.json"]["cols"]
    home_cards.main()
    assert json.loads((Path(tmp) / "home-cards.json").read_text())["renders"] == out["renders"]
print("Home page slice: every player and card picture the first screen looks up")
