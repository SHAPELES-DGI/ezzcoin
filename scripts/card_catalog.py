"""Keep new-card records and FC 27 artwork in sync with exact EA item metadata."""
import json
from datetime import datetime, timezone


def read(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def write(path, value):
    content = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def extract(player):
    item = player["eaId"]
    name = player.get("commonName") or " ".join(filter(None, [player.get("firstName"), player.get("lastName")]))
    image = player.get("cardImageUrl") or ""
    if str(player.get("game")) != "27" or not name or not isinstance(player.get("overall"), int):
        raise ValueError("Invalid FC 27 player metadata")
    # Exact year and item ID are mandatory; never infer artwork from a name.
    if not image.startswith("https://game-assets.fut.gg/") or f"/2027/futgg-player-item-card/27-{item}." not in image:
        image = None
    return {"eaId": item, "baseId": player.get("basePlayerEaId"), "name": name,
            "version": player.get("rarityName", ""), "ovr": player["overall"],
            "pos": player.get("position", ""), "alt": ",".join(player.get("alternativePositions") or []),
            "club": (player.get("club") or {}).get("name", ""),
            "league": (player.get("league") or {}).get("name", ""),
            "nation": (player.get("nation") or {}).get("name", ""),
            "sm": player.get("skillMoves"), "wf": player.get("weakFoot"),
            "stats": [s.get("rating") for s in player.get("faceStats", [])],
            "added": (player.get("createdAt") or "")[:10], "createdAt": player.get("createdAt", ""),
            "url": "https://www.fut.gg" + player.get("url", ""), "src": "FUT.GG",
            "isIcon": bool(player.get("isIcon")), "isHero": bool(player.get("isHero")),
            "isGallery": "hall of fut" in player.get("rarityName", "").lower(),
            "cardImageUrl": image, "isSpecial": bool(player.get("isSpecial") or player.get("isIcon") or player.get("isHero") or "hall of fut" in player.get("rarityName", "").lower()),
            "excluded": bool(player.get("isEvolutionPlayerItem") or player.get("isProvisional")),
            "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "gender": 1 if player.get("gender") == 2 else 0, "foot": player.get("foot", ""),
            "height": player.get("height"), "age": player.get("age")}


def publish(data, metadata, prices, published_at, quote_metadata=None):
    catalog = read(data / "newcards.json", {"cards": []})
    ids = read(data / "card-ids.json", {})
    renders = read(data / "card-renders.json", {})
    legends = read(data / "legends.json", {"cards": []})
    cards = catalog.get("cards", [])
    # Base Icons/Heroes are not in the normal-player roster or the new-card feed.
    # Publish every verified catalogue item, even while richer metadata is pending.
    market = read(data / "market-cards.json", {"cols": [], "rows": []})
    legend_by_id = {int(c.get("eaId") or c.get("gid")): c for c in legends.get("cards", [])}
    import re
    for row in market.get("rows", []):
        item = dict(zip(market["cols"], row))
        version = item.get("version", "")
        is_icon = bool(re.search(r"\bicon\b", version, re.I) or item.get("league") == "Icons")
        is_hero = bool(re.search(r"\bhero\b", version, re.I) or item.get("league") == "Heroes")
        is_icon = is_icon and not is_hero
        is_gallery = bool(re.search(r"hall of fut|fut gallery", version, re.I))
        if not (is_icon or is_hero or is_gallery):
            continue
        key = item.pop("id")
        card = legend_by_id.setdefault(key, {"gid": key})
        card.update(metadata.get(str(key), {}))
        card.update(item, eaId=key, isIcon=is_icon, isHero=is_hero, isGallery=is_gallery, src="FUT.GG")
        ids[str(card.get("gid") or card.get("fid"))] = key
    legends["cards"] = list(legend_by_id.values())
    roster = read(data / "players.json", None)
    base_ids = {row[roster["cols"].index("id")] for row in roster["rows"]} if roster else set()
    base_added = 0
    positions_updated = 0
    base_rows = {int(row[roster["cols"].index("id")]): row for row in roster["rows"]} if roster else {}
    existing = {}
    for card in cards + legends.get("cards", []):
        key = card.get("gid") or card.get("fid")
        item = ids.get(str(key)) or card.get("eaId") or card.get("gid")
        if item:
            existing[int(item)] = card
    added = 0
    for key, record in metadata.items():
        item = int(key)
        if record.get("excluded"):
            continue
        image = record.get("cardImageUrl")
        if image:
            renders[key] = {"url": image, "name": record["name"], "ovr": record["ovr"],
                            "pos": record["pos"], "version": record["version"]}
        if not record.get("isSpecial"):
            # Exact UT item positions can exceed EA ratings-page positions.
            row = base_rows.get(item)
            if row is not None and item == record.get("baseId") and record.get("pos") == row[roster["cols"].index("pos")] and record.get("ovr") == row[roster["cols"].index("ovr")]:
                alt_index = roster["cols"].index("alt")
                if isinstance(record.get("alt"), str) and row[alt_index] != record["alt"]:
                    row[alt_index] = record["alt"]
                    positions_updated += 1
            if roster and item == record.get("baseId") and item not in base_ids and len(record.get("stats", [])) == 6:
                values = {"id": item, "name": record["name"], "q": record["name"].split()[-1],
                          "full": record["name"], "foot": "L" if record.get("foot") == "Left" else "R"}
                values.update({k: record.get(k) for k in ("ovr", "pos", "alt", "club", "league", "nation", "gender", "sm", "wf", "height", "age")})
                values.update({"s" + str(i + 1): value for i, value in enumerate(record["stats"])})
                roster["rows"].append([values.get(col, "") for col in roster["cols"]])
                base_ids.add(item)
                base_added += 1
            continue
        card = existing.get(item)
        if card is None:
            # A new card needs complete stats and verified artwork before publication.
            if not image or len(record.get("stats", [])) != 6 or not all(isinstance(s, int) for s in record["stats"]) or not record.get("added"):
                continue
            card = {"gid": item}
            cards.append(card)
            existing[item] = card
            added += 1
        for field in ("eaId", "baseId", "name", "version", "ovr", "pos", "alt", "club", "league", "nation", "sm", "wf", "stats", "added", "createdAt", "url", "src", "isIcon", "isHero", "isGallery", "gender", "foot"):
            if record.get(field) is not None:
                card[field] = record[field]
        # Preserve old FUTBIN keys so saved watchlist entries and existing URLs survive.
        card_key = str(card.get("gid") or card.get("fid"))
        ids[card_key] = item
    for card in cards + legends.get("cards", []):
        key = str(card.get("gid") or card.get("fid"))
        item = ids.get(key) or card.get("eaId") or card.get("gid")
        quote = prices.get(int(item)) if item else None
        if quote:
            source = (quote_metadata or {}).get(str(item), {}).get("console", {})
            card["price"] = quote[1]
            card["priceAt"] = source.get("at", published_at)
            card["priceState"] = quote[3]
            card["priceSrc"] = source.get("src", "FUT.GG")
    cards.sort(key=lambda c: (c.get("added", ""), c.get("ovr", 0), c.get("createdAt", "")), reverse=True)
    # Only change the catalog timestamp when its contents change.
    old = read(data / "newcards.json", {"cards": []})
    if cards != old.get("cards", []):
        catalog["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    catalog.update({"cards": cards, "automatic": True, "discoverySource": "FUT.GG FC 27 item index"})
    legends.update(automatic=True, source="FUT.GG FC 27 item catalogue")
    write(data / "legends.json", legends)
    write(data / "newcards.json", catalog)
    write(data / "card-ids.json", ids)
    write(data / "card-renders.json", renders)
    if base_added or positions_updated:
        roster["count"] = len(roster["rows"])
        roster["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        roster["discoverySource"] = "FUT.GG FC 27 item index"
        write(data / "players.json", roster)
    return added
