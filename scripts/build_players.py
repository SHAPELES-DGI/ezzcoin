#!/usr/bin/env python3
"""Build data/players.json for Ezzcoin from EA's official FC 27 ratings.

EA's ratings page (https://www.ea.com/games/ea-sports-fc/ratings) is a Next.js page.
Page 1 of the list is embedded in its __NEXT_DATA__ JSON; further pages come from the
page's Next.js data route, which needs the buildId from that first response.

Usage: python3 scripts/build_players.py data/players.json
Writes the file only when every check passes; exits 1 with a one-line reason otherwise.
Standard library only.
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timezone

BASE = os.environ.get("EZZ_EA_BASE", "https://www.ea.com")
SLUG = "ea-sports-fc"
PAGE_SIZE = 100
ORDER = "ovr:desc"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
COLS = ["id", "name", "full", "q", "ovr", "pos", "alt", "club", "league", "nation", "gender",
        "sm", "wf", "foot", "height", "age", "s1", "s2", "s3", "s4", "s5", "s6", "psp"]


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "text/html,application/json",
                "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, ""
            last = e
        except Exception as e:  # network hiccup
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url} ({last})")


def first_page(gender):
    url = f"{BASE}/games/{SLUG}/ratings?" + urllib.parse.urlencode({"gender": gender, "orderBy": ORDER})
    status, html = get(url)
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if status != 200 or not m:
        raise RuntimeError(f"ratings page (gender {gender}) had no __NEXT_DATA__ (HTTP {status})")
    data = json.loads(m.group(1))
    rd = (data.get("props") or {}).get("pageProps", {}).get("ratingDetails") or {}
    if not rd.get("items"):
        raise RuntimeError(f"ratings page (gender {gender}) had no players")
    return data.get("buildId"), rd


def page(build_id, gender, n):
    q = urllib.parse.urlencode({"gender": gender, "orderBy": ORDER, "page": n, "franchiseSlug": SLUG})
    status, body = get(f"{BASE}/_next/data/{build_id}/en/games/{SLUG}/ratings.json?{q}")
    if status == 404:
        return None  # build id changed: caller refreshes it
    return ((json.loads(body).get("pageProps") or {}).get("ratingDetails") or {}).get("items") or []


def fetch_gender(gender):
    build_id, rd = first_page(gender)
    total = int(rd.get("totalItems") or len(rd["items"]))
    items = list(rd["items"])
    pages = math.ceil(total / PAGE_SIZE)
    n = 2
    while n <= pages:
        time.sleep(float(os.environ.get("EZZ_PAUSE", "0.3")))
        got = page(build_id, gender, n)
        if got is None:
            build_id, _ = first_page(gender)
            got = page(build_id, gender, n)
            if got is None:
                raise RuntimeError(f"data route kept returning 404 (gender {gender}, page {n})")
        items.extend(got)
        n += 1
    return total, items


def label(v, key="label"):
    if isinstance(v, dict):
        return v.get(key) or v.get("label") or v.get("name") or ""
    return v or ""


def stat(stats, k):
    v = (stats or {}).get(k)
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, (int, float)) else None


def age_from(b):
    if not b:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            d = datetime.strptime(str(b)[:19], fmt).date()
            t = date.today()
            return t.year - d.year - ((t.month, t.day) < (d.month, d.day))
        except ValueError:
            continue
    return None


def height_of(h):
    if isinstance(h, (int, float)):
        return int(h)
    m = re.search(r"\d{3}", str(h or ""))
    return int(m.group(0)) if m else None


def foot_of(f):
    if f in (1, "1") or str(f).lower().startswith("r"):
        return "R"
    if f in (2, "2") or str(f).lower().startswith("l"):
        return "L"
    return ""


def row(p, gender):
    first, last = (p.get("firstName") or "").strip(), (p.get("lastName") or "").strip()
    common = (p.get("commonName") or "").strip()
    fullname = f"{first} {last}".strip()
    name = common or fullname
    pos = label(p.get("position"), "shortLabel")
    alt = ",".join(label(a, "shortLabel") for a in (p.get("alternatePositions") or []) if label(a, "shortLabel"))
    st = p.get("stats") or {}
    if pos == "GK":
        spd = stat(st, "pac")
        if spd is None and stat(st, "acceleration") is not None and stat(st, "sprintSpeed") is not None:
            spd = round((stat(st, "acceleration") + stat(st, "sprintSpeed")) / 2)
        six = [stat(st, "gkDiving"), stat(st, "gkHandling"), stat(st, "gkKicking"), stat(st, "gkReflexes"), spd, stat(st, "gkPositioning")]
    else:
        six = [stat(st, k) for k in ("pac", "sho", "pas", "dri", "def", "phy")]
    league = p.get("leagueName") or label(p.get("league")) or label((p.get("team") or {}).get("league") if isinstance(p.get("team"), dict) else None)
    g = p.get("gender")
    g = (g.get("id") if isinstance(g, dict) else g)
    try:
        g = int(g)
    except (TypeError, ValueError):
        g = gender
    psp = ",".join(label(a) for a in (p.get("playerAbilities") or [])
                   if isinstance(a, dict) and label(a.get("type"), "id") == "playStylePlus")
    return [p.get("id"), name, fullname if fullname != name else "", common or last or name,
            p.get("overallRating"), pos, alt, label(p.get("team")), league or "", label(p.get("nationality")), g,
            p.get("skillMoves"), p.get("weakFootAbility"), foot_of(p.get("preferredFoot")),
            height_of(p.get("height")), age_from(p.get("birthdate")), *six, psp]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data/players.json"
    rows, seen, totals = [], set(), {}
    for gender in (0, 1):
        total, items = fetch_gender(gender)
        totals[gender] = (total, len(items))
        for p in items:
            r = row(p, gender)
            if r[0] is None or r[0] in seen:
                continue
            seen.add(r[0]); rows.append(r)
    rows.sort(key=lambda r: (-(r[4] or 0), r[1]))
    n = len(rows)
    complete = sum(1 for r in rows if r[4] and r[5] and r[7] and all(v is not None for v in r[16:22]))
    doc = {"updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "source": "EA SPORTS FC 27 ratings", "apiUrl": f"{BASE}/games/{SLUG}/ratings (Next.js data route)",
           "count": n, "cols": COLS, "rows": rows}
    blob = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    problems = []
    if n < 15000: problems.append(f"only {n} players")
    if n and complete / n < 0.95: problems.append(f"only {complete / n:.0%} of rows complete")
    if len(blob.encode()) > 8e6: problems.append("file over 8 MB")
    for g, (t, got) in totals.items():
        if got < t * 0.98: problems.append(f"gender {g}: got {got} of {t}")
    if problems:
        print("FAILED: " + "; ".join(problems)); sys.exit(1)
    with open(out, "w", encoding="utf-8") as f:
        f.write(blob)
    top = ", ".join(f"{r[1]} {r[4]}" for r in rows[:5])
    print(f"OK: {n} players ({totals[0][1]} men, {totals[1][1]} women), {complete / n:.1%} complete. Top: {top}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FAILED: " + str(e).splitlines()[0][:300]); sys.exit(1)
