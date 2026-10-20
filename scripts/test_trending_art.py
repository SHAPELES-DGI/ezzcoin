#!/usr/bin/env python3
"""Checks that every trending card gets its exact FUT.GG card picture (scripts/market_extras.py)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import market_extras as mx  # noqa: E402


def url(item, year="2027"):
    return f"https://game-assets.fut.gg/cdn-cgi/image/quality=85,format=auto,width=300/{year}/futgg-player-item-card/27-{item}.abc123.webp"


with tempfile.TemporaryDirectory() as tmp:
    mx.DATA = Path(tmp)
    (mx.DATA / "card-renders.json").write_text(json.dumps({"100": {"url": url(100), "name": "Known", "ovr": 80, "pos": "ST", "version": "Rare"}}))
    asked = []

    def fake(ids):
        asked.append(list(ids))
        details = {
            "200": {"name": "Low Riser", "ovr": 62, "pos": "CB", "version": "Common", "cardImageUrl": url(200)},
            "300": {"name": "Wrong Item", "ovr": 65, "pos": "GK", "version": "Common", "cardImageUrl": url(999)},   # another item's picture
            "400": {"name": "Old Game", "ovr": 67, "pos": "CM", "version": "Common", "cardImageUrl": url(400, "2026")},
            "500": {"name": "Evolution", "ovr": 70, "pos": "LW", "version": "Rare", "cardImageUrl": url(500), "excluded": True},
        }
        return [], details

    added = mx.ensure_card_art([100, 200, 300, 400, 500, 600, 200, None], fetch=fake)
    renders = json.loads((mx.DATA / "card-renders.json").read_text())
    assert asked == [[200, 300, 400, 500, 600]], asked              # only cards without a picture, once each
    assert added == 1 and renders["200"]["url"] == url(200) and renders["200"]["name"] == "Low Riser", renders
    assert not {"300", "400", "500", "600"} & renders.keys()        # never someone else's, last year's or an evolution's picture
    assert list(renders) == ["100", "200"]                           # stable key order

    asked.clear()
    assert mx.ensure_card_art([100, 200], fetch=fake) == 0 and asked == []   # nothing missing: no request at all

    def down(ids):
        raise RuntimeError("FC 27 metadata request failed: 403")
    before = (mx.DATA / "card-renders.json").read_text()
    assert mx.ensure_card_art([700], fetch=down) == 0                 # FUT.GG unreachable: the update carries on
    assert (mx.DATA / "card-renders.json").read_text() == before

print("Trending artwork: missing pictures fetched once, exact-item check, no request when complete, failures ignored pass")
