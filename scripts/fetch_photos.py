#!/usr/bin/env python3
"""Fetch freely licensed player photos from Wikimedia Commons for Ezzcoins player pages.

For every player rated MIN_OVR+ in data/players.json it looks for the player's Wikidata item,
takes the item's main image (P18), checks the file's licence on Commons (public domain, CC0,
CC BY or CC BY-SA only), downloads a 360 px thumbnail to photos/<EA id>.<ext> and records the
credit in photos/credits.json. Wrong-person matches are avoided: the Commons file name must
contain one of the player's names, and a name-only match must be unique among footballers.

Usage: python3 scripts/fetch_photos.py [site root]   (standard library only; runs on GitHub)
"""
import html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MIN_OVR = 80
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
    ids = [str(x["id"]) for x in players]
    for i in range(0, len(ids), 150):
        q = ("SELECT ?id ?image WHERE { VALUES ?id { " + " ".join(lit(v) for v in ids[i:i + 150]) + " } "
             "?item wdt:P1469 ?id; wdt:P18 ?image. }")
        for b in sparql(q):
            out.setdefault(int(b["id"]["value"]), set()).add(file_of(b["image"]["value"]))
        time.sleep(1)
    return out


def by_name(players):
    """Footballers whose English label equals the player's name; kept only when exactly one matches."""
    out = {}
    names = {}
    for x in players:
        for n in {x["f"], x["n"]} - {""}:
            names.setdefault(n, set()).add(x["id"])
    keys = [n for n, v in names.items() if len(v) == 1]
    for i in range(0, len(keys), 100):
        q = ("SELECT ?label ?item ?image WHERE { VALUES ?label { " + " ".join(lit(n) + "@en" for n in keys[i:i + 100]) + " } "
             "?item rdfs:label ?label; wdt:P106 wd:Q937857; wdt:P18 ?image. }")
        found = {}
        for b in sparql(q):
            found.setdefault(b["label"]["value"], {}).setdefault(b["item"]["value"], set()).add(file_of(b["image"]["value"]))
        for label, items in found.items():
            if len(items) == 1:
                pid = next(iter(names[label]))
                out.setdefault(pid, set()).update(next(iter(items.values())))
        time.sleep(1)
    return out


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


def main():
    data = json.load(open(os.path.join(ROOT, "data", "players.json"), encoding="utf-8"))
    ci = {c: i for i, c in enumerate(data["cols"])}
    players = [{"id": int(r[ci["id"]]), "n": r[ci["name"]] or "", "f": r[ci["full"]] or ""}
               for r in data["rows"] if (r[ci["ovr"]] or 0) >= MIN_OVR and r[ci["id"]] is not None]
    pdir = os.path.join(ROOT, "photos")
    os.makedirs(pdir, exist_ok=True)
    cpath = os.path.join(pdir, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}

    cand = by_id(players)
    for pid, files in by_name([x for x in players if x["id"] not in cand]).items():
        cand.setdefault(pid, set()).update(files)
    byid = {x["id"]: x for x in players}
    # keep only files whose name contains one of the player's names
    chosen = {}
    for pid, files in cand.items():
        toks = tokens(byid[pid])
        good = sorted(f for f in files if toks & set(norm(f).split()))
        if good:
            chosen[pid] = good[0]
    info = commons_info(set(chosen.values()))
    added = kept = 0
    for pid, f in sorted(chosen.items()):
        meta = info.get(f)
        if not meta or not meta["thumb"] or not OK_LICENCE.match(meta["licence"] or "") or meta["mime"] not in ("image/jpeg", "image/png"):
            continue
        name = f"{pid}.jpg"
        old = credits.get(str(pid))
        if old and old.get("file") == f and os.path.exists(os.path.join(pdir, old.get("img", ""))):
            kept += 1
            continue
        blob = http(meta["thumb"])
        if len(blob) < 2000:
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
    print(f"OK: {len(credits)} player photos ({added} new, {kept} unchanged) for {len(players)} players; "
          f"{len(cand)} candidates, {len(chosen)} with matching file names")


if __name__ == "__main__":
    main()
