#!/usr/bin/env python3
"""Fetch freely licensed player photos from Wikimedia Commons for Ezzcoins player pages.

For every player rated MIN_OVR+ in data/players.json, the base player of every new special card in
data/newcards.json (when it is surely the same person), and every Icon and Hero in data/legends.json whose full name
is known (saved under the card's own id, 1000000000 + FUT.GG or FUTBIN card id), it looks for the player's Wikidata item,
takes the item's main image (P18), checks the file's licence on Commons (public domain, CC0,
CC BY or CC BY-SA only), downloads a 360 px thumbnail to photos/<EA id>.<ext> and records the
credit in photos/credits.json. Items are found by EA id (P1469) or by name (English label or alias).
Wrong-person matches are avoided: a name match must be a single footballer, or a single one once
club, nationality and birth year are compared. photos/report.json lists why a
player rated 85+ (or a new card's base player) still has no photo.

Usage: python3 scripts/fetch_photos.py [site root]   (standard library only; runs on GitHub)
"""
import html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MIN_OVR = 80
SPECIAL = 1000000000  # Icons and Heroes are keyed SPECIAL + FUTBIN id, like special cards on the site
WIDTH = 360
UA = "EzzcoinsPhotoBot/1.0 (https://shapeles-dgi.github.io/ezzcoin/; https://github.com/SHAPELES-DGI/ezzcoin)"
SPARQL = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"
OK_LICENCE = re.compile(r"^(cc0( 1\.0)?|public domain|pd[- ].*|cc[- ]by(-sa)?[- ]\d\.\d( [a-z-]+)?|cc[- ]by(-sa)?[- ]\d\.\d)$", re.I)
SLUG_MAP = {"ø": "o", "Ø": "o", "ß": "ss", "ł": "l", "Ł": "l", "æ": "ae", "Æ": "ae",
            "œ": "oe", "đ": "d", "Đ": "d", "ı": "i", "ð": "d", "þ": "th"}


def norm(s):
    s = "".join(SLUG_MAP.get(ch, ch) for ch in str(s or "")).lower()
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.category(ch).startswith("M"))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def http(url, data=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # rate limit or network hiccup
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"request failed: {url[:120]} ({last})")


def sparql(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    return json.loads(http(SPARQL, body))["results"]["bindings"]


def lit(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def file_of(uri):
    return urllib.parse.unquote(uri.rsplit("/", 1)[-1]).replace("_", " ")


def tokens(x):
    """Name parts that should appear in the photo's file name (4+ letters)."""
    return {t for t in norm(x["n"] + " " + x["f"]).split() if len(t) >= 4}


def by_id(players):
    """Wikidata items whose 'FIFA player ID' (P1469, the EA/SoFIFA id) equals the EA id."""
    out = {}
    ids = [str(x["id"]) for x in players if x["id"] < SPECIAL]  # EA ids only
    for i in range(0, len(ids), 150):
        q = ("SELECT ?id ?image WHERE { VALUES ?id { " + " ".join(lit(v) for v in ids[i:i + 150]) + " } "
             "?item wdt:P1469 ?id; wdt:P18 ?image. }")
        for b in sparql(q):
            out.setdefault(int(b["id"]["value"]), set()).add(file_of(b["image"]["value"]))
        time.sleep(1)
    return out


COUNTRY_ALIASES = {"korea republic": "south korea", "korea dpr": "north korea", "usa": "united states",
                   "united states of america": "united states", "holland": "netherlands", "kingdom of the netherlands": "netherlands",
                   "cote d ivoire": "ivory coast", "turkiye": "turkey", "china pr": "people s republic of china",
                   "republic of ireland": "ireland", "czechia": "czech republic", "cabo verde": "cape verde",
                   "congo dr": "democratic republic of the congo", "dr congo": "democratic republic of the congo",
                   "bosnia herzegovina": "bosnia and herzegovina", "north macedonia": "north macedonia"}
SEASON_YEAR = 2026


def country_key(s):
    k = norm(s)
    return COUNTRY_ALIASES.get(k, k)


CLUB_NOISE = {"fc", "cf", "ac", "sc", "afc", "sv", "ss", "as", "us", "rc", "cd", "ud", "sd", "club", "de", "the", "football", "futbol",
              "calcio", "women", "ladies", "w", "fk", "nk", "sk", "if", "bk", "and", "city", "united"}


def club_words(s):
    """Distinctive words of a club name ("FC Barcelona" -> {"barcelona"}), for comparing EA and Wikidata names."""
    return frozenset(w for w in norm(s).split() if len(w) > 2 and w not in CLUB_NOISE)


def by_name(players):
    """Footballers whose English label or alias equals the player's name or full name. Kept when exactly one
    footballer matches, or exactly one is left after comparing birth year (from the player's age) and nationality."""
    names = {}
    for x in players:
        for n in {x["f"], x["n"]} - {""}:
            names.setdefault(n, set()).add(x["id"])
    keys = [n for n, v in names.items() if len(v) == 1]
    items = {}  # item uri -> {"files", "years", "countries", "labels"}
    for i in range(0, len(keys), 60):
        q = ("SELECT ?label ?item (GROUP_CONCAT(DISTINCT STR(?image); separator=\"|\") AS ?imgs) "
             "(GROUP_CONCAT(DISTINCT STR(YEAR(?dob)); separator=\"|\") AS ?ys) (GROUP_CONCAT(DISTINCT ?cl; separator=\"|\") AS ?cls) "
             "(GROUP_CONCAT(DISTINCT ?tl; separator=\"|\") AS ?tls) WHERE { VALUES ?label { " + " ".join(lit(n) + "@en" for n in keys[i:i + 60]) + " } "
             "?item rdfs:label|skos:altLabel ?label; wdt:P106 wd:Q937857; wdt:P18 ?image. "
             "OPTIONAL { ?item wdt:P569 ?dob } OPTIONAL { ?item wdt:P27 ?c . ?c rdfs:label ?cl FILTER(LANG(?cl) = \"en\") } "
             "OPTIONAL { ?item wdt:P54 ?t . ?t rdfs:label ?tl FILTER(LANG(?tl) = \"en\") } } GROUP BY ?label ?item")
        try:
            rows = sparql(q)
        except RuntimeError as e:  # one slow batch shouldn't stop the whole job
            print("by_name batch skipped:", e)
            continue
        parts = lambda b, k: [v for v in (b.get(k, {}).get("value") or "").split("|") if v]
        for b in rows:
            it = items.setdefault(b["item"]["value"], {"files": set(), "years": set(), "countries": set(), "teams": set(), "labels": set()})
            it["files"].update(file_of(v) for v in parts(b, "imgs"))
            it["labels"].add(b["label"]["value"])
            it["years"].update(int(v) for v in parts(b, "ys") if v.isdigit())
            it["countries"].update(country_key(v) for v in parts(b, "cls"))
            it["teams"].update(club_words(v) for v in parts(b, "tls"))
        time.sleep(1)
    by_label = {}
    for uri, it in items.items():
        for lab in it["labels"]:
            by_label.setdefault(lab, set()).add(uri)
    out, why = {}, {}
    for x in players:
        cands = set()
        for n in {x["f"], x["n"]} - {""}:
            if len(names.get(n, ())) == 1:
                cands |= by_label.get(n, set())
        if not cands:
            why[x["id"]] = "no Wikidata footballer with this name and a photo"
            continue
        if len(cands) > 1 and x.get("club"):
            mine = club_words(x["club"])
            same = {u for u in cands if mine and any(mine & t for t in items[u]["teams"])}
            if same:
                cands = same
        if len(cands) > 1 and x.get("age"):
            want = SEASON_YEAR - int(x["age"])
            near = {u for u in cands if any(abs(y - want) <= 1 for y in items[u]["years"])}
            if near:
                cands = near
        if len(cands) > 1 and x.get("nat"):
            same = {u for u in cands if country_key(x["nat"]) in items[u]["countries"]}
            if same:
                cands = same
        if len(cands) == 1:
            out[x["id"]] = items[next(iter(cands))]["files"]
        else:
            why[x["id"]] = f"{len(cands)} footballers with this name"
    return out, why


def commons_info(files):
    info = {}
    files = sorted(files)
    for i in range(0, len(files), 40):
        params = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
                  "iiurlwidth": str(WIDTH), "titles": "|".join("File:" + f for f in files[i:i + 40])}
        d = json.loads(http(COMMONS + "?" + urllib.parse.urlencode(params)))
        norm_map = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for page in d.get("query", {}).get("pages", {}).values():
            ii = (page.get("imageinfo") or [None])[0]
            if not ii:
                continue
            title = norm_map.get(page["title"], page["title"])
            meta = ii.get("extmetadata") or {}
            val = lambda k: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", str((meta.get(k) or {}).get("value") or "")))).strip()
            info[title.split(":", 1)[1]] = {"thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "mime": ii.get("mime"),
                                             "licence": val("LicenseShortName"), "licenceUrl": val("LicenseUrl"),
                                             "author": val("Artist")[:120] or "Unknown author"}
        time.sleep(1)
    return info


def clean_author(a):
    """Drop wiki signature leftovers such as '(talk) 14:48, 25 November 2015 (UTC)'."""
    a = re.sub(r"\s*\((talk|discussion|disc|diskussion)\b.*$", "", a, flags=re.I)
    a = re.sub(r"\s*\d{1,2}:\d{2},?\s+\d{1,2}\s+\w+\s+\d{4}.*$", "", a)
    return a.strip(" ,;-") or "Unknown author"


def shrink(blob, path):
    """Save a small JPEG (320 px wide, quality 78). Falls back to the original bytes without Pillow."""
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(blob))
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (28, 35, 32))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        if im.width > 320:
            im = im.resize((320, round(im.height * 320 / im.width)), Image.LANCZOS)
        im.save(path, "JPEG", quality=78, optimize=True, progressive=True)
        return True
    except Exception:
        with open(path, "wb") as fh:
            fh.write(blob)
        return False


def new_card_bases(rows, ci):
    """EA ids of the base players of the cards in data/newcards.json: the linked id, or a name match that is surely
    the same person (same club, or the only player with that name). Same rule as scripts/build_pages.py."""
    path = os.path.join(ROOT, "data", "newcards.json")
    try:
        cards = json.load(open(path, encoding="utf-8")).get("cards") or []
    except (OSError, ValueError, AttributeError):
        return set()
    ids = {int(r[ci["id"]]) for r in rows}
    byname, byfull = {}, {}
    for r in rows:
        byname.setdefault(norm(r[ci["name"]]), []).append(r)
        if r[ci["full"]]:
            byfull.setdefault(norm(r[ci["full"]]), []).append(r)
    out = set()
    for c in cards:
        if str(c.get("baseId") or "").isdigit() and int(c["baseId"]) in ids:
            out.add(int(c["baseId"]))
            continue
        hits = byname.get(norm(c.get("name")), []) or byfull.get(norm(c.get("name")), [])
        same = [r for r in hits if c.get("club") and r[ci["club"]] == c.get("club")]
        if same:
            out.add(int(same[0][ci["id"]]))
        elif len(hits) == 1:
            out.add(int(hits[0][ci["id"]]))
    return out


def main():
    data = json.load(open(os.path.join(ROOT, "data", "players.json"), encoding="utf-8"))
    ci = {c: i for i, c in enumerate(data["cols"])}
    rows = [r for r in data["rows"] if r[ci["id"]] is not None]
    info_of = lambda r: {"id": int(r[ci["id"]]), "n": r[ci["name"]] or "", "f": r[ci["full"]] or "", "o": r[ci["ovr"]] or 0,
                         "age": r[ci["age"]] if "age" in ci else None, "nat": r[ci["nation"]] if "nation" in ci else "",
                         "club": r[ci["club"]] if "club" in ci else ""}
    players = [info_of(r) for r in rows if (r[ci["ovr"]] or 0) >= MIN_OVR]
    # Base players of new special cards (often rated below MIN_OVR), so those cards get a photo too.
    have = {x["id"] for x in players}
    for pid in new_card_bases(rows, ci):
        r = next((r for r in rows if int(r[ci["id"]]) == pid), None)
        if r and pid not in have:
            players.append(dict(info_of(r), base=True))
            have.add(pid)
    # Icons and Heroes: only once their full name is known (a short card name alone could match the wrong person).
    try:
        lcards = json.load(open(os.path.join(ROOT, "data", "legends.json"), encoding="utf-8")).get("cards") or []
    except (OSError, ValueError, AttributeError):
        lcards = []
    for c in lcards:
        try:
            pid = SPECIAL + int(c.get("gid") if c.get("gid") not in (None, "") else c.get("fid"))
        except (TypeError, ValueError):
            continue
        if c.get("full") and pid not in have:
            players.append({"id": pid, "n": c.get("name") or "", "f": c["full"], "o": c.get("ovr") or 0, "age": None,
                            "nat": c.get("nation") or "", "club": "" if str(c.get("club") or "").upper() == "ICON" else c.get("club") or "",
                            "base": True})
            have.add(pid)
    pdir = os.path.join(ROOT, "photos")
    os.makedirs(pdir, exist_ok=True)
    cpath = os.path.join(pdir, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}

    cand = by_id(players)
    named, why = by_name([x for x in players if x["id"] not in cand])
    for pid, files in named.items():
        cand.setdefault(pid, set()).update(files)
    byid = {x["id"]: x for x in players}
    # The item's main photo is that person's photo; when it has several, prefer one whose file name carries the name.
    chosen = {}
    for pid, files in cand.items():
        toks = tokens(byid[pid])
        chosen[pid] = sorted(files, key=lambda f: (not (toks & set(norm(f).split())), f))[0]
    info = commons_info(set(chosen.values()))
    added = kept = 0
    for pid, f in sorted(chosen.items()):
        meta = info.get(f)
        if not meta or not meta["thumb"]:
            why[pid] = "photo not found on Commons"
            continue
        if not OK_LICENCE.match(meta["licence"] or ""):
            why[pid] = "licence not allowed: " + (meta["licence"] or "none")
            continue
        if meta["mime"] not in ("image/jpeg", "image/png"):
            why[pid] = "not a JPEG or PNG"
            continue
        name = f"{pid}.jpg"
        old = credits.get(str(pid))
        if old and old.get("file") == f and os.path.exists(os.path.join(pdir, old.get("img", ""))):
            kept += 1
            continue
        try:
            blob = http(meta["thumb"])
        except RuntimeError:
            why[pid] = "download failed"
            continue
        if len(blob) < 2000:
            why[pid] = "download too small"
            continue
        shrink(blob, os.path.join(pdir, name))
        credits[str(pid)] = {"img": name, "file": f, "page": meta["page"], "author": clean_author(meta["author"]),
                             "licence": meta["licence"], "licenceUrl": meta["licenceUrl"]}
        added += 1
        time.sleep(0.3)
    for v in credits.values():
        v["author"] = clean_author(v.get("author", ""))
    # drop photos of players who no longer have a page
    keep = {str(x["id"]) for x in players}
    for pid in [k for k in credits if k not in keep]:
        try:
            os.remove(os.path.join(pdir, credits[pid]["img"]))
        except OSError:
            pass
        del credits[pid]
    with open(cpath, "w", encoding="utf-8") as fh:
        json.dump(credits, fh, ensure_ascii=False, indent=0, sort_keys=True)
    # Why the players people look for most still have no photo (rated 85+, or the base of a new card).
    missing = {}
    for x in players:
        if str(x["id"]) in credits or not ((x.get("o") or 0) >= 85 or x.get("base")):
            continue
        missing[str(x["id"])] = {"name": x["f"] or x["n"], "ovr": x.get("o"), "why": why.get(x["id"], "no Wikidata item with this EA id or name")}
    with open(os.path.join(pdir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump({"photos": len(credits), "players": len(players), "missing": missing}, fh, ensure_ascii=False, indent=0, sort_keys=True)
    print(f"OK: {len(credits)} player photos ({added} new, {kept} unchanged) for {len(players)} players; "
          f"{len(cand)} candidates, {len(chosen)} with matching file names")


if __name__ == "__main__":
    main()
