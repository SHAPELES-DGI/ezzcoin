#!/usr/bin/env python3
"""Cache rendered FC 27 card artwork URLs from the matching FUT.GG card pages."""
import concurrent.futures, html, json, os, re, sys, unicodedata, urllib.request
from html.parser import HTMLParser
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PATH = os.path.join(ROOT, "data", "card-art.json")
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
class PlayStyleParser(HTMLParser):
    """Read active regular PlayStyles from the server-rendered FUT.GG card section."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    def __init__(self):
        super().__init__()
        self.depth = None
        self.names = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.depth is None:
            if attrs.get("id") == "playstyles":
                self.depth = 0
            return
        title = attrs.get("title")
        if title and title not in self.names:
            self.names.append(title)
        if tag not in self.VOID:
            self.depth += 1
    def handle_startendtag(self, tag, attrs):
        if self.depth is None:
            return
        title = dict(attrs).get("title")
        if title and title not in self.names:
            self.names.append(title)
    def handle_endtag(self, tag):
        if self.depth is None:
            return
        if self.depth == 0:
            self.depth = None
        elif tag not in self.VOID:
            self.depth -= 1


def fetch(entry):
    item, (player, name) = entry
    url = "https://www.fut.gg/players/%d-%s/27-%s/" % (player, slug(name), item)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Ezzcoins/1.0)"})
        with urllib.request.urlopen(request, timeout=15) as response:
            source = response.read().decode("utf-8", "ignore")
        pattern = r'https?://game-assets[.]fut[.]gg/[^\s<>]*?/2027/player-item/27-' + re.escape(item) + r'[.][a-f0-9]{32,}[.]webp'
        match = re.search(pattern, source)
        parser = PlayStyleParser()
        parser.feed(source)
        allowed = {
            "Finesse Shot", "Chip Shot", "Power Shot", "Dead Ball", "Precision Header", "Acrobatic", "Low Driven",
            "Gamechanger", "Incisive Pass", "Pinged Pass", "Long Ball", "Tiki Taka", "Whipped Pass", "Inventive",
            "Jockey", "Block", "Intercept", "Anticipate", "Slide Tackle", "Aerial Fortress", "Technical", "Rapid",
            "First Touch", "Trickster", "Press Proven", "Quick Step", "Relentless", "Long Throw", "Bruiser", "Enforcer",
            "Far Throw", "Footwork", "Cross Claimer", "1v1 Close Down", "Far Reach", "Deflector"
        }
        styles = [name for name in parser.names if name in allowed]
        return item, html.unescape(match.group(0)).replace("&amp;", "&") if match else None, styles
    except Exception:
        return item, None, None
os.makedirs(os.path.dirname(PATH), exist_ok=True)
try:
    cached = json.load(open(PATH, encoding="utf-8"))
except (OSError, ValueError):
    cached = {}
try:
    playstyles = json.load(open(os.path.join(ROOT, "data", "playstyles.json"), encoding="utf-8"))
except (OSError, ValueError):
    playstyles = {}
todo = [(item, info) for item, info in candidates().items() if item not in cached or item not in playstyles]
if todo:
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for item, url, styles in pool.map(fetch, todo):
            if url:
                cached[item] = url
            if styles:
                playstyles[str(item)] = ", ".join(styles)
os.makedirs(os.path.dirname(PATH), exist_ok=True)
with open(PATH, "w", encoding="utf-8") as fh:
    json.dump(cached, fh, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(ROOT, "data", "playstyles.json"), "w", encoding="utf-8") as fh:
    json.dump(playstyles, fh, ensure_ascii=False, separators=(",", ":"))
print("Cached FUT.GG artwork for %d cards; regular PlayStyles for %d cards (%d new lookups)." % (len(cached), len(playstyles), len(todo)))
