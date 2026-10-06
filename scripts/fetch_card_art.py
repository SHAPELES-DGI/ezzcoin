#!/usr/bin/env python3
"""Cache rendered FC 27 card artwork URLs from the matching FUT.GG card pages."""
import concurrent.futures, html, json, os, re, sys, unicodedata, urllib.request
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PATH = os.path.join(ROOT, "data", "card-art.json")
FULL_PATH = os.path.join(ROOT, "data", "full-card-art.json")
MAP = {"ø":"o","Ø":"o","ß":"ss","ł":"l","Ł":"l","æ":"ae","Æ":"ae","œ":"oe","đ":"d","Đ":"d","ı":"i","ð":"d","þ":"th"}
def slug(value):
    value = "".join(MAP.get(ch, ch) for ch in str(value or "")).lower()
    value = "".join(ch for ch in unicodedata.normalize("NFD", value) if not unicodedata.category(ch).startswith("M"))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "player"
def candidates():
    out = {}
    with open(os.path.join(ROOT, "data", "players.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    cols = {name: i for i, name in enumerate(data["cols"])}
    for row in data["rows"]:
        try:
            pid, ovr, name = int(row[cols["id"]]), int(row[cols["ovr"]] or 0), row[cols["name"]]
        except (KeyError, TypeError, ValueError):
            continue
        if ovr >= 80 and name:
            out[str(pid)] = (pid, name)
    for filename in ("newcards.json", "legends.json"):
        path = os.path.join(ROOT, "data", filename)
        if not os.path.exists(path):
            continue
        try:
            cards = json.load(open(path, encoding="utf-8")).get("cards") or []
        except (OSError, ValueError, AttributeError):
            continue
        for card in cards:
            item = card.get("gid") or card.get("fid")
            player = card.get("baseId")
            name = card.get("name")
            try:
                item, player = int(item), int(player)
            except (TypeError, ValueError):
                continue
            if name and int(card.get("ovr") or 0) >= 80:
                out[str(item)] = (player, name)
    return out
def fetch(entry):
    item, (player, name) = entry
    url = "https://www.fut.gg/players/%d-%s/27-%s/" % (player, slug(name), item)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Ezzcoins/1.0)"})
        with urllib.request.urlopen(request, timeout=15) as response:
            source = response.read().decode("utf-8", "ignore")
        pattern = r'https?://game-assets[.]fut[.]gg/[^\s<>"]+[.]webp'
        match = re.search(r'https?://game-assets[.]fut[.]gg/[^\s<>]*?/2027/player-item/27-' + re.escape(item) + r'[.][a-f0-9]{32,}[.]webp', source)
        player_image = html.unescape(match.group(0)).replace("&amp;", "&") if match else None

        # FUT.GG exposes a separate downloadable EA FC Item asset with the game card frame.
        full_card = None
        assets_url = url.rstrip("/") + "/assets/"
        assets_req = urllib.request.Request(assets_url, headers={"User-Agent": "Mozilla/5.0 (compatible; Ezzcoins/1.0)"})
        with urllib.request.urlopen(assets_req, timeout=15) as response:
            assets_source = response.read().decode("utf-8", "ignore")
        start = assets_source.lower().rfind("ea fc item")
        stop = assets_source.lower().find("futgg item", start + 1) if start >= 0 else -1
        section = assets_source[start:stop if stop > start else start + 12000] if start >= 0 else ""
        urls = re.findall(pattern, section)
        if item == "50570733":
            print("CARD_ASSET_DEBUG marker=%d stop=%d section=%s urls=%s" % (start, stop, section[:2500], urls[:5]))
        if urls:
            urls.sort(key=lambda u: ("width=" in u or "quality=" in u, len(u)), reverse=True)
            full_card = html.unescape(urls[0]).replace("&amp;", "&")
        return item, player_image, full_card
    except Exception as error:
        if item == "50570733":
            print("CARD_ASSET_ERROR", repr(error))
        return item, None, None
os.makedirs(os.path.dirname(PATH), exist_ok=True)
try:
    cached = json.load(open(PATH, encoding="utf-8"))
except (OSError, ValueError):
    cached = {}
try:
    full_cached = json.load(open(FULL_PATH, encoding="utf-8"))
except (OSError, ValueError):
    full_cached = {}
all_candidates = candidates()
todo = [(item, info) for item, info in all_candidates.items() if item not in cached or item not in full_cached]
if todo:
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for item, player_url, full_url in pool.map(fetch, todo):
            if player_url:
                cached[item] = player_url
            if full_url:
                full_cached[item] = full_url
with open(PATH, "w", encoding="utf-8") as fh:
    json.dump(cached, fh, ensure_ascii=False, separators=(",", ":"))
with open(FULL_PATH, "w", encoding="utf-8") as fh:
    json.dump(full_cached, fh, ensure_ascii=False, separators=(",", ":"))
sample = next(iter(full_cached.items()), ("", ""))
print("Cached FUT.GG player images for %d cards (%d new lookups)." % (len(cached), len(todo)))
print("Cached %d full EA FC Item card images; sample %s=%s" % (len(full_cached), sample[0], sample[1]))